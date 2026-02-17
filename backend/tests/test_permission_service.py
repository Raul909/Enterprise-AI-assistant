import pytest
from app.services.permission_service import PermissionService

class TestPermissionService:
    @pytest.fixture
    def service(self):
        return PermissionService()

    def test_can_access_tool_admin_success(self, service):
        """Test admin role can access all allowed tools."""
        assert service.can_access_tool("admin", "search_documents")
        assert service.can_access_tool("admin", "query_database")
        assert service.can_access_tool("admin", "search_github")
        assert service.can_access_tool("admin", "search_jira")
        assert service.can_access_tool("admin", "get_github_file")
        assert service.can_access_tool("admin", "get_jira_ticket")

    def test_can_access_tool_manager_success(self, service):
        """Test manager role can access allowed tools but not others."""
        assert service.can_access_tool("manager", "search_documents")
        assert service.can_access_tool("manager", "query_database")
        assert service.can_access_tool("manager", "search_jira")
        assert service.can_access_tool("manager", "get_jira_ticket")

        # Manager should not access github tools
        assert not service.can_access_tool("manager", "search_github")
        assert not service.can_access_tool("manager", "get_github_file")

    def test_can_access_tool_employee_success(self, service):
        """Test employee role can access only search_documents."""
        assert service.can_access_tool("employee", "search_documents")

        # Employee should not access other tools
        assert not service.can_access_tool("employee", "query_database")
        assert not service.can_access_tool("employee", "search_jira")
        assert not service.can_access_tool("employee", "get_jira_ticket")

    def test_can_access_tool_unknown_role(self, service):
        """Test unknown role cannot access any tool."""
        assert not service.can_access_tool("unknown_role", "search_documents")
        assert not service.can_access_tool("unknown_role", "unknown_tool")

    def test_can_access_tool_unknown_tool(self, service):
        """Test accessing unknown tool returns False."""
        assert not service.can_access_tool("admin", "unknown_tool")
        assert not service.can_access_tool("manager", "unknown_tool")
        assert not service.can_access_tool("employee", "unknown_tool")

    def test_can_access_tool_case_sensitivity(self, service):
        """Test that role lookup is case-sensitive (based on implementation)."""
        # The current implementation uses dictionary lookup, so it is case-sensitive.
        # "Admin" is not "admin".
        assert not service.can_access_tool("Admin", "search_documents")
