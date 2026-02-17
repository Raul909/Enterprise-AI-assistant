import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add mcp-server to path
sys.path.append(os.path.join(os.getcwd(), 'mcp-server'))

from tools.jira_tool import search_jira, get_jira_ticket, get_project_info, list_sprints

class TestJiraTool(unittest.TestCase):

    def setUp(self):
        # Clear env vars
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_mock_search_jira(self):
        # Test mock fallback
        result = search_jira(query="streaming")
        self.assertTrue(result["success"])
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["key"], "EA-101")

    def test_mock_get_ticket(self):
        result = get_jira_ticket("EA-101")
        self.assertTrue(result["success"])
        self.assertEqual(result["key"], "EA-101")

    @patch('tools.jira_tool.get_jira_client')
    def test_real_search_jira(self, mock_get_client):
        # Setup mock client
        mock_client = MagicMock()
        mock_issue = MagicMock()
        mock_issue.key = "REAL-123"
        mock_issue.fields.summary = "Real Summary"
        mock_issue.fields.description = "Real Description"
        mock_issue.fields.issuetype.name = "Bug"
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.priority.name = "High"
        mock_issue.fields.assignee.emailAddress = "assignee@example.com"
        mock_issue.fields.reporter.emailAddress = "reporter@example.com"
        mock_issue.fields.created = "2024-01-01"
        mock_issue.fields.updated = "2024-01-02"
        mock_issue.fields.labels = ["test"]

        # Handle custom field for sprint
        mock_sprint = MagicMock()
        mock_sprint.name = "Sprint 1"
        mock_issue.fields.customfield_10020 = [mock_sprint]

        mock_client.search_issues.return_value = [mock_issue]
        mock_get_client.return_value = mock_client

        result = search_jira(query="test")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["key"], "REAL-123")
        self.assertEqual(result["results"][0]["sprint"], "Sprint 1")

        # Verify JQL
        args, kwargs = mock_client.search_issues.call_args
        self.assertIn('summary ~ "test" OR description ~ "test"', args[0])

    @patch('tools.jira_tool.get_jira_client')
    def test_real_get_ticket(self, mock_get_client):
        mock_client = MagicMock()
        mock_issue = MagicMock()
        mock_issue.key = "REAL-123"
        mock_issue.fields.summary = "Real Summary"
        mock_issue.fields.description = "Real Description"
        mock_issue.fields.issuetype.name = "Bug"
        mock_issue.fields.status.name = "Open"
        mock_issue.fields.priority.name = "High"
        mock_issue.fields.assignee.emailAddress = "assignee@example.com"
        mock_issue.fields.reporter.emailAddress = "reporter@example.com"
        mock_issue.fields.created = "2024-01-01"
        mock_issue.fields.updated = "2024-01-02"
        mock_issue.fields.labels = ["test"]

        # Mock sprint
        mock_sprint = MagicMock()
        mock_sprint.name = "Sprint 1"
        mock_issue.fields.customfield_10020 = [mock_sprint]

        # Mock comment
        mock_comment = MagicMock()
        mock_comment.author.emailAddress = "user@example.com"
        mock_comment.body = "A comment"
        mock_comment.created = "2024-01-01"
        mock_issue.fields.comment.comments = [mock_comment]

        mock_client.issue.return_value = mock_issue
        mock_get_client.return_value = mock_client

        result = get_jira_ticket("REAL-123")

        self.assertTrue(result["success"])
        self.assertEqual(result["key"], "REAL-123")
        self.assertEqual(len(result["comments"]), 1)
        self.assertEqual(result["comments"][0]["body"], "A comment")

    @patch('tools.jira_tool.get_jira_client')
    def test_real_project_info(self, mock_get_client):
        mock_client = MagicMock()
        mock_project = MagicMock()
        mock_project.key = "REAL"
        mock_project.name = "Real Project"
        mock_project.description = "Real Description"
        mock_project.lead.emailAddress = "lead@example.com"
        mock_project.projectTypeKey = "software"

        mock_client.project.return_value = mock_project
        # Mock search for total count
        mock_client.search_issues.return_value = {'total': 100}

        mock_get_client.return_value = mock_client

        result = get_project_info("REAL")
        self.assertTrue(result["success"])
        self.assertEqual(result["name"], "Real Project")
        self.assertEqual(result["total_tickets"], 100)

    @patch('tools.jira_tool.get_jira_client')
    def test_real_list_sprints(self, mock_get_client):
        mock_client = MagicMock()
        mock_board = MagicMock()
        mock_board.id = 1
        mock_client.boards.return_value = [mock_board]

        mock_sprint = MagicMock()
        mock_sprint.id = 10
        mock_sprint.name = "Sprint 10"
        mock_sprint.state = "active"
        mock_client.sprints.return_value = [mock_sprint]

        mock_get_client.return_value = mock_client

        result = list_sprints(project_key="REAL")
        self.assertTrue(result["success"])
        self.assertEqual(len(result["sprints"]), 1)
        self.assertEqual(result["sprints"][0]["name"], "Sprint 10")

if __name__ == '__main__':
    unittest.main()
