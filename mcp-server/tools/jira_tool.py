"""
Jira integration tool for MCP server.
Provides access to Jira tickets, projects, and sprints.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

try:
    from jira import JIRA
    from jira.exceptions import JIRAError
    JIRA_AVAILABLE = True
except ImportError:
    JIRA = None
    JIRAError = Exception
    JIRA_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

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

def get_jira_client():
    """
    Initialize Jira client from environment variables.
    Returns None if configuration is missing.
    """
    if not JIRA_AVAILABLE:
        return None

    url = os.environ.get("JIRA_URL")
    username = os.environ.get("JIRA_USERNAME")
    token = os.environ.get("JIRA_API_TOKEN")

    if url and username and token:
        try:
            return JIRA(server=url, basic_auth=(username, token))
        except Exception as e:
            logger.error(f"Failed to connect to Jira: {e}")
            return None
    return None

def _issue_to_dict(issue) -> Dict[str, Any]:
    """Convert a Jira issue object to a dictionary."""
    return {
        "key": issue.key,
        "summary": issue.fields.summary,
        "description": issue.fields.description,
        "type": issue.fields.issuetype.name,
        "status": issue.fields.status.name,
        "priority": issue.fields.priority.name if hasattr(issue.fields, 'priority') and issue.fields.priority else "None",
        "assignee": issue.fields.assignee.emailAddress if hasattr(issue.fields, 'assignee') and issue.fields.assignee else None,
        "reporter": issue.fields.reporter.emailAddress if hasattr(issue.fields, 'reporter') and issue.fields.reporter else None,
        "created": issue.fields.created,
        "updated": issue.fields.updated,
        "sprint": getattr(issue.fields, 'customfield_10020', [None])[0].name if hasattr(issue.fields, 'customfield_10020') and getattr(issue.fields, 'customfield_10020') else None,
        # Note: customfield_10020 is commonly Sprint in Jira Cloud, but it might vary.
        # For robustness, we might omit sprint if not easily available or handle dynamic fields.
        "labels": issue.fields.labels
    }

def _search_jira_mock(
    query: str,
    project: str | None = None,
    status: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    ticket_type: str | None = None,
    limit: int = 10
) -> Dict[str, Any]:
    """Mock implementation of search_jira."""
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
    """
    client = get_jira_client()
    if not client:
        return _search_jira_mock(query, project, status, assignee, priority, ticket_type, limit)

    jql_parts = []
    
    # Text search (summary ~ query OR description ~ query)
    if query:
        # Sanitize query for JQL
        clean_query = query.replace('"', '\"')
        jql_parts.append(f'(summary ~ "{clean_query}" OR description ~ "{clean_query}")')
    
    if project:
        jql_parts.append(f'project = "{project}"')
    if status:
        jql_parts.append(f'status = "{status}"')
    if assignee:
        jql_parts.append(f'assignee = "{assignee}"')
    if priority:
        jql_parts.append(f'priority = "{priority}"')
    if ticket_type:
        jql_parts.append(f'issuetype = "{ticket_type}"')

    jql_query = " AND ".join(jql_parts) if jql_parts else "order by created DESC"

    try:
        issues = client.search_issues(jql_query, maxResults=limit)
        results = [_issue_to_dict(issue) for issue in issues]
        return {
            "success": True,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Jira search failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def _get_jira_ticket_mock(ticket_key: str) -> Dict[str, Any]:
    """Mock implementation of get_jira_ticket."""
    for ticket in MOCK_TICKETS:
        if ticket["key"] == ticket_key.upper():
            return {
                "success": True,
                **ticket,
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

def get_jira_ticket(ticket_key: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific Jira ticket.
    """
    client = get_jira_client()
    if not client:
        return _get_jira_ticket_mock(ticket_key)

    try:
        issue = client.issue(ticket_key)
        ticket_data = _issue_to_dict(issue)

        # Get comments
        comments = []
        if hasattr(issue.fields, 'comment') and issue.fields.comment:
            for comment in issue.fields.comment.comments:
                comments.append({
                    "author": comment.author.emailAddress if hasattr(comment.author, 'emailAddress') else comment.author.displayName,
                    "body": comment.body,
                    "created": comment.created
                })
        ticket_data["comments"] = comments

        # We're not fetching full changelog here as it requires expand='changelog' and parsing
        # For simplicity, returning empty changelog for real Jira or we could implement it if needed
        ticket_data["changelog"] = []

        return {
            "success": True,
            **ticket_data
        }
    except Exception as e:
        # Check if it's a 404
        if "Issue Does Not Exist" in str(e):
             return {
                "success": False,
                "error": f"Ticket not found: {ticket_key}"
            }
        return {
            "success": False,
            "error": str(e)
        }

def _get_project_info_mock(project_key: str) -> Dict[str, Any]:
    """Mock implementation of get_project_info."""
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

def get_project_info(project_key: str) -> Dict[str, Any]:
    """
    Get information about a Jira project.
    """
    client = get_jira_client()
    if not client:
        return _get_project_info_mock(project_key)

    try:
        project = client.project(project_key)

        # Get ticket counts (this is expensive in real Jira, maybe we use JQL)
        # JQL: project = KEY
        # We can group by status

        # Note: 'jira' library doesn't have a direct 'group by' search.
        # We can simulate it by searching for all issues in project (limit=0, json_result=True) if API allows metadata,
        # but standard search_issues gets issues.
        # A lightweight way is to search for common statuses or just total count.

        # Getting total count
        jql = f'project = "{project_key}"'
        issues = client.search_issues(jql, maxResults=0, json_result=True)
        total_tickets = issues['total']

        return {
            "success": True,
            "key": project.key,
            "name": project.name,
            "description": project.description if hasattr(project, 'description') else "",
            "lead": project.lead.emailAddress if hasattr(project, 'lead') and hasattr(project.lead, 'emailAddress') else getattr(project.lead, 'displayName', ''),
            "type": project.projectTypeKey if hasattr(project, 'projectTypeKey') else "software",
            "total_tickets": total_tickets,
            "ticket_counts": {"info": "Status breakdown not available in real-time mode"} # optimization
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def _list_sprints_mock(
    project_key: str | None = None,
    state: str | None = None
) -> Dict[str, Any]:
    """Mock implementation of list_sprints."""
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

def list_sprints(
    project_key: str | None = None,
    state: str | None = None
) -> Dict[str, Any]:
    """
    List sprints for a project.
    Note: In real Jira, this attempts to find boards associated with the project.
    """
    client = get_jira_client()
    if not client:
        return _list_sprints_mock(project_key, state)

    try:
        # Try to find boards for the project
        boards = []
        if project_key:
            boards = client.boards(name=project_key)
            if not boards:
                # Fallback: try to find boards by project key filter
                 boards = client.boards(projectKeyOrID=project_key)
        else:
            # If no project key, we might return too many sprints.
            # Limit to first few boards? Or fail?
            # Mock behavior returns all sprints.
            return {
                "success": False,
                "error": "Project key is required for real Jira sprint listing"
            }

        sprints_data = []
        for board in boards:
            try:
                sprints = client.sprints(board.id, state=state)
                for sprint in sprints:
                    # Get tickets in sprint? This is expensive.
                    # Mock implementation returns tickets. Real implementation might skip it for performance
                    # unless explicitly requested, but the signature matches mock.
                    # We will return basic sprint info for now.

                    sprints_data.append({
                        "id": sprint.id,
                        "name": sprint.name,
                        "state": sprint.state,
                        "start_date": getattr(sprint, 'startDate', None),
                        "end_date": getattr(sprint, 'endDate', None),
                        "goal": getattr(sprint, 'goal', ""),
                        "board_id": board.id
                    })
            except Exception:
                continue

        return {
            "success": True,
            "count": len(sprints_data),
            "sprints": sprints_data
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_my_tickets(email: str) -> Dict[str, Any]:
    """
    Get tickets assigned to a specific user.
    """
    client = get_jira_client()
    if not client:
        # Mock implementation inline for simplicity as it wasn't separate before
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

    try:
        # JQL search
        jql = f'assignee = "{email}" AND status != Done ORDER BY updated DESC'
        issues = client.search_issues(jql, maxResults=50)
        results = [_issue_to_dict(issue) for issue in issues]

        return {
            "success": True,
            "assignee": email,
            "count": len(results),
            "tickets": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
