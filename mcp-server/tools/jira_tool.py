"""
Jira integration tool for MCP server.
Provides access to Jira tickets, projects, and sprints.
"""

from typing import Dict, Any


# Mock Jira data for demonstration
MOCK_PROJECTS = {
    "EA": {
        "key": "EA",
        "name": "Enterprise Assistant",
        "description": "AI-powered enterprise knowledge assistant",
        "lead": "alice@company.com",
        "type": "software"
    },
    "DP": {
        "key": "DP",
        "name": "Data Pipeline",
        "description": "ETL and data processing pipeline",
        "lead": "bob@company.com",
        "type": "software"
    },
    "HR": {
        "key": "HR",
        "name": "HR Operations",
        "description": "Human resources tasks and processes",
        "lead": "jane@company.com",
        "type": "business"
    }
}

MOCK_TICKETS = [
    {
        "key": "EA-101",
        "summary": "Implement streaming responses for chat API",
        "description": "Users are experiencing slow response times. We need to implement streaming responses to improve UX.",
        "type": "Story",
        "status": "In Progress",
        "priority": "High",
        "assignee": "alice@company.com",
        "reporter": "product@company.com",
        "created": "2024-01-10T09:00:00Z",
        "updated": "2024-01-15T14:30:00Z",
        "sprint": "Sprint 42",
        "story_points": 5,
        "labels": ["backend", "performance"]
    },
    {
        "key": "EA-100",
        "summary": "Add role-based access control for tools",
        "description": "Implement RBAC so different user roles have different tool access permissions.",
        "type": "Story",
        "status": "Done",
        "priority": "Critical",
        "assignee": "bob@company.com",
        "reporter": "security@company.com",
        "created": "2024-01-05T10:00:00Z",
        "updated": "2024-01-12T16:00:00Z",
        "sprint": "Sprint 41",
        "story_points": 8,
        "labels": ["security", "backend"]
    },
    {
        "key": "EA-99",
        "summary": "Fix vector store memory leak",
        "description": "Memory usage grows unbounded when adding documents to the vector store.",
        "type": "Bug",
        "status": "Done",
        "priority": "Critical",
        "assignee": "alice@company.com",
        "reporter": "ops@company.com",
        "created": "2024-01-03T08:00:00Z",
        "updated": "2024-01-08T11:00:00Z",
        "sprint": "Sprint 41",
        "story_points": 3,
        "labels": ["bug", "vector-store"]
    },
    {
        "key": "EA-98",
        "summary": "Add Jira integration documentation",
        "description": "Document the Jira integration API and usage examples.",
        "type": "Task",
        "status": "To Do",
        "priority": "Medium",
        "assignee": None,
        "reporter": "docs@company.com",
        "created": "2024-01-02T14:00:00Z",
        "updated": "2024-01-02T14:00:00Z",
        "sprint": "Sprint 42",
        "story_points": 2,
        "labels": ["documentation"]
    },
    {
        "key": "DP-55",
        "summary": "Optimize Spark job for daily aggregation",
        "description": "The daily aggregation job is taking too long. Need to optimize partitioning.",
        "type": "Story",
        "status": "In Progress",
        "priority": "High",
        "assignee": "charlie@company.com",
        "reporter": "data@company.com",
        "created": "2024-01-08T10:00:00Z",
        "updated": "2024-01-14T09:00:00Z",
        "sprint": "Sprint 42",
        "story_points": 5,
        "labels": ["spark", "performance"]
    }
]

MOCK_SPRINTS = [
    {
        "id": 42,
        "name": "Sprint 42",
        "state": "active",
        "start_date": "2024-01-08T00:00:00Z",
        "end_date": "2024-01-22T00:00:00Z",
        "goal": "Complete streaming API and Jira integration"
    },
    {
        "id": 41,
        "name": "Sprint 41",
        "state": "closed",
        "start_date": "2023-12-25T00:00:00Z",
        "end_date": "2024-01-08T00:00:00Z",
        "goal": "Security improvements and bug fixes"
    }
]


