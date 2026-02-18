
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

# Add backend/app to path if needed, but PYTHONPATH should handle it
import sys
import os

# We need to mock settings and other deps before importing the service to avoid side effects
# However, for unit testing a method that doesn't use those deps, we can just mock the class instantiation.

# Let's try importing directly, assuming PYTHONPATH is set correctly.
try:
    from services.ai_orchestrator import AIOrchestrator
except ImportError:
    # If import fails, we might need to adjust sys.path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../app")))
    from services.ai_orchestrator import AIOrchestrator

class TestAIOrchestratorPromptBuilder:

    @pytest.fixture
    def orchestrator(self):
        """Fixture to return an AIOrchestrator instance with mocked dependencies."""
        with patch("services.ai_orchestrator.MCPClient") as MockMCP:
            # We also need to patch settings if they are used in __init__
            # In the current code, settings are used in properties, not __init__.
            # But MCPClient() is instantiated in __init__.
            orchestrator = AIOrchestrator()
            return orchestrator

    def test_build_prompt_basic(self, orchestrator):
        """Test basic prompt construction with query and RAG context."""
        query = "How do I request time off?"
        rag_context = "Policy: Request time off via the HR portal."
        tool_results: List[Dict[str, Any]] = []
        conversation_history: List[Dict[str, str]] = []

        prompt = orchestrator._build_prompt(
            query=query,
            rag_context=rag_context,
            tool_results=tool_results,
            conversation_history=conversation_history
        )

        assert "Context from Documents" in prompt
        assert rag_context in prompt
        assert "User Question" in prompt
        assert query in prompt
        assert "Conversation History" not in prompt
        assert "Tool Results" not in prompt

    def test_build_prompt_with_history(self, orchestrator):
        """Test prompt construction with conversation history."""
        query = "And how many days do I have?"
        rag_context = "Policy: You have 20 days."
        tool_results: List[Dict[str, Any]] = []
        conversation_history = [
            {"role": "user", "content": "How do I request time off?"},
            {"role": "assistant", "content": "Via HR portal."}
        ]

        prompt = orchestrator._build_prompt(
            query=query,
            rag_context=rag_context,
            tool_results=tool_results,
            conversation_history=conversation_history
        )

        assert "Conversation History" in prompt
        # Verify formatting
        assert "User: How do I request time off?" in prompt
        assert "Assistant: Via HR portal." in prompt

    def test_build_prompt_with_tool_results(self, orchestrator):
        """Test prompt construction with tool execution results."""
        query = "What is the status of JIRA-123?"
        rag_context = ""
        tool_results = [
            {"tool": "search_jira", "data": {"key": "JIRA-123", "status": "In Progress"}}
        ]
        conversation_history: List[Dict[str, str]] = []

        prompt = orchestrator._build_prompt(
            query=query,
            rag_context=rag_context,
            tool_results=tool_results,
            conversation_history=conversation_history
        )

        assert "Tool Results" in prompt
        assert "**search_jira**" in prompt
        # Check that tool data is stringified
        assert "JIRA-123" in prompt
        assert "In Progress" in prompt

    def test_build_prompt_history_truncation(self, orchestrator):
        """Test that conversation history is truncated to last 4 messages."""
        query = "Current question"
        rag_context = ""
        tool_results: List[Dict[str, Any]] = []
        # Create 10 messages
        conversation_history = [{"role": "user", "content": f"msg {i}"} for i in range(10)]

        prompt = orchestrator._build_prompt(
            query=query,
            rag_context=rag_context,
            tool_results=tool_results,
            conversation_history=conversation_history
        )

        # Should only have last 4 messages (6, 7, 8, 9)
        assert "msg 9" in prompt
        assert "msg 6" in prompt
        assert "msg 5" not in prompt

    def test_build_prompt_message_truncation(self, orchestrator):
        """Test that individual long messages in history are truncated."""
        query = "Current question"
        rag_context = ""
        tool_results: List[Dict[str, Any]] = []
        # Create a message longer than 500 chars
        long_message = "a" * 1000
        conversation_history = [{"role": "user", "content": long_message}]

        prompt = orchestrator._build_prompt(
            query=query,
            rag_context=rag_context,
            tool_results=tool_results,
            conversation_history=conversation_history
        )

        # Check if the message is truncated (len 500)
        # Verify first 500 chars are present
        assert long_message[:500] in prompt
        # Verify the full message is NOT present
        # Since prompt contains other text, checking exact match of full message should fail if truncated properly
        assert long_message not in prompt
