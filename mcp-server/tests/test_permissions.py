import pytest
from permissions import can_access, get_allowed_tools

@pytest.mark.parametrize("role, tool, expected", [
    # Admin access
    ("admin", "search_documents", True),
    ("admin", "query_database", True),
    ("admin", "search_github", True),
    ("admin", "get_jira_ticket", True),

    # Manager access
    ("manager", "search_documents", True),
    ("manager", "query_database", True),
    ("manager", "search_jira", True),
    ("manager", "search_github", False),  # Manager cannot access github

    # Employee access
    ("employee", "search_documents", True),
    ("employee", "query_database", False),
    ("employee", "search_jira", False),

    # Unknown role
    ("unknown", "search_documents", False),

    # Unknown tool
    ("admin", "non_existent_tool", False),
    ("employee", "non_existent_tool", False),

    # Empty inputs
    ("", "search_documents", False),
    ("admin", "", False),
])
def test_can_access(role, tool, expected):
    """Test that can_access correctly identifies authorized and unauthorized access."""
    assert can_access(role, tool) == expected

def test_get_allowed_tools():
    """Test that get_allowed_tools returns the correct tools for each role."""
    # Test admin
    admin_tools = get_allowed_tools("admin")
    assert "search_documents" in admin_tools
    assert "search_github" in admin_tools
    assert len(admin_tools) == 8

    # Test manager
    manager_tools = get_allowed_tools("manager")
    assert "search_documents" in manager_tools
    assert "query_database" in manager_tools
    assert "search_github" not in manager_tools
    assert len(manager_tools) == 6

    # Test employee
    employee_tools = get_allowed_tools("employee")
    assert employee_tools == ["search_documents"]

    # Test unknown role
    unknown_tools = get_allowed_tools("unknown")
    assert unknown_tools == []