def search_jira(
    query: str,
    project: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    ticket_type: str | None = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search Jira tickets using JQL-like filters.
    
    Args:
        query: Text search query
        project: Filter by project key (e.g., "EA")
        status: Filter by status (e.g., "In Progress", "Done")
        assignee: Filter by assignee email
        priority: Filter by priority (e.g., "High", "Critical")
        ticket_type: Filter by type (e.g., "Bug", "Story")
        limit: Maximum results to return
    
    Returns:
        Search results
    """
    query_lower = query.lower()
    results = []
    
    for ticket in MOCK_TICKETS:
        # Text search
        if query_lower and not (
            query_lower in ticket["summary"].lower() or
            query_lower in ticket["description"].lower() or
            query_lower in ticket["key"].lower()
        ):
            continue
        
        # Filters
        if project and not ticket["key"].startswith(project):
            continue
        if status and ticket["status"].lower() != status.lower():
            continue
        if assignee and ticket["assignee"] != assignee:
            continue
        if priority and ticket["priority"].lower() != priority.lower():
            continue
        if ticket_type and ticket["type"].lower() != ticket_type.lower():
            continue
        
        results.append(ticket)
        
        if len(results) >= limit:
            break
    
    return {
        "success": True,
        "count": len(results),
        "results": results
    }


def get_jira_ticket(ticket_key: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific Jira ticket.
    
    Args:
        ticket_key: Jira ticket key (e.g., "EA-101")
    
    Returns:
        Ticket details
    """
    for ticket in MOCK_TICKETS:
        if ticket["key"] == ticket_key.upper():
            return {
                "success": True,
                **ticket,
                # Add mock comments
                "comments": [
                    {
                        "author": "alice@company.com",
                        "body": "Started working on this. Initial implementation looks promising.",
                        "created": "2024-01-11T10:00:00Z"
                    },
                    {
                        "author": "product@company.com",
                        "body": "Great progress! Let me know if you need any clarification on requirements.",
                        "created": "2024-01-12T14:00:00Z"
                    }
                ],
                # Add mock history
                "changelog": [
                    {
                        "author": "alice@company.com",
                        "field": "status",
                        "from": "To Do",
                        "to": "In Progress",
                        "created": "2024-01-11T09:00:00Z"
                    }
                ]
            }
    
    return {
        "success": False,
        "error": f"Ticket not found: {ticket_key}"
    }


def get_project_info(project_key: str) -> Dict[str, Any]:
    """
    Get information about a Jira project.
    
    Args:
        project_key: Project key (e.g., "EA")
    
    Returns:
        Project information
    """
    if project_key.upper() in MOCK_PROJECTS:
        project = MOCK_PROJECTS[project_key.upper()]
        
        # Count tickets by status
        status_counts = {}
        for ticket in MOCK_TICKETS:
            if ticket["key"].startswith(project_key.upper()):
                status = ticket["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "success": True,
            **project,
            "ticket_counts": status_counts,
            "total_tickets": sum(status_counts.values())
        }
    
    return {
        "success": False,
        "error": f"Project not found: {project_key}"
    }


def list_sprints(
    project_key: str | None = None,
    state: str | None = None
) -> Dict[str, Any]:
    """
    List sprints for a project.
    
    Args:
        project_key: Optional project key to filter
        state: Filter by state (active, closed, future)
    
    Returns:
        List of sprints
    """
    results = []
    
    for sprint in MOCK_SPRINTS:
        if state and sprint["state"] != state:
            continue
        
        # Get tickets in sprint
        sprint_tickets = [
            {"key": t["key"], "summary": t["summary"], "status": t["status"]}
            for t in MOCK_TICKETS
            if t.get("sprint") == sprint["name"]
        ]
        
        if project_key:
            sprint_tickets = [
                t for t in sprint_tickets
                if t["key"].startswith(project_key.upper())
            ]
        
        results.append({
            **sprint,
            "tickets": sprint_tickets,
            "ticket_count": len(sprint_tickets)
        })
    
    return {
        "success": True,
        "count": len(results),
        "sprints": results
    }


def get_my_tickets(email: str) -> Dict[str, Any]:
    """
    Get tickets assigned to a specific user.
    
    Args:
        email: User's email address
    
    Returns:
        List of assigned tickets
    """
    results = [
        ticket for ticket in MOCK_TICKETS
        if ticket["assignee"] == email
    ]
    
    return {
        "success": True,
        "assignee": email,
        "count": len(results),
        "tickets": results
    }
