import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add the backend directory to sys.path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestPermissionService:
    @pytest.fixture
    def permission_service(self):
        # Patch sys.modules to mock dependencies
        with patch.dict(sys.modules, {'core': MagicMock(), 'core.logging': MagicMock()}):
            from app.services.permission_service import PermissionService
            service = PermissionService()
            # Set up specific permissions for testing logic, not configuration
            service.role_permissions = {
                "admin": {"search_documents", "query_database"},
                "manager": {"search_documents"},
                "employee": set()
            }
            yield service

    @pytest.mark.parametrize("role, tool", [
        ("admin", "search_documents"),
        ("admin", "query_database"),
        ("manager", "search_documents"),
    ])
    def test_can_access_tool_allowed(self, permission_service, role, tool):
        """Test that roles can access their allowed tools based on injected permissions."""
        assert permission_service.can_access_tool(role, tool) is True

    @pytest.mark.parametrize("role, tool", [
        ("manager", "query_database"),
        ("employee", "search_documents"),
        ("unknown_role", "search_documents"),
    ])
    def test_can_access_tool_denied(self, permission_service, role, tool):
        """Test that roles cannot access tools they don't have permission for based on injected permissions."""
        assert permission_service.can_access_tool(role, tool) is False

    def test_can_access_tool_unknown_tool(self, permission_service):
        """Test that unknown tools cannot be accessed by any role."""
        assert permission_service.can_access_tool("admin", "unknown_tool") is False

    def test_default_configuration_loaded(self):
        """Verify that the service loads the default configuration correctly (integration test)."""
        # This test verifies that the real configuration is loaded, so we mock only dependencies but not the service logic
        with patch.dict(sys.modules, {'core': MagicMock(), 'core.logging': MagicMock()}):
             from app.services.permission_service import PermissionService, ROLE_TOOL_PERMISSIONS
             service = PermissionService()
             # Check that service uses the global ROLE_TOOL_PERMISSIONS
             assert service.role_permissions == ROLE_TOOL_PERMISSIONS
             # Check a known default permission to ensure configuration hasn't been accidentally cleared
             assert "search_documents" in service.role_permissions.get("admin", set())
