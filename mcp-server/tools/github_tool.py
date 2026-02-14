"""
GitHub integration tool for MCP server.
Provides access to GitHub repositories, issues, and code.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime


# In production, you would use the GitHub API with a token
# For demo purposes, we provide mock data

MOCK_REPOS = {
    "enterprise-ai-assistant": {
        "full_name": "company/enterprise-ai-assistant",
        "description": "AI-powered knowledge assistant for enterprise",
        "language": "Python",
        "stars": 42,
        "forks": 8,
        "open_issues": 5,
        "default_branch": "main",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    "data-pipeline": {
        "full_name": "company/data-pipeline",
        "description": "ETL data pipeline for analytics",
        "language": "Python",
        "stars": 28,
        "forks": 4,
        "open_issues": 2,
        "default_branch": "main",
        "updated_at": "2024-01-14T15:45:00Z"
    }
}

MOCK_ISSUES = [
    {
        "number": 101,
        "title": "Add streaming response support",
        "state": "open",
        "labels": ["enhancement", "priority-high"],
        "assignee": "alice",
        "created_at": "2024-01-10T09:00:00Z",
        "body": "We need to implement streaming responses for better UX..."
    },
    {
        "number": 99,
        "title": "Fix memory leak in vector store",
        "state": "closed",
        "labels": ["bug", "priority-critical"],
        "assignee": "bob",
        "created_at": "2024-01-08T14:30:00Z",
        "body": "There's a memory leak when adding large documents..."
    },
    {
        "number": 95,
        "title": "Add Jira integration",
        "state": "open",
        "labels": ["enhancement", "integration"],
        "assignee": None,
        "created_at": "2024-01-05T11:00:00Z",
        "body": "Integrate with Jira for ticket management..."
    }
]

MOCK_PRS = [
    {
        "number": 102,
        "title": "feat: Add RAG service with semantic search",
        "state": "open",
        "author": "alice",
        "base": "main",
        "head": "feature/rag-service",
        "created_at": "2024-01-12T10:00:00Z",
        "changed_files": 8,
        "additions": 450,
        "deletions": 32
    },
    {
        "number": 100,
        "title": "fix: Resolve database connection pooling issue",
        "state": "merged",
        "author": "bob",
        "base": "main",
        "head": "fix/db-pooling",
        "created_at": "2024-01-09T16:00:00Z",
        "changed_files": 3,
        "additions": 45,
        "deletions": 12
    }
]


def search_github(
    query: str,
    search_type: str = "issues",
    state: str | None = None,
    labels: List[str] | None = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search GitHub for issues, PRs, or repositories.
    
    Args:
        query: Search query string
        search_type: Type of search - "issues", "prs", "repos"
        state: Filter by state - "open", "closed", "all"
        labels: Filter by labels (issues/PRs only)
        limit: Maximum results to return
    
    Returns:
        Search results
    """
    query_lower = query.lower()
    
    if search_type == "repos":
        # Search repositories
        results = []
        for name, repo in MOCK_REPOS.items():
            if query_lower in name.lower() or query_lower in repo["description"].lower():
                results.append({**repo, "name": name})
        
        return {
            "success": True,
            "type": "repositories",
            "count": len(results[:limit]),
            "results": results[:limit]
        }
    
    elif search_type == "prs":
        # Search pull requests
        results = []
        for pr in MOCK_PRS:
            if query_lower in pr["title"].lower():
                if state and state != "all" and pr["state"] != state:
                    continue
                results.append(pr)
        
        return {
            "success": True,
            "type": "pull_requests",
            "count": len(results[:limit]),
            "results": results[:limit]
        }
    
    else:  # issues
        # Search issues
        results = []
        for issue in MOCK_ISSUES:
            if query_lower in issue["title"].lower() or query_lower in issue["body"].lower():
                if state and state != "all" and issue["state"] != state:
                    continue
                if labels:
                    if not any(label in issue["labels"] for label in labels):
                        continue
                results.append(issue)
        
        return {
            "success": True,
            "type": "issues",
            "count": len(results[:limit]),
            "results": results[:limit]
        }


def get_github_file(
    repo: str,
    path: str,
    ref: str = "main"
) -> Dict[str, Any]:
    """
    Get contents of a file from a GitHub repository.
    
    Args:
        repo: Repository name (e.g., "enterprise-ai-assistant")
        path: Path to the file in the repository
        ref: Branch, tag, or commit SHA
    
    Returns:
        File contents and metadata
    """
    # Mock file content
    mock_files = {
        "README.md": """# Enterprise AI Assistant

An AI-powered knowledge assistant for enterprise use.

## Features
- Natural language queries
- Document search
- Database queries
- GitHub integration
- Jira integration

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables
4. Run: `uvicorn main:app --reload`
""",
        "config.py": """# Configuration settings
DATABASE_URL = "postgresql://localhost/enterprise_ai"
OPENAI_API_KEY = "sk-..."
MCP_SERVER_URL = "http://localhost:3333"
"""
    }
    
    filename = path.split("/")[-1]
    
    if filename in mock_files:
        content = mock_files[filename]
        return {
            "success": True,
            "path": path,
            "repo": repo,
            "ref": ref,
            "content": content,
            "size": len(content),
            "encoding": "utf-8"
        }
    
    return {
        "success": False,
        "error": f"File not found: {path}",
        "path": path,
        "repo": repo
    }


def get_repo_info(repo: str) -> Dict[str, Any]:
    """
    Get information about a GitHub repository.
    
    Args:
        repo: Repository name
    
    Returns:
        Repository metadata
    """
    if repo in MOCK_REPOS:
        return {
            "success": True,
            **MOCK_REPOS[repo],
            "name": repo
        }
    
    return {
        "success": False,
        "error": f"Repository not found: {repo}"
    }


def list_repo_contents(
    repo: str,
    path: str = "",
    ref: str = "main"
) -> Dict[str, Any]:
    """
    List contents of a directory in a repository.
    
    Args:
        repo: Repository name
        path: Directory path (empty for root)
        ref: Branch, tag, or commit SHA
    
    Returns:
        List of files and directories
    """
    # Mock directory structure
    mock_structure = {
        "": [
            {"name": "README.md", "type": "file", "size": 1024},
            {"name": "requirements.txt", "type": "file", "size": 256},
            {"name": "backend", "type": "dir"},
            {"name": "mcp-server", "type": "dir"},
            {"name": "docker", "type": "dir"},
        ],
        "backend": [
            {"name": "main.py", "type": "file", "size": 512},
            {"name": "requirements.txt", "type": "file", "size": 128},
            {"name": "app", "type": "dir"},
        ],
        "backend/app": [
            {"name": "core", "type": "dir"},
            {"name": "api", "type": "dir"},
            {"name": "models", "type": "dir"},
        ]
    }
    
    if path in mock_structure:
        return {
            "success": True,
            "repo": repo,
            "path": path,
            "ref": ref,
            "contents": mock_structure[path]
        }
    
    return {
        "success": False,
        "error": f"Path not found: {path}",
        "repo": repo,
        "path": path
    }
