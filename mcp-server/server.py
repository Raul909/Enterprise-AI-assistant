"""
MCP Server for Enterprise AI Assistant.
Registers and exposes tools for the AI orchestrator to use.
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import time

from permissions import can_access, ROLE_TOOL_MAP
from tools.document_tool import search_documents
from tools.database_tool import query_database, get_schema
from tools.github_tool import search_github, get_github_file, get_repo_info, list_repo_contents
from tools.jira_tool import search_jira, get_jira_ticket, get_project_info, list_sprints


app = FastAPI(
    title="MCP Server",
    description="Model Context Protocol Server for Enterprise AI Assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Tool Registry
TOOLS = {
    "search_documents": {
        "name": "search_documents",
        "description": "Search internal company documents using semantic search",
        "parameters": {
            "query": {"type": "string", "description": "Search query", "required": True},
            "department": {"type": "string", "description": "Filter by department", "required": False}
        },
        "handler": search_documents
    },
    "query_database": {
        "name": "query_database",
        "description": "Run read-only SQL queries on the enterprise database. Only SELECT statements allowed.",
        "parameters": {
            "query": {"type": "string", "description": "SQL SELECT query", "required": True},
            "params": {"type": "object", "description": "Query parameters (dictionary)", "required": False}
        },
        "handler": query_database
    },
    "get_database_schema": {
        "name": "get_database_schema",
        "description": "Get the database schema (available tables and columns)",
        "parameters": {},
        "handler": get_schema
    },
    "search_github": {
        "name": "search_github",
        "description": "Search GitHub for issues, pull requests, or repositories",
        "parameters": {
            "query": {"type": "string", "description": "Search query", "required": True},
            "search_type": {"type": "string", "description": "Type: issues, prs, repos", "required": False},
            "state": {"type": "string", "description": "Filter by state: open, closed, all", "required": False}
        },
        "handler": search_github
    },
    "get_github_file": {
        "name": "get_github_file",
        "description": "Get contents of a file from a GitHub repository",
        "parameters": {
            "repo": {"type": "string", "description": "Repository name", "required": True},
            "path": {"type": "string", "description": "File path", "required": True},
            "ref": {"type": "string", "description": "Branch or commit", "required": False}
        },
        "handler": get_github_file
    },
    "search_jira": {
        "name": "search_jira",
        "description": "Search Jira tickets with filters",
        "parameters": {
            "query": {"type": "string", "description": "Search query", "required": True},
            "project": {"type": "string", "description": "Project key (e.g., EA)", "required": False},
            "status": {"type": "string", "description": "Ticket status", "required": False},
            "priority": {"type": "string", "description": "Priority level", "required": False}
        },
        "handler": search_jira
    },
    "get_jira_ticket": {
        "name": "get_jira_ticket",
        "description": "Get detailed information about a Jira ticket",
        "parameters": {
            "ticket_key": {"type": "string", "description": "Ticket key (e.g., EA-101)", "required": True}
        },
        "handler": get_jira_ticket
    },
    "list_jira_sprints": {
        "name": "list_jira_sprints",
        "description": "List sprints for a project",
        "parameters": {
            "project_key": {"type": "string", "description": "Project key", "required": False},
            "state": {"type": "string", "description": "Sprint state: active, closed, future", "required": False}
        },
        "handler": list_sprints
    }
}


# Request/Response models
class ToolRequest(BaseModel):
    """Request to execute a tool."""
    role: str = "employee"
    parameters: Dict[str, Any] = {}


class ToolResponse(BaseModel):
    """Response from tool execution."""
    success: bool
    tool_name: str
    result: Any = None
    error: str | None = None
    execution_time_ms: float


# ============== Endpoints ==============

@app.get("/")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "mcp-server"}


@app.get("/tools")
def list_tools(role: str = "employee") -> Dict[str, Any]:
    """
    List all available tools and their descriptions.
    Filters based on role permissions.
    """
    allowed_tools = ROLE_TOOL_MAP.get(role, [])
    
    tools = []
    for name, tool in TOOLS.items():
        # Check if role has access
        if name in allowed_tools or role == "admin":
            tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            })
    
    return {
        "role": role,
        "available_tools": len(tools),
        "tools": tools
    }


@app.get("/tools/{tool_name}")
def get_tool_info(tool_name: str) -> Dict[str, Any]:
    """Get information about a specific tool."""
    if tool_name not in TOOLS:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    
    tool = TOOLS[tool_name]
    return {
        "name": tool["name"],
        "description": tool["description"],
        "parameters": tool["parameters"]
    }


@app.post("/tools/{tool_name}", response_model=ToolResponse)
def execute_tool(tool_name: str, request: ToolRequest) -> ToolResponse:
    """
    Execute a tool with the given parameters.
    Checks role permissions before execution.
    """
    start_time = time.time()
    
    # Check if tool exists
    if tool_name not in TOOLS:
        return ToolResponse(
            success=False,
            tool_name=tool_name,
            error=f"Tool not found: {tool_name}",
            execution_time_ms=0
        )
    
    # Check permissions
    if not can_access(request.role, tool_name):
        return ToolResponse(
            success=False,
            tool_name=tool_name,
            error=f"Permission denied: Role '{request.role}' cannot access tool '{tool_name}'",
            execution_time_ms=0
        )
    
    try:
        # Execute the tool
        tool = TOOLS[tool_name]
        handler = tool["handler"]
        result = handler(**request.parameters)
        
        execution_time = (time.time() - start_time) * 1000
        
        return ToolResponse(
            success=True,
            tool_name=tool_name,
            result=result,
            execution_time_ms=execution_time
        )
    
    except TypeError as e:
        execution_time = (time.time() - start_time) * 1000
        return ToolResponse(
            success=False,
            tool_name=tool_name,
            error=f"Invalid parameters: {str(e)}",
            execution_time_ms=execution_time
        )
    
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return ToolResponse(
            success=False,
            tool_name=tool_name,
            error=f"Tool execution failed: {str(e)}",
            execution_time_ms=execution_time
        )


# Legacy endpoint for backward compatibility
@app.post("/tools/{tool_name}/execute")
def execute_tool_legacy(tool_name: str, request: ToolRequest) -> ToolResponse:
    """Legacy endpoint - redirects to main execute endpoint."""
    return execute_tool(tool_name, request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3333)
