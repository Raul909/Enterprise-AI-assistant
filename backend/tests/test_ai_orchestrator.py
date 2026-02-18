import pytest
from unittest.mock import MagicMock, patch

# AIOrchestrator imports libraries that we mocked or might have issues,
# but conftest.py should handle it.
from services.ai_orchestrator import AIOrchestrator


class TestAIOrchestrator:
    @pytest.fixture
    def orchestrator(self):
        # We need to mock the dependencies created in __init__ if they do network calls or heavy lifting.
        # AIOrchestrator.__init__ creates MCPClient.
        # It also has lazy properties for openai_client and anthropic_client.

        # We can patch MCPClient to avoid it doing anything real,
        # although its __init__ is light.
        with patch("services.ai_orchestrator.MCPClient") as mock_mcp:
            orchestrator = AIOrchestrator()
            yield orchestrator

    def test_prepare_tool_params_search_documents(self, orchestrator):
        # Test search_documents with department
        user = {"department": "engineering"}
        query = "how to deploy"
        params = orchestrator._prepare_tool_params("search_documents", query, user)
        assert params == {"query": query, "department": "engineering"}

    def test_prepare_tool_params_search_documents_default_department(
        self, orchestrator
    ):
        # Test search_documents without department in user dict
        user = {}
        query = "company policy"
        params = orchestrator._prepare_tool_params("search_documents", query, user)
        assert params == {"query": query, "department": "general"}

    def test_prepare_tool_params_query_database(self, orchestrator):
        # Test query_database
        user = {"department": "hr"}
        query = "show me employees"
        params = orchestrator._prepare_tool_params("query_database", query, user)
        # current implementation returns a fixed query
        assert params == {"query": "SELECT * FROM employees LIMIT 5"}

    def test_prepare_tool_params_search_github(self, orchestrator):
        # Test search_github
        user = {}
        query = "find bug in login"
        params = orchestrator._prepare_tool_params("search_github", query, user)
        assert params == {"query": query, "search_type": "issues", "state": "open"}

    def test_prepare_tool_params_search_jira(self, orchestrator):
        # Test search_jira
        user = {}
        query = "ticket about ui"
        params = orchestrator._prepare_tool_params("search_jira", query, user)
        assert params == {"query": query, "status": None}

    def test_prepare_tool_params_default_tool(self, orchestrator):
        # Test unknown tool
        user = {}
        query = "some query"
        params = orchestrator._prepare_tool_params("unknown_tool", query, user)
        assert params == {"query": query}
