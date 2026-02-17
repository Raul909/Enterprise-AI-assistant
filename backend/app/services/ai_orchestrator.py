"""
AI Orchestrator service.
Coordinates between RAG, MCP tools, and LLM to answer user queries.
"""

import time
import uuid
import asyncio
from typing import Dict, Any, List
from contextvars import ContextVar
from dataclasses import dataclass, field

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from core.config import settings
from core.logging import get_logger, audit_logger
from services.mcp_client import MCPClient
from services.rag_service import rag_service
from services.permission_service import permission_service
from schemas.chat import (
    ChatRequest, ChatResponse, ToolExecution, SourceReference
)

logger = get_logger(__name__)

# Context-local storage for LLM clients
_openai_client_var: ContextVar[AsyncOpenAI | None] = ContextVar("openai_client", default=None)
_anthropic_client_var: ContextVar[AsyncAnthropic | None] = ContextVar("anthropic_client", default=None)


@dataclass
class ConversationContext:
    """Holds context for a conversation."""
    conversation_id: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    tools_used: List[ToolExecution] = field(default_factory=list)
    sources: List[SourceReference] = field(default_factory=list)


# Simple in-memory conversation store (use Redis in production)
_conversations: Dict[str, ConversationContext] = {}


class AIOrchestrator:
    """
    Orchestrates AI responses using RAG, MCP tools, and LLM.
    """
    
    def __init__(self):
        self.mcp_client = MCPClient()
        # Clients are managed via ContextVars to ensure loop safety
    
    @property
    def openai_client(self) -> AsyncOpenAI:
        """Lazy-load OpenAI client in current context."""
        client = _openai_client_var.get()
        if client is None:
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            _openai_client_var.set(client)
        return client
    
    @property
    def anthropic_client(self) -> AsyncAnthropic:
        """Lazy-load Anthropic client in current context."""
        client = _anthropic_client_var.get()
        if client is None:
            client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            _anthropic_client_var.set(client)
        return client
    
    def get_or_create_conversation(self, conversation_id: str | None) -> ConversationContext:
        """Get existing conversation or create a new one."""
        if conversation_id and conversation_id in _conversations:
            return _conversations[conversation_id]
        
        new_id = conversation_id or str(uuid.uuid4())
        context = ConversationContext(conversation_id=new_id)
        _conversations[new_id] = context
        return context
    
    async def handle_query(
        self,
        user: Dict[str, Any],
        request: ChatRequest
    ) -> ChatResponse:
        """
        Handle a user query with full orchestration.
        
        Args:
            user: User info dict with id, email, role
            request: Chat request with query and options
        
        Returns:
            ChatResponse with answer and metadata
        """
        start_time = time.time()
        
        # Get or create conversation context
        context = self.get_or_create_conversation(request.conversation_id)
        
        user_id = user.get("id", 0)
        user_role = user.get("role", "employee")
        user_dept = user.get("department", "general")
        
        logger.info(
            "Processing query",
            user_id=user_id,
            query_length=len(request.query),
            conversation_id=context.conversation_id
        )
        
        # Step 1: Discover available tools
        tools = await self.mcp_client.discover_tools(role=user_role)
        
        # Step 2: Get RAG context
        rag_context = rag_service.build_context(
            query=request.query,
            department=user_dept
        )
        
        # Step 3: Determine which tools to use and execute them
        tool_results = []
        tools_used = []
        
        # Helper function for concurrent execution
        async def execute_tool_safe(tool):
            try:
                # Prepare parameters based on tool
                params = self._prepare_tool_params(tool.name, request.query, user)
                
                # Execute tool
                result = await self.mcp_client.call_tool(
                    tool_name=tool.name,
                    parameters=params,
                    role=user_role,
                    user_id=user_id
                )
                
                tool_exec = ToolExecution(
                    tool_name=tool.name,
                    success=result.get("success", False),
                    result=result.get("result") if result.get("success") else None,
                    error=result.get("error"),
                    execution_time_ms=result.get("execution_time_ms", 0)
                )
                return tool_exec
            except Exception as e:
                logger.error("Tool execution wrapper failed", tool=tool.name, error=str(e))
                return ToolExecution(
                    tool_name=tool.name,
                    success=False,
                    error=str(e),
                    execution_time_ms=0
                )

        tasks = []
        for tool in tools:
            if tool.should_use(request.query):
                # Check permission
                if not permission_service.can_access_tool(user_role, tool.name):
                    continue
                
                tasks.append(execute_tool_safe(tool))

        # Execute tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks)
            tools_used.extend(results)

            for tool_exec in results:
                if tool_exec.success:
                    tool_results.append({
                        "tool": tool_exec.tool_name,
                        "data": tool_exec.result
                    })
        
        # Step 4: Build prompt and call LLM
        prompt = self._build_prompt(
            query=request.query,
            rag_context=rag_context,
            tool_results=tool_results,
            conversation_history=context.messages[-10:]  # Last 10 messages
        )
        
        # Call LLM
        answer = await self._call_llm(prompt, request.max_tokens)
        
        # Step 5: Update conversation
        context.messages.append({"role": "user", "content": request.query})
        context.messages.append({"role": "assistant", "content": answer})
        context.tools_used.extend(tools_used)
        
        # Build sources from RAG results
        sources = []
        if request.include_sources:
            rag_results = rag_service.semantic_search(request.query, department=user_dept)
            for doc in rag_results[:3]:
                sources.append(SourceReference(
                    title=doc.get("title", "Document"),
                    content_snippet=doc.get("content", "")[:200],
                    source_type="document",
                    relevance_score=doc.get("score", 0)
                ))
        
        processing_time = (time.time() - start_time) * 1000
        
        # Log the query
        audit_logger.log_tool_execution(
            user_id=user_id,
            tool_name="ai_orchestrator",
            query=request.query,
            execution_time_ms=processing_time,
            success=True
        )
        
        return ChatResponse(
            answer=answer,
            conversation_id=context.conversation_id,
            sources=sources,
            tools_used=tools_used,
            processing_time_ms=processing_time,
            model_used=settings.openai_model if settings.ai_provider == "openai" else settings.anthropic_model
        )
    
    def _prepare_tool_params(
        self,
        tool_name: str,
        query: str,
        user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare parameters for a tool based on the query."""
        
        if tool_name == "search_documents":
            return {
                "query": query,
                "department": user.get("department", "general")
            }
        
        elif tool_name == "query_database":
            # Extract SQL-like intent from query
            # In production, use LLM to generate SQL
            return {"query": "SELECT * FROM employees LIMIT 5"}
        
        elif tool_name == "search_github":
            return {
                "query": query,
                "search_type": "issues",
                "state": "open"
            }
        
        elif tool_name == "search_jira":
            return {
                "query": query,
                "status": None
            }
        
        return {"query": query}
    
    def _build_prompt(
        self,
        query: str,
        rag_context: str,
        tool_results: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Build the prompt for the LLM."""
        
        history_text = ""
        if conversation_history:
            history_text = "\n## Conversation History\n"
            for msg in conversation_history[-4:]:  # Last 4 messages
                role = msg["role"].capitalize()
                history_text += f"{role}: {msg['content'][:500]}\n"
        
        tool_text = ""
        if tool_results:
            tool_text = "\n## Tool Results\n"
            for result in tool_results:
                tool_text += f"**{result['tool']}**:\n{str(result['data'])[:1000]}\n\n"
        
        prompt = f"""You are an Enterprise AI Assistant helping employees find information and answer questions about company resources.

## Context from Documents
{rag_context}
{tool_text}
{history_text}

## User Question
{query}

## Instructions
- Answer the question based on the provided context and tool results
- If you don't have enough information, say so clearly
- Be concise but comprehensive
- Use professional, helpful language
- If referencing specific documents or data, mention the source

Answer:"""
        
        return prompt
    
    async def _call_llm(self, prompt: str, max_tokens: int | None = None) -> str:
        """Call the configured LLM."""
        
        max_tokens = max_tokens or settings.openai_max_tokens
        
        try:
            if settings.ai_provider == "anthropic":
                response = await self.anthropic_client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            else:  # OpenAI
                response = await self.openai_client.chat.completions.create(
                    model=settings.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=settings.openai_temperature
                )
                return response.choices[0].message.content or ""
        
        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            return f"I apologize, but I encountered an error processing your request. Please try again later. Error: {str(e)}"


# Global orchestrator instance
ai_orchestrator = AIOrchestrator()


def handle_query(user: Dict[str, Any], query: str) -> str:
    """
    Legacy function for backward compatibility.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
         raise RuntimeError("Cannot call synchronous handle_query from an async context. Use await ai_orchestrator.handle_query() instead.")

    request = ChatRequest(query=query)
    # Use asyncio.run to execute the async method from sync context
    return asyncio.run(ai_orchestrator.handle_query(user, request)).answer
