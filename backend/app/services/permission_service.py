"""
Permission service for role-based access control.
"""

from typing import List, Dict, Set

from core.logging import audit_logger


# Tool permissions by role
ROLE_TOOL_PERMISSIONS: Dict[str, Set[str]] = {
    "admin": {
        "search_documents",
        "query_database",
        "search_github",
        "search_jira",
        "get_github_file",
        "get_jira_ticket",
    },
    "manager": {
        "search_documents",
        "query_database",
        "search_jira",
        "get_jira_ticket",
    },
    "employee": {
        "search_documents",
    },
}

# Department-based document access
DEPARTMENT_DOCUMENT_ACCESS: Dict[str, Set[str]] = {
    "engineering": {"engineering", "general", "public"},
    "hr": {"hr", "general", "public"},
    "finance": {"finance", "general", "public"},
    "sales": {"sales", "general", "public"},
    "admin": {"*"},  # Access to all departments
}


class PermissionService:
    """Service for checking user permissions."""
    
    def __init__(self):
        self.role_permissions = ROLE_TOOL_PERMISSIONS
        self.department_access = DEPARTMENT_DOCUMENT_ACCESS
    
    def can_access_tool(self, role: str, tool_name: str) -> bool:
        """
        Check if a role can access a specific tool.
        
        Args:
            role: User role (admin, manager, employee)
            tool_name: Name of the tool to check
        
        Returns:
            True if access is allowed, False otherwise
        """
        allowed_tools = self.role_permissions.get(role, set())
        return tool_name in allowed_tools
    
    def get_allowed_tools(self, role: str) -> List[str]:
        """
        Get list of tools allowed for a role.
        
        Args:
            role: User role
        
        Returns:
            List of tool names
        """
        return list(self.role_permissions.get(role, set()))
    
    def can_access_department_docs(
        self,
        user_department: str,
        user_role: str,
        document_department: str
    ) -> bool:
        """
        Check if a user can access documents from a specific department.
        
        Args:
            user_department: User's department
            user_role: User's role
            document_department: Department the document belongs to
        
        Returns:
            True if access is allowed
        """
        # Admins can access everything
        if user_role == "admin":
            return True
        
        # Get allowed departments for user's department
        allowed_depts = self.department_access.get(
            user_department.lower(),
            {"public"}
        )
        
        # Check if document department is in allowed list
        if "*" in allowed_depts:
            return True
        
        return document_department.lower() in allowed_depts
    
    def filter_tools_by_role(
        self,
        tools: List[Dict],
        role: str
    ) -> List[Dict]:
        """
        Filter a list of tools to only those allowed for the role.
        
        Args:
            tools: List of tool definitions
            role: User role
        
        Returns:
            Filtered list of tools
        """
        allowed_tools = self.role_permissions.get(role, set())
        return [t for t in tools if t.get("name") in allowed_tools]
    
    def check_and_log_permission(
        self,
        user_id: int,
        role: str,
        tool_name: str
    ) -> bool:
        """
        Check permission and log if denied.
        
        Args:
            user_id: User ID
            role: User role
            tool_name: Tool being accessed
        
        Returns:
            True if access is allowed
        """
        allowed = self.can_access_tool(role, tool_name)
        
        if not allowed:
            audit_logger.log_permission_denied(
                user_id=user_id,
                resource=f"tool:{tool_name}",
                action="execute",
                reason=f"Role '{role}' not authorized for tool '{tool_name}'"
            )
        
        return allowed


# Global permission service instance
permission_service = PermissionService()
