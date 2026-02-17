"""
MCP Client for communicating with the MCP Server.
Handles tool discovery and execution with proper error handling.
"""

import time
from typing import Dict, Any, List
from contextvars import ContextVar

import httpx

from core.config import settings
from core.logging import get_logger, audit_logger

logger = get_logger(__name__)

# Context-local storage for HTTP client
_client_var: ContextVar[httpx.AsyncClient | None] = ContextVar("mcp_client", default=None)


class Tool:
    """Represents an MCP tool."""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    def should_use(self, query: str) -> bool:
        """
        Determine if this tool should be used for the given query.
        Uses simple keyword matching for now.
        """
        query_lower = query.lower()
        
        # Tool-specific keywords
        keywords = {
            "search_documents": ["document", "policy", "guide", "manual", "find", "search", "company"],
            "query_database": ["database", "sql", "query", "employee", "salary", "project", "department"],
            "get_database_schema": ["schema", "tables", "columns", "database structure"],
            "search_github": ["github", "issue", "pull request", "pr", "repository", "repo", "code"],
            "get_github_file": ["file content", "source code", "readme"],
            "search_jira": ["jira", "ticket", "task", "story", "bug", "sprint"],
            "get_jira_ticket": ["jira ticket", "ticket details"],
            "list_jira_sprints": ["sprint", "sprints", "iteration"],
        }
        
        tool_keywords = keywords.get(self.name, [])
        return any(kw in query_lower for kw in tool_keywords)


class MCPClient:
    """Client for interacting with the MCP Server."""
    
    def __init__(self, base_url: str | None = None, timeout: int | None = None):
        self.base_url = base_url or settings.mcp_server_url
        self.timeout = timeout or settings.mcp_timeout_seconds
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-initialize HTTP client in the current context."""
        client = _client_var.get()
        if client is None or client.is_closed:
            client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
            _client_var.set(client)
        return client
    
    async def discover_tools(self, role: str = "employee") -> List[Tool]:
        """
        Discover available tools from the MCP server.
        
        Args:
            role: User role for permission filtering
        
        Returns:
            List of Tool objects
        """
        try:
            response = await self.client.get("/tools", params={"role": role})
            response.raise_for_status()
            
            data = response.json()
            tools = []
            
            for tool_data in data.get("tools", []):
                tools.append(Tool(
                    name=tool_data["name"],
                    description=tool_data["description"],
                    parameters=tool_data.get("parameters", {})
                ))
            
            logger.info(
                "Discovered tools from MCP server",
                role=role,
                tool_count=len(tools)
            )
            return tools
        
        except httpx.HTTPError as e:
            logger.error("Failed to discover tools", error=str(e))
            # Return default tools on error
            return [
                Tool("search_documents", "Search internal documents", {})
            ]
    
    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        role: str = "employee",
        user_id: int | None = None
    ) -> Dict[str, Any]:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Parameters for the tool
            role: User role for permission checking
            user_id: Optional user ID for audit logging
        
        Returns:
            Tool execution result
        """
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"/tools/{tool_name}",
                json={
                    "role": role,
                    "parameters": parameters
                }
            )
            response.raise_for_status()
            
            result = response.json()
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Log successful execution
            if user_id:
                audit_logger.log_tool_execution(
                    user_id=user_id,
                    tool_name=tool_name,
                    query=str(parameters),
                    result=result.get("result"),
                    execution_time_ms=execution_time_ms,
                    success=result.get("success", True)
                )
            
            logger.info(
                "Tool executed successfully",
                tool=tool_name,
                execution_time_ms=execution_time_ms
            )
            
            return result
        
        except httpx.HTTPError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_msg = f"Tool call failed: {str(e)}"
            
            # Log failed execution
            if user_id:
                audit_logger.log_tool_execution(
                    user_id=user_id,
                    tool_name=tool_name,
                    query=str(parameters),
                    execution_time_ms=execution_time_ms,
                    success=False,
                    error=error_msg
                )
            
            logger.error("Tool call failed", tool=tool_name, error=str(e))
            
            return {
                "success": False,
                "tool_name": tool_name,
                "error": error_msg,
                "execution_time_ms": execution_time_ms
            }
    
    async def get_tool_info(self, tool_name: str) -> Dict[str, Any] | None:
        """Get information about a specific tool."""
        try:
            response = await self.client.get(f"/tools/{tool_name}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None
    
    async def health_check(self) -> bool:
        """Check if the MCP server is healthy."""
        try:
            response = await self.client.get("/")
            return response.status_code == 200
        except httpx.HTTPError:
            return False
    
    async def close(self) -> None:
        """Close the HTTP client in the current context."""
        client = _client_var.get()
        if client:
            await client.aclose()
            _client_var.set(None)


# Global MCP client instance
mcp_client = MCPClient()
