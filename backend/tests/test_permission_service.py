import pytest
import sys
import os

# Add the backend/app directory to sys.path so we can import modules as if we were in app/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from services.permission_service import PermissionService

class TestPermissionService:
    def setup_method(self):
        self.permission_service = PermissionService()

    @pytest.mark.parametrize("role, tool", [
        ("admin", "search_documents"),
        ("admin", "query_database"),
        ("admin", "search_github"),
        ("admin", "search_jira"),
        ("admin", "get_github_file"),
        ("admin", "get_jira_ticket"),
        ("manager", "search_documents"),
        ("manager", "query_database"),
        ("manager", "search_jira"),
        ("manager", "get_jira_ticket"),
        ("employee", "search_documents"),
    ])
    def test_can_access_tool_allowed(self, role, tool):
        """Test that roles can access their allowed tools."""
        assert self.permission_service.can_access_tool(role, tool) is True

    @pytest.mark.parametrize("role, tool", [
        ("manager", "search_github"),
        ("manager", "get_github_file"),
        ("employee", "query_database"),
        ("employee", "search_github"),
        ("employee", "search_jira"),
        ("employee", "get_github_file"),
        ("employee", "get_jira_ticket"),
    ])
    def test_can_access_tool_denied(self, role, tool):
        """Test that roles cannot access tools they don't have permission for."""
        assert self.permission_service.can_access_tool(role, tool) is False

    def test_can_access_tool_unknown_role(self):
        """Test that unknown roles have no access."""
        assert self.permission_service.can_access_tool("unknown_role", "search_documents") is False

    def test_can_access_tool_unknown_tool(self):
        """Test that unknown tools cannot be accessed by any role."""
        assert self.permission_service.can_access_tool("admin", "unknown_tool") is False
        assert self.permission_service.can_access_tool("manager", "unknown_tool") is False
        assert self.permission_service.can_access_tool("employee", "unknown_tool") is False
