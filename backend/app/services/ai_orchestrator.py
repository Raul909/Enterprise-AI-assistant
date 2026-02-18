"""
AI Orchestrator service.
Coordinates between RAG, MCP tools, and LLM to answer user queries.
"""

import time
import uuid
from typing import Dict, Any, List, Optional, AsyncGenerator

from openai import OpenAI
import anthropic

from core.config import settings
from core.logging import get_logger, audit_logger
from services.mcp_client import MCPClient, Tool
from services.rag_service import rag_service
from services.permission_service import permission_service
from services.conversation_storage import conversation_storage
from schemas.chat import (
    ChatRequest, ChatResponse, ToolExecution, SourceReference, ConversationContext
)

logger = get_logger(__name__)




class AIOrchestrator:
    """
    Orchestrates AI responses using RAG, MCP tools, and LLM.
    """
    
    def __init__(self):
        self.mcp_client = MCPClient()
        self._openai_client: OpenAI | None = None
        self._anthropic_client: anthropic.Anthropic | None = None
    
    @property
    def openai_client(self) -> OpenAI:
        """Lazy-load OpenAI client."""
        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=settings.openai_api_key)
        return self._openai_client
    
    @property
    def anthropic_client(self) -> anthropic.Anthropic:
        """Lazy-load Anthropic client."""
        if self._anthropic_client is None:
            self._anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._anthropic_client
    
    def get_or_create_conversation(self, conversation_id: str | None) -> ConversationContext:
        """Get existing conversation or create a new one."""
        if conversation_id:
            context = conversation_storage.get(conversation_id)
            if context:
                return context
        
        new_id = conversation_id or str(uuid.uuid4())
        context = ConversationContext(conversation_id=new_id)
        conversation_storage.set(new_id, context)
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
        tools = self.mcp_client.discover_tools(role=user_role)
        
        # Step 2: Get RAG context
        rag_context = await rag_service.build_context(
            query=request.query,
            department=user_dept
        )
        
        # Step 3: Determine which tools to use and execute them
        tool_results = []
        tools_used = []
        
        for tool in tools:
            if tool.should_use(request.query):
                # Check permission
                if not permission_service.can_access_tool(user_role, tool.name):
                    continue
                
                # Prepare parameters based on tool
                params = self._prepare_tool_params(tool.name, request.query, user)
                
                # Execute tool
                result = self.mcp_client.call_tool(
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
                tools_used.append(tool_exec)
                
                if result.get("success"):
                    tool_results.append({
                        "tool": tool.name,
                        "data": result.get("result")
                    })
        
        # Step 4: Build prompt and call LLM
        messages = self._build_prompt(
            query=request.query,
            rag_context=rag_context,
            tool_results=tool_results,
            conversation_history=context.messages[-10:]  # Last 10 messages
        )
        
        # Call LLM
        answer = self._call_llm(messages, request.max_tokens)
        
        # Step 5: Update conversation
        context.messages.append({"role": "user", "content": request.query})
        context.messages.append({"role": "assistant", "content": answer})
        context.tools_used.extend(tools_used)
        
        # Persist updated conversation
        conversation_storage.set(context.conversation_id, context)

        # Build sources from RAG results
        sources = []
        if request.include_sources:
            rag_results = await rag_service.semantic_search(request.query, department=user_dept)
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
    ) -> List[Dict[str, str]]:
        """Build the structured prompt for the LLM."""
        
        system_prompt = """You are an Enterprise AI Assistant helping employees find information and answer questions about company resources.

Instructions:
- Answer the question based on the provided context and tool results
- If you don't have enough information, say so clearly
- Be concise but comprehensive
- Use professional, helpful language
- If referencing specific documents or data, mention the source"""

        # Build context content
        context_content = ""
        
        if rag_context:
            context_content += f"<context_from_documents>\n{rag_context}\n</context_from_documents>\n\n"

        if tool_results:
            tool_text = ""
            for result in tool_results:
                tool_text += f"**{result['tool']}**:\n{str(result['data'])[:1000]}\n\n"
            context_content += f"<tool_results>\n{tool_text}\n</tool_results>\n\n"

        if conversation_history:
            history_text = ""
            for msg in conversation_history[-4:]:  # Last 4 messages
                role = msg["role"].capitalize()
                history_text += f"{role}: {msg['content'][:500]}\n"
            context_content += f"<conversation_history>\n{history_text}\n</conversation_history>\n\n"

        user_content = f"""{context_content}
<user_question>
{query}
</user_question>"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    
    def _call_llm(self, messages: List[Dict[str, str]], max_tokens: int | None = None) -> str:
        """Call the configured LLM."""
        
        max_tokens = max_tokens or settings.openai_max_tokens
        
        try:
            if settings.ai_provider == "anthropic":
                # Extract system message for Anthropic
                system_message = ""
                chat_messages = []

                for msg in messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        chat_messages.append(msg)

                response = self.anthropic_client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=max_tokens,
                    system=system_message,
                    messages=chat_messages
                )
                return response.content[0].text
            
            else:  # OpenAI
                response = self.openai_client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=settings.openai_temperature
                )
                return response.choices[0].message.content or ""
        
        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            return f"I apologize, but I encountered an error processing your request. Please try again later. Error: {str(e)}"


# Global orchestrator instance
ai_orchestrator = AIOrchestrator()


async def handle_query(user: Dict[str, Any], query: str) -> str:
    """
    Legacy function for backward compatibility.
    """
    request = ChatRequest(query=query)
    response = await ai_orchestrator.handle_query(user, request)
    return response.answer
