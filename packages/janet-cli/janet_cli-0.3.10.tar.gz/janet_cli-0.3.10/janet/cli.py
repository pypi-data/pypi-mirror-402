"""Main CLI application using Typer."""

import sys
import json
import typer
from typing import Optional, List
from typing_extensions import Annotated

from janet import __version__
from janet.config.manager import ConfigManager
from janet.utils.console import console, print_success, print_error, print_info
from janet.utils.errors import JanetCLIError

# Initialize Typer app
app = typer.Typer(
    name="janet",
    help="Janet AI CLI - Sync tickets to local markdown files",
    add_completion=False,
)

# Sub-commands
auth_app = typer.Typer(help="Authentication commands")
org_app = typer.Typer(help="Organization management")
project_app = typer.Typer(help="Project management")
config_app = typer.Typer(help="Configuration management")
ticket_app = typer.Typer(help="Ticket management")

app.add_typer(auth_app, name="auth", rich_help_panel="Management")
app.add_typer(org_app, name="org", rich_help_panel="Management")
app.add_typer(project_app, name="project", rich_help_panel="Management")
app.add_typer(config_app, name="config", rich_help_panel="Management")
app.add_typer(ticket_app, name="ticket", rich_help_panel="Management")

# Initialize config manager
config_manager = ConfigManager()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"Janet CLI v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool, typer.Option("--version", "-v", callback=version_callback, is_eager=True)
    ] = False,
) -> None:
    """Janet AI CLI - Sync tickets to local markdown files."""
    pass


# =============================================================================
# Authentication Commands
# =============================================================================


@app.command(name="login", rich_help_panel="Authentication")
def login() -> None:
    """Authenticate with Janet AI and select organization."""
    try:
        from janet.auth.oauth_flow import OAuthFlow
        from janet.api.organizations import OrganizationAPI
        from InquirerPy import inquirer

        print_info("Starting authentication flow...")

        # Start OAuth flow
        oauth_flow = OAuthFlow(config_manager)
        oauth_flow.start_login()

        # Fetch available organizations
        print_info("Fetching your organizations...")
        org_api = OrganizationAPI(config_manager)
        organizations = org_api.list_organizations()

        if not organizations:
            print_error("No organizations found for your account")
            raise typer.Exit(1)

        # Select organization
        if len(organizations) == 1:
            # Auto-select if only one org
            selected_org = organizations[0]
            print_success(f"Auto-selected organization: {selected_org['name']}")
        else:
            # Show interactive selection
            console.print("\n[bold]Select an organization:[/bold]\n")

            org_choices = []
            for org in organizations:
                role = org.get("userRole", "member")
                label = f"{org['name']} ({role})"
                org_choices.append({"name": label, "value": org})

            selected_org = inquirer.select(
                message="Select organization:",
                choices=org_choices,
            ).execute()

        # Save selected organization
        from janet.config.models import OrganizationInfo

        config = config_manager.get()
        config.selected_organization = OrganizationInfo(
            id=selected_org["id"], name=selected_org["name"], uuid=selected_org["uuid"]
        )
        config_manager.update(config)

        print_success(f"Selected organization: {selected_org['name']}")
        console.print("\n[green]✓ Authentication complete![/green]")
        console.print("Run [cyan]janet sync[/cyan] to sync tickets and watch for real-time updates.")

    except JanetCLIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command(name="update", rich_help_panel="Utilities")
