"""
Database query tool for MCP server.
Allows read-only SQL queries on enterprise databases.
"""

import re
from typing import Dict, Any, List
import sqlite3
from contextlib import contextmanager

# In production, this would connect to your actual database
# For demo purposes, we use an in-memory SQLite database

# Sample data for demonstration
SAMPLE_DATA = {
    "employees": [
        {"id": 1, "name": "John Doe", "department": "Engineering", "salary": 85000},
        {"id": 2, "name": "Jane Smith", "department": "HR", "salary": 75000},
        {"id": 3, "name": "Bob Johnson", "department": "Sales", "salary": 90000},
        {"id": 4, "name": "Alice Brown", "department": "Engineering", "salary": 95000},
    ],
    "projects": [
        {"id": 1, "name": "AI Assistant", "status": "active", "budget": 500000},
        {"id": 2, "name": "Data Pipeline", "status": "completed", "budget": 250000},
        {"id": 3, "name": "Mobile App", "status": "active", "budget": 350000},
    ],
    "departments": [
        {"id": 1, "name": "Engineering", "head": "Alice Brown", "headcount": 15},
        {"id": 2, "name": "HR", "head": "Jane Smith", "headcount": 5},
        {"id": 3, "name": "Sales", "head": "Bob Johnson", "headcount": 10},
    ],
}


# SQL keywords that are NOT allowed (write operations)
DISALLOWED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", 
    "TRUNCATE", "REPLACE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
]

# Maximum rows to return
MAX_ROWS = 100


def _init_demo_db() -> sqlite3.Connection:
    """Initialize demo database with sample data."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            department TEXT,
            salary INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            name TEXT,
            status TEXT,
            budget INTEGER
        )
    """)
    
    cursor.execute("""
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            head TEXT,
            headcount INTEGER
        )
    """)
    
    # Insert sample data
    for emp in SAMPLE_DATA["employees"]:
        cursor.execute(
            "INSERT INTO employees VALUES (?, ?, ?, ?)",
            (emp["id"], emp["name"], emp["department"], emp["salary"])
        )
    
    for proj in SAMPLE_DATA["projects"]:
        cursor.execute(
            "INSERT INTO projects VALUES (?, ?, ?, ?)",
            (proj["id"], proj["name"], proj["status"], proj["budget"])
        )
    
    for dept in SAMPLE_DATA["departments"]:
        cursor.execute(
            "INSERT INTO departments VALUES (?, ?, ?, ?)",
            (dept["id"], dept["name"], dept["head"], dept["headcount"])
        )
    
    conn.commit()
    return conn


# Global demo database
_demo_db: sqlite3.Connection | None = None


def _get_db() -> sqlite3.Connection:
    """Get database connection."""
    global _demo_db
    if _demo_db is None:
        _demo_db = _init_demo_db()
    return _demo_db


def _validate_query(query: str) -> tuple[bool, str]:
    """
    Validate that the query is safe (SELECT only).
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    query_upper = query.upper().strip()
    
    # Must start with SELECT or WITH
    if not (query_upper.startswith("SELECT") or query_upper.startswith("WITH")):
        return False, "Only SELECT queries are allowed"
    
    # Check for disallowed keywords
    for keyword in DISALLOWED_KEYWORDS:
        # Match whole words only
        if re.search(rf'\b{keyword}\b', query_upper):
            return False, f"Query contains disallowed keyword: {keyword}"
    
    # Check for suspicious patterns
    if "--" in query or "/*" in query:
        return False, "SQL comments are not allowed"
    
    if ";" in query and not query.strip().endswith(";"):
        return False, "Multiple statements are not allowed"
    
    return True, ""


def query_database(query: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Execute a read-only SQL query on the database.
    
    Args:
        query: SQL SELECT query to execute
        params: Optional parameters for the query
    
    Returns:
        Dictionary with columns and rows
    """
    # Validate query
    is_valid, error = _validate_query(query)
    if not is_valid:
        return {
            "success": False,
            "error": error,
            "rows": [],
            "columns": []
        }
    
    try:
        conn = _get_db()
        cursor = conn.cursor()
        
        # Add LIMIT if not present
        query_upper = query.upper()
        if "LIMIT" not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {MAX_ROWS}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Get column names
        columns = [description[0] for description in cursor.description] if cursor.description else []
        
        # Convert to list of dicts
        results = [dict(row) for row in rows]
        
        return {
            "success": True,
            "columns": columns,
            "rows": results,
            "row_count": len(results),
            "truncated": len(results) >= MAX_ROWS
        }
    
    except sqlite3.Error as e:
        return {
            "success": False,
            "error": f"Database error: {str(e)}",
            "rows": [],
            "columns": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "rows": [],
            "columns": []
        }


def get_schema() -> Dict[str, Any]:
    """
    Get the database schema.
    
    Returns:
        Dictionary describing available tables and columns
    """
    return {
        "tables": {
            "employees": {
                "description": "Employee information",
                "columns": ["id", "name", "department", "salary"]
            },
            "projects": {
                "description": "Project information",
                "columns": ["id", "name", "status", "budget"]
            },
            "departments": {
                "description": "Department information",
                "columns": ["id", "name", "head", "headcount"]
            }
        }
    }
