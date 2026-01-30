"""Server-Sent Events (SSE) watcher for real-time ticket updates."""

import json
import signal
import sys
from typing import Dict, List, Optional, Callable

import httpx

from janet.config.manager import ConfigManager
from janet.markdown.generator import MarkdownGenerator
from janet.sync.file_manager import FileManager
from janet.utils.console import console


class SSEWatcher:
    """Watch for ticket changes via Server-Sent Events."""

    def __init__(
        self,
        config_manager: ConfigManager,
        projects: List[Dict],
        org_name: str,
        sync_dir: str,
        org_members: Optional[List[Dict]] = None,
        on_update: Optional[Callable[[str, str], None]] = None,
        project_statuses: Optional[Dict[str, List[str]]] = None,
    ):
        """
        Initialize SSE watcher.

        Args:
            config_manager: Configuration manager instance
            projects: List of project dictionaries to watch
            org_name: Organization name
            sync_dir: Sync directory path
            org_members: Organization members for name resolution
            on_update: Optional callback when ticket is updated (ticket_key, action)
            project_statuses: Dict mapping project_identifier to list of valid statuses
        """
        self.config_manager = config_manager
        self.config = config_manager.get()
        self.projects = {p["id"]: p for p in projects}
        self.projects_list = projects  # Keep list for README generation
        self.org_name = org_name
        self.sync_dir = sync_dir
        self.file_manager = FileManager(sync_dir)
        self.markdown_generator = MarkdownGenerator()
        self.org_members = org_members
        self.on_update = on_update
        self.project_statuses = project_statuses or {}
        self._running = False

        # Build SSE URL
        self.sse_url = f"{self.config.api.base_url}/api/v1/cli/events"

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for SSE connection."""
        from janet.auth.token_manager import TokenManager

        token_manager = TokenManager(self.config_manager)
        access_token = token_manager.get_access_token()

        return {
            "Authorization": f"Bearer {access_token}",
            "X-Organization-ID": self.config.selected_organization.id,
            "Accept": "text/event-stream",
        }

    def _handle_event(self, event: Dict) -> None:
        """
        Handle incoming SSE event.

        Args:
            event: Event dictionary
        """
        event_type = event.get("type")
        project_id = event.get("projectId")
        ticket_id = event.get("ticketId")
        ticket_data = event.get("ticketData", {})

        # Skip if not for a project we're watching
        if project_id and project_id not in self.projects:
            return

        # Get project info
        project = self.projects.get(project_id, {})
        project_name = project.get("project_name", "Unknown")

        if event_type == "connected":
            project_count = len(self.projects)
            project_names = ", ".join([p.get("project_name", p.get("project_identifier", "")) for p in self.projects.values()][:3])
            if project_count > 3:
                project_names += f" +{project_count - 3} more"
            console.print(f"[green]Watching {project_count} project(s) in {self.org_name}[/green] ({project_names})")
            return

        if event_type in ("ticket-change", "ticket-created"):
            ticket_key = ticket_data.get("ticket_key", "")
            if not ticket_key:
                return

            # Generate markdown and write to file
            try:
                # Extract attachments from event data if present
                attachments = None
                if ticket_data.get("attachments"):
                    attachments = {
                        "direct_attachments": ticket_data.get("attachments", []),
                        "indirect_attachments": []
                    }
                org_id = self.config.selected_organization.id
                markdown = self.markdown_generator.generate(
                    ticket_data, self.org_members, attachments, org_id, project_id
                )
                self.file_manager.write_ticket(
                    org_name=self.org_name,
                    project_name=project_name,
                    ticket_key=ticket_key,
                    content=markdown,
                )

                action = "Created" if event_type == "ticket-created" else "Updated"
                updated_fields = ticket_data.get("updated_fields", [])
                # Transform field names for display (backend uses "labels", CLI uses "tags")
                display_fields = ["tags" if f == "labels" else f for f in updated_fields]
                if display_fields and event_type == "ticket-change":
                    console.print(f"[green]   {ticket_key}[/green] ({', '.join(display_fields)})")
                else:
                    console.print(f"[green]   {ticket_key}[/green] ({action.lower()})")

                if self.on_update:
                    self.on_update(ticket_key, action.lower())

            except Exception as e:
                console.print(f"[red]   Failed to update {ticket_key}: {e}[/red]")

        elif event_type == "ticket-deleted":
            ticket_key = event.get("ticketKey", "")
            if not ticket_key:
                return

            # Delete or archive local file
            try:
                deleted = self.file_manager.delete_ticket(
                    org_name=self.org_name,
                    project_name=project_name,
                    ticket_key=ticket_key,
                )
                if deleted:
                    console.print(f"[yellow]   {ticket_key}[/yellow] (deleted)")
                    if self.on_update:
                        self.on_update(ticket_key, "deleted")

            except Exception as e:
                console.print(f"[red]   Failed to delete {ticket_key}: {e}[/red]")

        elif event_type == "column-change":
            # Update project statuses and regenerate README
            project_identifier = event.get("projectIdentifier", "")
            columns = event.get("columns", [])

            if project_identifier and columns:
                # Extract status values in order
                statuses = [col.get("status_value", "") for col in sorted(columns, key=lambda x: x.get("column_order", 0))]
                self.project_statuses[project_identifier] = statuses

                # Regenerate README with updated statuses
                try:
                    from janet.sync.readme_generator import ReadmeGenerator
                    from pathlib import Path

                    # Calculate total tickets from projects
                    total_tickets = sum(p.get("ticket_count", 0) for p in self.projects_list)

                    readme_gen = ReadmeGenerator()
                    readme_gen.write_readme(
                        sync_dir=Path(self.sync_dir),
                        org_name=self.org_name,
                        projects=self.projects_list,
                        total_tickets=total_tickets,
                        project_statuses=self.project_statuses,
                    )
                    console.print(f"[cyan]   README updated[/cyan] ({project_identifier} statuses changed)")
                except Exception as e:
                    console.print(f"[red]   Failed to update README: {e}[/red]")

    def watch(self) -> None:
        """
        Start watching for events.

        This method blocks until interrupted (Ctrl+C).
        """
        self._running = True

        # Setup signal handler for graceful shutdown
        def signal_handler(sig, frame):
            console.print("\n[yellow]Stopping watch...[/yellow]")
            self._running = False
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        console.print("[cyan]Watching for changes... (Ctrl+C to stop)[/cyan]")
        console.print("[dim]Ticket updates from the platform will sync to your local markdown files in real-time.[/dim]\n")

        while self._running:
            try:
                self._connect_and_stream()
            except httpx.ConnectError as e:
                console.print(f"[red]Connection error: {e}[/red]")
                console.print("[yellow]Reconnecting in 5 seconds...[/yellow]")
                import time
                time.sleep(5)
            except Exception as e:
                error_str = str(e)
                # Check if this is an auth error that requires re-login
                if "401" in error_str or "Unauthorized" in error_str:
                    console.print("[red]Authentication failed. Attempting to refresh token...[/red]")
                    try:
                        from janet.auth.token_manager import TokenManager
                        token_manager = TokenManager(self.config_manager)
                        token_manager.refresh_access_token()
                        console.print("[green]Token refreshed successfully.[/green]")
                    except Exception as refresh_error:
                        console.print(f"[red]Token refresh failed: {refresh_error}[/red]")
                        console.print("[yellow]Please run 'janet login' to re-authenticate.[/yellow]")
                        self._running = False
                        break
                # Expected disconnection from load balancer timeout - reconnect silently
                elif "incomplete chunked read" in error_str or "closed" in error_str.lower():
                    console.print("[dim]Connection closed, reconnecting...[/dim]")
                else:
                    console.print(f"[yellow]Connection interrupted: {e}[/yellow]")
                import time
                time.sleep(2)  # Shorter delay for expected disconnections

    def _connect_and_stream(self) -> None:
        """Connect to SSE endpoint and process stream."""
        headers = self._get_headers()

        with httpx.Client(timeout=None) as client:
            with client.stream("GET", self.sse_url, headers=headers) as response:
                if response.status_code == 401:
                    raise Exception("401 Unauthorized - token may have expired")
                if response.status_code != 200:
                    raise Exception(f"SSE connection failed: {response.status_code}")

                for line in response.iter_lines():
                    if not self._running:
                        break

                    if not line:
                        continue

                    # SSE format: "data: {...json...}"
                    if line.startswith("data: "):
                        try:
                            event_data = json.loads(line[6:])
                            self._handle_event(event_data)
                        except json.JSONDecodeError:
                            pass  # Ignore malformed events

                    # Ignore comments (keepalive pings)
                    elif line.startswith(":"):
                        pass