def update(
    test_pypi: bool = typer.Option(False, "--test", help="Update from Test PyPI (for development)")
) -> None:
    """Update Janet CLI to the latest version."""
    import subprocess
    import httpx
    from janet import __version__

    console.print("[cyan]Checking for updates...[/cyan]")

    try:
        # Determine PyPI URL based on flag
        if test_pypi:
            pypi_url = "https://test.pypi.org/pypi/janet-cli/json"
            index_url = "https://test.pypi.org/simple/"
        else:
            pypi_url = "https://pypi.org/pypi/janet-cli/json"
            index_url = None

        # Fetch latest version from PyPI
        try:
            response = httpx.get(pypi_url, timeout=10)
            response.raise_for_status()
            latest_version = response.json()["info"]["version"]
        except Exception as e:
            print_error(f"Failed to check for updates: {e}")
            raise typer.Exit(1)

        current_version = __version__

        console.print(f"[dim]Current version: {current_version}[/dim]")
        console.print(f"[dim]Latest version:  {latest_version}[/dim]")

        # Compare versions
        if current_version == latest_version:
            console.print("[green]Janet CLI is already up to date.[/green]")
            return

        # Build pip command
        pip_cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "janet-cli"]
        if index_url:
            pip_cmd.extend(["--index-url", index_url])

        console.print(f"[cyan]Updating to version {latest_version}...[/cyan]")

        result = subprocess.run(pip_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            console.print(f"[green]✓ Janet CLI updated to {latest_version}![/green]")
            console.print("[dim]Restart your terminal to use the new version.[/dim]")
        else:
            print_error(f"Update failed: {result.stderr}")
            raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        print_error(f"Update failed: {e}")
        raise typer.Exit(1)


@app.command(name="logout", rich_help_panel="Authentication")
def logout() -> None:
    """Clear stored credentials."""
    try:
        config = config_manager.get()
        if not config_manager.is_authenticated():
            print_info("Not currently logged in")
            return

        # Clear authentication data
        config.auth.access_token = None
        config.auth.refresh_token = None
        config.auth.expires_at = None
        config.auth.user_id = None
        config.auth.user_email = None
        config.selected_organization = None

        config_manager.update(config)
        print_success("Logged out successfully")
    except JanetCLIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@auth_app.command(name="status")
def auth_status() -> None:
    """Show current authentication status."""
    try:
        config = config_manager.get()

        if not config_manager.is_authenticated():
            console.print("[yellow]Not authenticated[/yellow]")
            console.print("Run 'janet login' to authenticate")
            return

        console.print("[bold green]Authenticated[/bold green]")
        if config.auth.user_email:
            console.print(f"User: [cyan]{config.auth.user_email}[/cyan]")
        if config.selected_organization:
            console.print(f"Organization: [cyan]{config.selected_organization.name}[/cyan]")
            console.print(f"Organization ID: [dim]{config.selected_organization.id}[/dim]")

        if config.auth.expires_at:
            console.print(f"Token expires: [dim]{config.auth.expires_at}[/dim]")
    except JanetCLIError as e:
        print_error(str(e))
        raise typer.Exit(1)


# =============================================================================
# Organization Commands
# =============================================================================


@org_app.command(name="list")
def org_list() -> None:
    """List available organizations."""
    try:
        from janet.api.organizations import OrganizationAPI
        from rich.table import Table

        if not config_manager.is_authenticated():
            print_error("Not authenticated. Run 'janet login' first.")
            raise typer.Exit(1)

        print_info("Fetching organizations...")
        org_api = OrganizationAPI(config_manager)
        organizations = org_api.list_organizations()

        if not organizations:
            print_info("No organizations found")
            return

        # Display as table
        table = Table(title="Organizations", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold")
        table.add_column("Role")

        for org in organizations:
            table.add_row(
                org.get("id", ""), org.get("name", ""), org.get("userRole", "member")
            )

        console.print(table)
    except JanetCLIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@org_app.command(name="select")
def org_select(org_id: str) -> None:
    """
    Switch active organization.

    Args:
        org_id: Organization ID to select
    """
    try:
        from janet.api.organizations import OrganizationAPI
        from janet.config.models import OrganizationInfo

        if not config_manager.is_authenticated():
            print_error("Not authenticated. Run 'janet login' first.")
            raise typer.Exit(1)

        print_info(f"Selecting organization: {org_id}")
        org_api = OrganizationAPI(config_manager)

        # Fetch organization details
        org_data = org_api.get_organization(org_id)

        # Update config
        config = config_manager.get()
        old_org_id = config.selected_organization.id if config.selected_organization else None

        config.selected_organization = OrganizationInfo(
            id=org_data["id"], name=org_data["name"], uuid=org_data.get("uuid", org_id)
        )

        # Clear synced projects when switching orgs (they belong to the old org)
        if old_org_id and old_org_id != org_data["id"]:
            config.sync.synced_projects = []
            config.sync.last_sync_org_id = None
            config.sync.last_sync_total_tickets = 0

            # Regenerate README with new org but empty projects (no statuses until sync)
            from janet.utils.paths import expand_path
            from pathlib import Path

            sync_dir = expand_path(config.sync.root_directory)
            if sync_dir.exists():
                from janet.sync.readme_generator import ReadmeGenerator
                readme_gen = ReadmeGenerator()
                readme_gen.write_readme(
                    sync_dir=sync_dir,
                    org_name=org_data["name"],
                    projects=[],
                    total_tickets=0,
                    project_statuses={},
                )
                print_info(f"README updated for new organization. Run 'janet sync' to sync projects.")

        config_manager.update(config)

        print_success(f"Selected organization: {org_data['name']}")
    except JanetCLIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@org_app.command(name="current")
def org_current() -> None:
    """Show current organization."""
    try:
        config = config_manager.get()

        if not config_manager.has_organization():
            print_info("No organization selected")
            console.print("Run 'janet org list' to see available organizations")
            return

        org = config.selected_organization
        console.print(f"[bold]Current Organization:[/bold]")
        console.print(f"  Name: [cyan]{org.name}[/cyan]")
        console.print(f"  ID: [dim]{org.id}[/dim]")
        console.print(f"  UUID: [dim]{org.uuid}[/dim]")
    except JanetCLIError as e:
        print_error(str(e))
        raise typer.Exit(1)


# =============================================================================
# Project Commands
# =============================================================================


@project_app.command(name="list")
def project_list() -> None:
    """List projects in current organization."""
    try:
        from janet.api.projects import ProjectAPI
        from rich.table import Table

        if not config_manager.is_authenticated():
            print_error("Not authenticated. Run 'janet login' first.")
            raise typer.Exit(1)

        if not config_manager.has_organization():
            print_error("No organization selected. Run 'janet org select' first.")
            raise typer.Exit(1)

        print_info("Fetching projects...")
        project_api = ProjectAPI(config_manager)
        projects = project_api.list_projects()

        if not projects:
            print_info("No projects found")
            return

        # Display as table
        table = Table(title="Projects", show_header=True, header_style="bold cyan")
        table.add_column("Key", style="bold")
        table.add_column("Name")
        table.add_column("Tickets", justify="right")
        table.add_column("Role")

        for project in projects:
            table.add_row(
                project.get("project_identifier", ""),
                project.get("project_name", ""),
                str(project.get("ticket_count", 0)),
                project.get("user_role", ""),
            )

        console.print(table)
    except JanetCLIError as e:
        print_error(str(e))
        raise typer.Exit(1)


# =============================================================================
# Sync Commands
# =============================================================================


@app.command(name="sync", rich_help_panel="Syncing")
def sync(
    directory: Annotated[str, typer.Option("--dir", "-d", help="Sync directory")] = None,
    all_projects: Annotated[bool, typer.Option("--all", help="Sync all projects")] = False,
    no_watch: Annotated[bool, typer.Option("--no-watch", help="Exit after sync instead of watching for updates")] = False,
) -> None:
    """
    Sync tickets to local markdown files and watch for real-time updates.

    Interactive mode: prompts for project selection and directory.
    After syncing, stays connected for real-time updates (Ctrl+C to stop).
    """
    try:
        from janet.sync.sync_engine import SyncEngine
        from janet.api.projects import ProjectAPI
        import os

        if not config_manager.is_authenticated():
            print_error("Not authenticated. Run 'janet login' first.")
            raise typer.Exit(1)

        if not config_manager.has_organization():
            print_error("No organization selected. Run 'janet org select' first.")
            raise typer.Exit(1)

        org_name = config_manager.get().selected_organization.name

        # Step 1: Select projects to sync
        console.print(f"\n[bold]Sync tickets for {org_name}[/bold]\n")

        # Fetch projects
        print_info("Fetching projects...")
        project_api = ProjectAPI(config_manager)
        all_project_list = project_api.list_projects()

        if not all_project_list:
            print_error("No projects found")
            raise typer.Exit(1)

        # Filter out projects with no tickets
        available_projects = [p for p in all_project_list if p.get("ticket_count", 0) > 0]

        if not available_projects:
            print_info("No projects with tickets found")
            return

        # Show project selection
        selected_projects = []

        if all_projects:
            # Skip selection, use all projects
            selected_projects = available_projects
            console.print(f"Syncing all {len(selected_projects)} projects")
        else:
            # Interactive project selection with checkboxes
            from InquirerPy import inquirer

            console.print("\n[bold]Select projects to sync:[/bold]")
            console.print("[dim]Use ↑/↓ to move, SPACE to toggle selection, ENTER to confirm[/dim]\n")

            # Build choices with formatted display
            choices = []
            for project in available_projects:
                key = project.get("project_identifier", "")
                name = project.get("project_name", "")
                count = project.get("ticket_count", 0)
                label = f"{key:8s} - {name:30s} ({count} tickets)"
                choices.append({"name": label, "value": project, "enabled": True})

            # Show checkbox multi-select
            import sys
            import os as os_module

            # Temporarily suppress InquirerPy's result output
            selected = inquirer.checkbox(
                message="Select projects:",
                choices=choices,
                validate=lambda result: len(result) > 0 or "Please select at least one project",
                instruction="(SPACE to toggle, ENTER to confirm)",
                amark="✓",
                transformer=lambda result: "",  # Suppress the result display
            ).execute()

            if not selected:
                print_info("No projects selected")
                return

            selected_projects = selected

        # Show selected projects cleanly
        console.print(f"\n[green]✓ Selected {len(selected_projects)} project(s):[/green]")
        for proj in selected_projects:
            key = proj.get("project_identifier", "")
            name = proj.get("project_name", "")
            count = proj.get("ticket_count", 0)
            console.print(f"  • {key} - {name} ({count} tickets)")

        # Step 2: Select sync directory
        if directory:
            sync_dir = directory
        else:
            # Get current directory
            current_dir = os.getcwd()
            from InquirerPy import inquirer

            console.print(f"\n[bold]Where should tickets be synced?[/bold]")
            console.print(f"[dim]Current directory: {current_dir}[/dim]\n")

            # Build directory choices
            dir_choices = [
                {
                    "name": f"Current directory ({current_dir}/janet-tickets)",
                    "value": os.path.join(current_dir, "janet-tickets"),
                },
                {
                    "name": "Home directory (~/janet-tickets)",
                    "value": "~/janet-tickets",
                },
                {
                    "name": "Custom path...",
                    "value": "__custom__",
                },
            ]

            choice = inquirer.select(
                message="Select sync location:",
                choices=dir_choices,
            ).execute()

            if choice == "__custom__":
                sync_dir = inquirer.filepath(
                    message="Enter custom path:",
                    default=current_dir,
                    validate=lambda x: len(x) > 0 or "Path cannot be empty",
                ).execute()
                if not sync_dir:
                    print_info("Sync cancelled")
                    return
            else:
                sync_dir = choice

        # Expand path
        from janet.utils.paths import expand_path
        expanded_dir = expand_path(sync_dir)

        console.print(f"\n[green]✓ Sync directory: {expanded_dir}[/green]")

        # Confirm
        from InquirerPy import inquirer
        confirmed = inquirer.confirm(
            message=f"Sync {len(selected_projects)} project(s) to {expanded_dir}?",
            default=True,
        ).execute()

        if not confirmed:
            print_info("Sync cancelled")
            return

        # Step 3: Start sync
        console.print(f"\n[bold]Starting sync...[/bold]\n")

        # Update config with new directory
        config = config_manager.get()
        config.sync.root_directory = str(expanded_dir)
        config_manager.update(config)

        # Initialize sync engine with new directory
        sync_engine = SyncEngine(config_manager)

        # Sync selected projects
        total_tickets = 0
        for project in selected_projects:
            project_key = project.get("project_identifier", "")
            project_name = project.get("project_name", "")

            synced = sync_engine.sync_project(project["id"], project_key, project_name)
            total_tickets += synced

        # Fetch project statuses (kanban columns) for each project
        project_statuses = {}
        try:
            for project in selected_projects:
                project_id = project.get("id", "")
                project_key = project.get("project_identifier", "")
                if project_id:
                    columns = project_api.get_project_columns(project_id)
                    # Extract status values in order
                    statuses = [col.get("status_value", "") for col in sorted(columns, key=lambda x: x.get("column_order", 0))]
                    project_statuses[project_key] = statuses
        except Exception as e:
            print_info(f"Note: Could not fetch project statuses: {e}")

        # Generate README for AI agents
        from janet.sync.readme_generator import ReadmeGenerator
        readme_gen = ReadmeGenerator()
        readme_path = readme_gen.write_readme(
            sync_dir=expanded_dir,
            org_name=org_name,
            projects=selected_projects,
            total_tickets=total_tickets,
            project_statuses=project_statuses,
        )

        # Save synced projects to config for README regeneration on org change
        from janet.config.models import SyncedProject
        config.sync.synced_projects = [
            SyncedProject(
                id=p.get("id", ""),
                project_identifier=p.get("project_identifier", ""),
                project_name=p.get("project_name", ""),
                ticket_count=p.get("ticket_count", 0),
            )
            for p in selected_projects
        ]
        config.sync.last_sync_org_id = config.selected_organization.id
        config.sync.last_sync_total_tickets = total_tickets
        config_manager.update(config)

        # Show summary
        console.print(f"\n[bold green]✓ Sync complete![/bold green]")
        console.print(f"  Projects: {len(selected_projects)}")
        console.print(f"  Tickets: {total_tickets}")
        console.print(f"\n[cyan]Tickets saved to: {expanded_dir}[/cyan]")
        console.print(f"[dim]README for AI agents: {readme_path}[/dim]")

        # Start watch mode (default behavior, unless --no-watch)
        if not no_watch:
            from janet.sync.sse_watcher import SSEWatcher
            from janet.api.organizations import OrganizationAPI

            console.print(f"\n")

            # Fetch org members for name resolution in SSE updates
            org_members = None
            try:
                org_api = OrganizationAPI(config_manager)
                org_id = config.selected_organization.id
                response = org_api.get(f"/api/v1/organizations/{org_id}/members", include_org=False)
                org_members = response.get("members", [])
            except Exception:
                pass  # Will fall back to emails if members can't be fetched

            # Create SSE watcher
            watcher = SSEWatcher(
                config_manager=config_manager,
                projects=selected_projects,
                org_name=org_name,
                sync_dir=str(expanded_dir),
                org_members=org_members,
                project_statuses=project_statuses,
            )

            # This blocks until Ctrl+C
            watcher.watch()

    except JanetCLIError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Sync failed: {e}")
        raise typer.Exit(1)


# =============================================================================
# Status Command
# =============================================================================


@app.command(name="status", rich_help_panel="Syncing")
def status() -> None:
    """Show overall status (auth, org, last sync)."""
    try:
        config = config_manager.get()

        console.print("[bold]Janet CLI Status[/bold]\n")

        # Authentication status
        if config_manager.is_authenticated():
            console.print("✓ [green]Authenticated[/green]")
            if config.auth.user_email:
                console.print(f"  User: {config.auth.user_email}")
        else:
            console.print("✗ [yellow]Not authenticated[/yellow]")
            console.print("  Run 'janet login' to authenticate\n")
            return

        # Organization status
        if config_manager.has_organization():
            console.print(f"✓ [green]Organization selected: {config.selected_organization.name}[/green]")
        else:
            console.print("✗ [yellow]No organization selected[/yellow]")
            console.print("  Run 'janet org list' to select an organization\n")
            return

        # Sync status
        console.print(f"\n[bold]Sync Directory:[/bold] {config.sync.root_directory}")
        if config.sync.last_sync_times:
            console.print(f"[bold]Last Synced Projects:[/bold] {len(config.sync.last_sync_times)}")
        else:
            console.print("[dim]No projects synced yet[/dim]")
    except JanetCLIError as e:
        print_error(str(e))
        raise typer.Exit(1)


# =============================================================================
# Config Commands
# =============================================================================


@config_app.command(name="show")
def config_show() -> None:
    """Display current configuration."""
    try:
        config = config_manager.get()
        console.print_json(config.model_dump_json(indent=2))
    except JanetCLIError as e:
        print_error(str(e))
        raise typer.Exit(1)


@config_app.command(name="path")
def config_path() -> None:
    """Show config file location."""
    console.print(f"Config file: [cyan]{config_manager.config_path}[/cyan]")


@config_app.command(name="reset")
def config_reset(
    confirm: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
) -> None:
    """Reset configuration to defaults."""
    try:
        if not confirm:
            console.print("[yellow]This will reset all configuration to defaults.[/yellow]")
            confirmed = typer.confirm("Are you sure?")
            if not confirmed:
                print_info("Reset cancelled")
                return

        config_manager.reset()
        print_success("Configuration reset to defaults")
    except JanetCLIError as e:
        print_error(str(e))
        raise typer.Exit(1)


# =============================================================================
# Ticket Commands
# =============================================================================


@ticket_app.command(name="create")
def ticket_create(
    title: Annotated[str, typer.Argument(help="Ticket title")],
    project: Annotated[Optional[str], typer.Option("--project", "-p", help="Project key (e.g., PROJ) or ID")] = None,
    description: Annotated[Optional[str], typer.Option("--description", "-d", help="Ticket description")] = None,
    status: Annotated[Optional[str], typer.Option("--status", "-s", help="Status (default: To Do)")] = None,
    priority: Annotated[Optional[str], typer.Option("--priority", help="Priority: Low, Medium, High, Critical")] = None,
    issue_type: Annotated[Optional[str], typer.Option("--type", "-t", help="Type: Task, Bug, Story, Epic")] = None,
    assignee: Annotated[Optional[List[str]], typer.Option("--assignee", "-a", help="Assignee email (can repeat)")] = None,
    tag: Annotated[Optional[List[str]], typer.Option("--tag", help="Tag (can repeat)")] = None,
    output_json: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """
    Create a new ticket.

    Examples:
        janet ticket create "Fix login bug" -p PROJ
        janet ticket create "Add feature" -p PROJ -d "Details here" --priority High
        echo "Description" | janet ticket create "Title" -p PROJ
    """
    try:
        from janet.api.tickets import TicketAPI
        from janet.api.projects import ProjectAPI

        if not config_manager.is_authenticated():
            print_error("Not authenticated. Run 'janet login' first.")
            raise typer.Exit(1)

        if not config_manager.has_organization():
            print_error("No organization selected. Run 'janet org select' first.")
            raise typer.Exit(1)

        # Get project list
        project_api = ProjectAPI(config_manager)
        projects = project_api.list_projects()

        if not projects:
            print_error("No projects found in organization")
            raise typer.Exit(1)

        # Resolve project
        project_id = None
        project_key = None

        if project:
            # Try to match by key or ID
            for p in projects:
                if p.get("project_identifier", "").upper() == project.upper():
                    project_id = p["id"]
                    project_key = p["project_identifier"]
                    break
                if p.get("id") == project:
                    project_id = p["id"]
                    project_key = p.get("project_identifier", "")
                    break

            if not project_id:
                print_error(f"Project '{project}' not found")
                raise typer.Exit(1)
        else:
            # Interactive project selection
            if not sys.stdin.isatty():
                print_error("--project is required for non-interactive use")
                raise typer.Exit(1)

            from InquirerPy import inquirer

            console.print("\n[bold]Select a project:[/bold]\n")

            choices = []
            for p in projects:
                key = p.get("project_identifier", "")
                name = p.get("project_name", "")
                count = p.get("ticket_count", 0)
                label_text = f"{key:8s} - {name} ({count} tickets)"
                choices.append({"name": label_text, "value": p})

            selected = inquirer.select(
                message="Project:",
                choices=choices,
            ).execute()

            project_id = selected["id"]
            project_key = selected.get("project_identifier", "")

        # Check for piped stdin for description
        final_description = description
        if not sys.stdin.isatty() and not description:
            # Read from stdin
            stdin_content = sys.stdin.read().strip()
            if stdin_content:
                final_description = stdin_content

        # Create ticket
        ticket_api = TicketAPI(config_manager)
        result = ticket_api.create_ticket(
            project_id=project_id,
            title=title,
            description=final_description,
            status=status or "To Do",
            priority=priority,
            issue_type=issue_type,
            assignees=assignee,
            labels=tag,
        )

        ticket_key_result = result.get("ticket_key", f"{project_key}-{result.get('ticket_identifier', '?')}")

        if output_json:
            output = {
                "success": True,
                "ticket_id": result.get("ticket_id"),
                "ticket_key": ticket_key_result,
                "title": title,
                "project_key": project_key,
            }
            console.print(json.dumps(output, indent=2))
        else:
            print_success(f"Created {ticket_key_result}: {title}")

    except JanetCLIError as e:
        if output_json:
            console.print(json.dumps({"success": False, "error": str(e)}))
        else:
            print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        if output_json:
            console.print(json.dumps({"success": False, "error": str(e)}))
        else:
            print_error(f"Failed to create ticket: {e}")
        raise typer.Exit(1)


@ticket_app.command(name="update")
def ticket_update(
    ticket_key: Annotated[str, typer.Argument(help="Ticket key (e.g., PROJ-123) or ticket ID")],
    title: Annotated[Optional[str], typer.Option("--title", help="New title")] = None,
    description: Annotated[Optional[str], typer.Option("--description", "-d", help="New description")] = None,
    status: Annotated[Optional[str], typer.Option("--status", "-s", help="New status")] = None,
    priority: Annotated[Optional[str], typer.Option("--priority", help="New priority: Low, Medium, High, Critical")] = None,
    issue_type: Annotated[Optional[str], typer.Option("--type", "-t", help="New type: Task, Bug, Story, Epic")] = None,
    assignee: Annotated[Optional[List[str]], typer.Option("--assignee", "-a", help="New assignee email (can repeat, replaces all)")] = None,
    tag: Annotated[Optional[List[str]], typer.Option("--tag", help="New tag (can repeat, replaces all)")] = None,
    due_date: Annotated[Optional[str], typer.Option("--due-date", help="New due date (YYYY-MM-DD)")] = None,
    output_json: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """
    Update an existing ticket.

    Examples:
        janet ticket update PROJ-123 --status "In Progress"
        janet ticket update PROJ-123 --title "New title" --priority High
        janet ticket update PROJ-123 -a user@example.com -a user2@example.com
    """
    try:
        from janet.api.tickets import TicketAPI
        from janet.api.projects import ProjectAPI

        if not config_manager.is_authenticated():
            print_error("Not authenticated. Run 'janet login' first.")
            raise typer.Exit(1)

        if not config_manager.has_organization():
            print_error("No organization selected. Run 'janet org select' first.")
            raise typer.Exit(1)

        # Resolve ticket_key to ticket_id
        ticket_id = None
        resolved_ticket_key = ticket_key

        # Check if it looks like a UUID (ticket ID)
        if "-" in ticket_key and len(ticket_key) == 36:
            ticket_id = ticket_key
        else:
            # It's a ticket key like PROJ-123, need to find the ticket ID
            # Parse project key and ticket number
            parts = ticket_key.upper().rsplit("-", 1)
            if len(parts) != 2:
                print_error(f"Invalid ticket key format: {ticket_key}. Expected format: PROJ-123")
                raise typer.Exit(1)

            project_key, ticket_num = parts

            # Get project list to find the project
            project_api = ProjectAPI(config_manager)
            projects = project_api.list_projects()

            project_id = None
            for p in projects:
                if p.get("project_identifier", "").upper() == project_key:
                    project_id = p["id"]
                    break

            if not project_id:
                print_error(f"Project '{project_key}' not found")
                raise typer.Exit(1)

            # Fetch tickets from project to find the one with matching identifier
            ticket_api = TicketAPI(config_manager)
            sync_result = ticket_api.sync_all_tickets(project_id)
            tickets = sync_result.get("tickets", [])

            for t in tickets:
                if str(t.get("ticket_identifier")) == ticket_num:
                    ticket_id = t["id"]
                    break

            if not ticket_id:
                print_error(f"Ticket '{ticket_key}' not found")
                raise typer.Exit(1)

        # Check if any update field was provided
        if not any([title, description, status, priority, issue_type, assignee, tag, due_date]):
            print_error("No update fields provided. Use --help to see available options.")
            raise typer.Exit(1)

        # Update ticket
        ticket_api = TicketAPI(config_manager)
        result = ticket_api.update_ticket(
            ticket_id=ticket_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            issue_type=issue_type,
            assignees=assignee,
            labels=tag,
            due_date=due_date,
        )

        if output_json:
            output = {
                "success": True,
                "ticket_key": resolved_ticket_key,
                "ticket_id": ticket_id,
                "updated_fields": result.get("updated_fields", []),
            }
            console.print(json.dumps(output, indent=2))
        else:
            updated = result.get("updated_fields", [])
            if updated:
                print_success(f"Updated {resolved_ticket_key}: {', '.join(updated)}")
            else:
                print_success(f"Updated {resolved_ticket_key}")

    except JanetCLIError as e:
        if output_json:
            console.print(json.dumps({"success": False, "error": str(e)}))
        else:
            print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        if output_json:
            console.print(json.dumps({"success": False, "error": str(e)}))
        else:
            print_error(f"Failed to update ticket: {e}")
        raise typer.Exit(1)


# =============================================================================
# Context Command (for AI agents)
# =============================================================================


@app.command(name="context", rich_help_panel="Syncing")
def context(
    output_json: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """
    Show current context (org, projects) for AI agents.

    Use --json for machine-readable output.
    """
    try:
        from janet.api.projects import ProjectAPI

        config = config_manager.get()

        context_data = {
            "authenticated": config_manager.is_authenticated(),
            "user_email": config.auth.user_email if config.auth else None,
            "organization": None,
            "projects": [],
        }

        if config_manager.is_authenticated() and config.selected_organization:
            context_data["organization"] = {
                "id": config.selected_organization.id,
                "name": config.selected_organization.name,
                "uuid": config.selected_organization.uuid,
            }

            # Fetch projects
            if config_manager.has_organization():
                try:
                    project_api = ProjectAPI(config_manager)
                    projects = project_api.list_projects()
                    context_data["projects"] = [
                        {
                            "id": p.get("id"),
                            "key": p.get("project_identifier"),
                            "name": p.get("project_name"),
                            "ticket_count": p.get("ticket_count", 0),
                        }
                        for p in projects
                    ]
                except Exception:
                    pass  # Projects fetch failed, leave empty

        if output_json:
            console.print(json.dumps(context_data, indent=2))
        else:
            console.print("[bold]Janet CLI Context[/bold]\n")

            if not context_data["authenticated"]:
                console.print("[yellow]Not authenticated[/yellow]")
                console.print("Run 'janet login' to authenticate")
                return

            console.print(f"[green]✓ Authenticated[/green] as {context_data['user_email']}")

            if context_data["organization"]:
                console.print(f"[green]✓ Organization:[/green] {context_data['organization']['name']}")
            else:
                console.print("[yellow]No organization selected[/yellow]")
                return

            if context_data["projects"]:
                console.print(f"\n[bold]Projects ({len(context_data['projects'])}):[/bold]")
                for p in context_data["projects"]:
                    console.print(f"  • {p['key']:8s} - {p['name']} ({p['ticket_count']} tickets)")
            else:
                console.print("\n[dim]No projects found[/dim]")

    except JanetCLIError as e:
        if output_json:
            console.print(json.dumps({"authenticated": False, "error": str(e)}))
        else:
            print_error(str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
