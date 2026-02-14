"""
Role-based tool permissions for MCP server.
"""

from typing import Dict, Set, List

# Tool permissions by role
ROLE_TOOL_MAP: Dict[str, List[str]] = {
    "admin": [
        "search_documents",
        "query_database",
        "get_database_schema",
        "search_github",
        "get_github_file",
        "search_jira",
        "get_jira_ticket",
        "list_jira_sprints",
    ],
    "manager": [
        "search_documents",
        "query_database",
        "get_database_schema",
        "search_jira",
        "get_jira_ticket",
        "list_jira_sprints",
    ],
    "employee": [
        "search_documents",
    ],
}


def can_access(role: str, tool_name: str) -> bool:
    """
    Check if a role can access a specific tool.
    
    Args:
        role: User role
        tool_name: Name of the tool
    
    Returns:
        True if access is allowed
    """
    allowed_tools = ROLE_TOOL_MAP.get(role, [])
    return tool_name in allowed_tools


def get_allowed_tools(role: str) -> List[str]:
    """
    Get list of tools allowed for a role.
    
    Args:
        role: User role
    
    Returns:
        List of tool names
    """
    return ROLE_TOOL_MAP.get(role, [])
