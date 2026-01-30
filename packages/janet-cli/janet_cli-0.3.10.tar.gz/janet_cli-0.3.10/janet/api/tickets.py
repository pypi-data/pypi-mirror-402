"""Ticket API methods."""

from typing import List, Dict, Optional

from janet.api.client import APIClient
from janet.config.manager import ConfigManager


class TicketAPI(APIClient):
    """API methods for ticket management."""

    def __init__(self, config_manager: ConfigManager):
        """
        Initialize ticket API.

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__(config_manager)

    def list_tickets(
        self,
        project_id: str,
        limit: int = 1000,
        offset: int = 0,
        show_resolved: bool = True,
    ) -> Dict:
        """
        List tickets for a project.

        Args:
            project_id: Project ID
            limit: Maximum tickets to return
            offset: Pagination offset
            show_resolved: Include resolved tickets older than 7 days

        Returns:
            Dictionary with tickets and metadata

        Raises:
            NetworkError: If API request fails
        """
        endpoint = f"/api/v1/projects/{project_id}/tickets/list"

        data = {
            "limit": limit,
            "offset": offset,
            "show_resolved_over_7_days": show_resolved,
        }

        response = self.post(endpoint, data=data, include_org=True)

        if not response.get("success"):
            raise Exception(response.get("error", "Failed to list tickets"))

        return response

    def get_ticket(self, ticket_id: str) -> Dict:
        """
        Get full ticket details.

        Args:
            ticket_id: Ticket ID

        Returns:
            Ticket dictionary with all fields

        Raises:
            NetworkError: If API request fails
        """
        response = self.get(f"/api/v1/tickets/{ticket_id}", include_org=True)

        if not response.get("success"):
            raise Exception(response.get("error", "Failed to fetch ticket"))

        return response.get("ticket", {})

    def cli_batch_fetch(self, ticket_ids: List[str]) -> List[Dict]:
        """
        Fetch multiple tickets using CLI unlimited endpoint - NO 500 LIMIT.

        Args:
            ticket_ids: List of ticket IDs (unlimited)

        Returns:
            List of ticket dictionaries

        Raises:
            NetworkError: If API request fails
        """
        if not ticket_ids:
            return []

        data = {"ticket_ids": ticket_ids}
        response = self.post("/api/v1/cli/tickets/batch", data=data, include_org=True)

        if not response.get("success"):
            raise Exception(response.get("error", "Failed to batch fetch tickets"))

        return response.get("tickets", [])

    def batch_fetch(self, ticket_ids: List[str]) -> List[Dict]:
        """
        Fetch multiple tickets in one request.

        Args:
            ticket_ids: List of ticket IDs

        Returns:
            List of ticket dictionaries

        Raises:
            NetworkError: If API request fails
        """
        if not ticket_ids:
            return []

        data = {"ticket_ids": ticket_ids}
        response = self.post("/api/v1/tickets/batch", data=data, include_org=True)

        if not response.get("success"):
            raise Exception(response.get("error", "Failed to batch fetch tickets"))

        return response.get("tickets", [])

    def sync_all_tickets(self, project_id: str) -> Dict:
        """
        Get ALL tickets for a project using the CLI sync endpoint - NO LIMIT.

        Uses dedicated CLI endpoint that returns all tickets in one call.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with ALL tickets (no pagination)

        Raises:
            NetworkError: If API request fails
        """
        endpoint = f"/api/v1/cli/projects/{project_id}/tickets/sync"

        data = {
            "show_resolved_over_7_days": True,
        }

        response = self.post(endpoint, data=data, include_org=True)

        if not response.get("success"):
            raise Exception(response.get("error", "Failed to sync tickets"))

        return response

    def get_ticket_attachments(self, ticket_id: str) -> Dict:
        """
        Get attachments for a ticket.

        Args:
            ticket_id: Ticket ID

        Returns:
            Dictionary with direct and indirect attachments

        Raises:
            NetworkError: If API request fails
        """
        response = self.get(
            f"/api/v1/attachments/record/ticket/{ticket_id}", include_org=True
        )

        if not response.get("success"):
            raise Exception(response.get("error", "Failed to fetch attachments"))

        return {
            "direct_attachments": response.get("direct_attachments", []),
            "indirect_attachments": response.get("indirect_attachments", []),
        }

    def batch_fetch_attachments(self, ticket_ids: List[str]) -> Dict[str, Dict]:
        """
        Batch fetch attachments for multiple tickets in one request.

        Args:
            ticket_ids: List of ticket IDs

        Returns:
            Dictionary mapping ticket_id to attachments dict

        Raises:
            NetworkError: If API request fails
        """
        if not ticket_ids:
            return {}

        response = self.post(
            "/api/v1/attachments/batch/tickets",
            data={"ticket_ids": ticket_ids},
            include_org=True,
        )

        if not response.get("success"):
            raise Exception(response.get("error", "Failed to batch fetch attachments"))

        return response.get("attachments_by_ticket", {})

    def create_ticket(
        self,
        project_id: str,
        title: str,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        issue_type: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict:
        """
        Create a new ticket.

        Args:
            project_id: Project ID to create ticket in
            title: Ticket title (required)
            description: Ticket description
            status: Status (e.g., "To Do", "In Progress")
            priority: Priority (Low, Medium, High, Critical)
            issue_type: Type (Task, Bug, Story, Epic)
            assignees: List of assignee emails
            labels: List of label strings

        Returns:
            Dictionary with created ticket details including ticket_key

        Raises:
            NetworkError: If API request fails
        """
        payload: Dict = {
            "project_id": project_id,
            "title": title,
        }

        if description:
            payload["description"] = description
        if status:
            payload["status"] = status
        if priority:
            payload["priority"] = priority
        if issue_type:
            payload["issue_type"] = issue_type
        if assignees:
            payload["assignees"] = assignees
        if labels:
            payload["labels"] = labels

        response = self.post("/api/v1/tickets", data=payload, include_org=True)

        if not response.get("success"):
            raise Exception(response.get("error", "Failed to create ticket"))

        return response

    def update_ticket(
        self,
        ticket_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        issue_type: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        due_date: Optional[str] = None,
    ) -> Dict:
        """
        Update an existing ticket.

        Args:
            ticket_id: Ticket ID (UUID) to update
            title: New ticket title
            description: New ticket description
            status: New status (e.g., "To Do", "In Progress", "Done")
            priority: New priority (Low, Medium, High, Critical)
            issue_type: New type (Task, Bug, Story, Epic)
            assignees: New list of assignee emails (replaces existing)
            labels: New list of labels (replaces existing)
            due_date: New due date (ISO format)

        Returns:
            Dictionary with update result

        Raises:
            NetworkError: If API request fails
        """
        payload: Dict = {}

        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        if status is not None:
            payload["status"] = status
        if priority is not None:
            payload["priority"] = priority
        if issue_type is not None:
            payload["issue_type"] = issue_type
        if assignees is not None:
            payload["assignees"] = assignees
        if labels is not None:
            payload["labels"] = labels
        if due_date is not None:
            payload["due_date"] = due_date

        if not payload:
            raise Exception("No fields to update")

        response = self.put(f"/api/v1/tickets/{ticket_id}", data=payload, include_org=True)

        if not response.get("success"):
            raise Exception(response.get("error", "Failed to update ticket"))

        return response
