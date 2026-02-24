import sys
from unittest.mock import MagicMock, patch
import pytest

# Define mocks globally so they can be accessed by tests
mock_httpx = MagicMock()
mock_httpx.HTTPError = type("HTTPError", (Exception,), {})
mock_httpx.Client = MagicMock()

mock_audit_logger = MagicMock()
mock_logger = MagicMock()

@pytest.fixture(scope="module", autouse=True)
def mock_missing_deps():
    """
    Fixture to mock missing dependencies for the duration of this module.
    This avoids polluting sys.modules globally for other test modules.
    """
    mocks = {
        "httpx": mock_httpx,
        "structlog": MagicMock(),
        "core.config": MagicMock(),
        "core.logging": MagicMock(),
    }

    # Configure core.config
    mock_settings = MagicMock()
    mock_settings.mcp_server_url = "http://mcp-server"
    mock_settings.mcp_timeout_seconds = 5
    mocks["core.config"].settings = mock_settings

    # Configure core.logging
    mocks["core.logging"].get_logger.return_value = mock_logger
    mocks["core.logging"].audit_logger = mock_audit_logger

    with patch.dict(sys.modules, mocks):
        # We need to ensure the service is imported while the mocks are in sys.modules
        if "services.mcp_client" in sys.modules:
            import importlib
            importlib.reload(sys.modules["services.mcp_client"])
        yield

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset mocks before each test to ensure test isolation."""
    mock_httpx.Client.reset_mock()
    mock_httpx.Client.return_value.get.reset_mock()
    mock_httpx.Client.return_value.post.reset_mock()
    mock_httpx.Client.return_value.get.side_effect = None
    mock_httpx.Client.return_value.post.side_effect = None
    mock_audit_logger.log_tool_execution.reset_mock()
    mock_logger.reset_mock()

class TestMCPClient:
    @pytest.fixture
    def MCPClient(self):
        # Import inside the fixture to ensure mocks are active
        from services.mcp_client import MCPClient
        return MCPClient

    @pytest.fixture
    def Tool(self):
        from services.mcp_client import Tool
        return Tool

    @pytest.fixture
    def mcp_client(self, MCPClient):
        return MCPClient(base_url="http://mcp-server", timeout=5)

    @pytest.fixture
    def mock_client_instance(self):
        return mock_httpx.Client.return_value

    def test_init(self, MCPClient):
        client = MCPClient(base_url="http://test-url", timeout=10)
        assert client.base_url == "http://test-url"
        assert client.timeout == 10
        assert client._client is None

    def test_call_tool_success(self, mcp_client, mock_client_instance):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "result": "Tool result"}
        mock_client_instance.post.return_value = mock_response

        tool_name = "test_tool"
        parameters = {"param1": "val1"}
        user_id = 123
        role = "admin"

        result = mcp_client.call_tool(
            tool_name=tool_name,
            parameters=parameters,
            role=role,
            user_id=user_id
        )

        assert result == {"success": True, "result": "Tool result"}
        mock_audit_logger.log_tool_execution.assert_called_once()

    def test_call_tool_failure(self, mcp_client, mock_client_instance):
        mock_client_instance.post.side_effect = mock_httpx.HTTPError("Connection failed")

        result = mcp_client.call_tool("test_tool", {}, user_id=123)

        assert result["success"] is False
        mock_audit_logger.log_tool_execution.assert_called_once()

    def test_call_tool_no_user_id(self, mcp_client, mock_client_instance):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_client_instance.post.return_value = mock_response

        mcp_client.call_tool("test_tool", {}, user_id=None)

        mock_audit_logger.log_tool_execution.assert_not_called()

    def test_discover_tools_success(self, mcp_client, mock_client_instance, Tool):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tools": [{"name": "tool1", "description": "desc1"}]
        }
        mock_client_instance.get.return_value = mock_response

        tools = mcp_client.discover_tools(role="employee")

        assert len(tools) == 1
        assert isinstance(tools[0], Tool)
        assert tools[0].name == "tool1"

    def test_discover_tools_failure(self, mcp_client, mock_client_instance):
        mock_client_instance.get.side_effect = mock_httpx.HTTPError("API Down")

        tools = mcp_client.discover_tools()

        assert len(tools) == 1
        assert tools[0].name == "search_documents"

    def test_get_tool_info_success(self, mcp_client, mock_client_instance):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "test_tool"}
        mock_client_instance.get.return_value = mock_response

        info = mcp_client.get_tool_info("test_tool")

        assert info == {"name": "test_tool"}

    def test_get_tool_info_failure(self, mcp_client, mock_client_instance):
        mock_client_instance.get.side_effect = mock_httpx.HTTPError("Not found")
        assert mcp_client.get_tool_info("unknown") is None

    def test_health_check_success(self, mcp_client, mock_client_instance):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client_instance.get.return_value = mock_response
        assert mcp_client.health_check() is True

    def test_health_check_failure(self, mcp_client, mock_client_instance):
        mock_client_instance.get.side_effect = mock_httpx.HTTPError("Down")
        assert mcp_client.health_check() is False
