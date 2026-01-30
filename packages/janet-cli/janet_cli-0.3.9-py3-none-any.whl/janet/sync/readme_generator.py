"""Generate README for synced ticket directory."""

from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


class ReadmeGenerator:
    """Generate README.md for synced ticket directory."""

    def generate(
        self,
        org_name: str,
        projects: List[Dict],
        total_tickets: int,
        sync_time: datetime,
        project_statuses: Optional[Dict[str, List[str]]] = None,
    ) -> str:
        """
        Generate README content for ticket directory.
        Written as instructions FOR the AI coding agent.

        Args:
            org_name: Organization name
            projects: List of synced projects
            total_tickets: Total number of tickets synced
            sync_time: Timestamp of sync
            project_statuses: Dict mapping project_identifier to list of valid statuses

        Returns:
            README markdown content
        """
        sections = []

        # Header - addressing the AI agent directly
        sections.append(f"# Instructions for AI Coding Agents - {org_name}\n")
        sections.append(
            "This directory contains project management tickets from Janet AI. "
            "Use these tickets to understand requirements, track work, and stay aligned with project goals.\n"
        )

        # Context for the AI
        sections.append("## Context\n")
        sections.append(f"- **Organization:** {org_name}")
        sections.append(f"- **Projects:** {len(projects)}")
        sections.append(f"- **Total Tickets:** {total_tickets}")
        sections.append(
            f"- **Last Synced:** {sync_time.strftime('%B %d, %Y at %I:%M %p')}\n"
        )

        # Projects list with statuses
        if projects:
            sections.append("## Projects\n")
            for project in projects:
                key = project.get("project_identifier", "")
                name = project.get("project_name", "")
                count = project.get("ticket_count", 0)
                sections.append(f"### {key} - {name}\n")
                sections.append(f"- **Tickets:** {count}")

                # Show valid statuses for this project
                if project_statuses and key in project_statuses:
                    statuses = project_statuses[key]
                    if statuses:
                        sections.append(f"- **Valid Statuses:** {', '.join(statuses)}")
                sections.append("")

        # Ticket format explanation
        sections.append("## Ticket Format\n")
        sections.append("Each `.md` file represents a ticket with:")
        sections.append("- **Title** - Ticket key and summary (e.g., `PROJ-123: Add login feature`)")
        sections.append("- **Metadata** - Status, priority, type, assignees, dates, sprint, story points, labels")
        sections.append("- **Description** - Full requirements and details")
        sections.append("- **Comments** - Discussion and updates")
        sections.append("- **Attachments** - Files attached to the ticket with type, size, and AI-generated descriptions")
        sections.append("- **Child Tasks** - Sub-tasks if applicable\n")

        # Instructions for the AI
        sections.append("## How to Use These Tickets\n")
        sections.append("When working on this codebase:")
        sections.append("1. **Reference tickets** - Read relevant tickets before implementing features")
        sections.append("2. **Check status** - Verify ticket status before starting work")
        sections.append("3. **Follow requirements** - Use ticket descriptions as specifications")
        sections.append("4. **Note priorities** - High/Critical tickets should be addressed first\n")

        # Important notes for AI agents
        sections.append("## ⚠️ IMPORTANT: Creating Tickets (Required Fields)\n")
        sections.append("### Required Fields for Ticket Creation\n")
        sections.append("**Every** ticket creation command **MUST** include:\n")
        sections.append("1. **Title** - The ticket title (first positional argument)")
        sections.append("2. **Project** - The project key using `--project` or `-p`")
        sections.append("3. **Status** - A valid status using `--status` or `-s`\n")

        sections.append("### Status Values Are Custom Per Project\n")
        sections.append("Each project has custom status values (see \"Valid Statuses\" in Projects section above).\n")
        sections.append("⚠️ **REQUIRED:** Always use a valid status from the project's \"Valid Statuses\" list.")
        sections.append("⚠️ **If user doesn't specify a status:** Ask which status to use before running the command.")
        sections.append("⚠️ **Never assume or guess status values** - they vary by project (e.g., \"To Do\" vs \"Backlog\" vs \"Open\").\n")

        sections.append("### Example Workflow\n")
        sections.append('**User prompt:** "Create a bug ticket in BACK for the login issue"\n')
        sections.append("**Your response:** \"Which status should I use for the new ticket? Valid options for BACK are: To Do, In Progress, In Review, Done\"\n")
        sections.append('**After user responds:** Run the command with the specified status:')
        sections.append("```bash")
        sections.append('janet ticket create "Fix login issue" -p BACK --status "To Do" --type Bug')
        sections.append("```\n")

        # CLI commands for the AI - comprehensive reference
        sections.append("## CLI Commands Reference\n")
        sections.append("Use the `janet` CLI to create and update tickets.\n")

        # Get context
        sections.append("### Get Project Context\n")
        sections.append("```bash")
        sections.append("janet context --json")
        sections.append("```")
        sections.append("Returns available projects with their keys. Use this to find valid project keys.\n")

        # Create ticket
        sections.append("### Create a Ticket\n")
        sections.append("```bash")
        sections.append('janet ticket create "Title" --project <PROJECT_KEY> [options]')
        sections.append("```\n")
        sections.append("**Required:**")
        sections.append("- `--project`, `-p` - Project key (e.g., MAIN, BACK, FRONT)\n")
        sections.append("**Optional:**")
        sections.append("- `--description`, `-d` - Detailed description")
        sections.append("- `--status`, `-s` - Status (see valid statuses per project above)")
        sections.append("- `--priority` - Low, Medium, High, Critical")
        sections.append("- `--type`, `-t` - Task, Bug, Story, Epic")
        sections.append("- `--assignee`, `-a` - Assignee email (can use multiple times)")
        sections.append("- `--tag` - Label/tag (can use multiple times)")
        sections.append("- `--json` - Output as JSON\n")
        sections.append("**Example:**")
        sections.append("```bash")
        sections.append('janet ticket create "Fix authentication bug" \\')
        sections.append('  --project BACK \\')
        sections.append('  --description "Users are getting logged out unexpectedly" \\')
        sections.append('  --priority High \\')
        sections.append('  --type Bug \\')
        sections.append('  --tag backend \\')
        sections.append('  --tag auth')
        sections.append("```\n")

        # Update ticket
        sections.append("### Update a Ticket\n")
        sections.append("```bash")
        sections.append('janet ticket update <TICKET_KEY> [options]')
        sections.append("```\n")
        sections.append("**Options:**")
        sections.append("- `--status`, `-s` - New status (see valid statuses per project above)")
        sections.append("- `--title` - New title")
        sections.append("- `--description`, `-d` - New description")
        sections.append("- `--priority` - Low, Medium, High, Critical")
        sections.append("- `--type`, `-t` - Task, Bug, Story, Epic")
        sections.append("- `--assignee`, `-a` - New assignee(s)")
        sections.append("- `--tag` - New tag(s)")
        sections.append("- `--json` - Output as JSON\n")
        sections.append("**Examples:**")
        sections.append("```bash")
        sections.append("# Starting work on a ticket")
        sections.append('janet ticket update MAIN-123 --status "In Progress"')
        sections.append("")
        sections.append("# Marking ticket as complete")
        sections.append('janet ticket update MAIN-123 --status "Done"')
        sections.append("")
        sections.append("# Ticket is blocked by external dependency")
        sections.append('janet ticket update MAIN-123 --status "Blocked"')
        sections.append("")
        sections.append("# Update priority and add description")
        sections.append('janet ticket update MAIN-123 --priority Critical --description "Causing production issues"')
        sections.append("```\n")

        # Project selection guidance
        sections.append("### When to Ask User for Project\n")
        sections.append("If the user doesn't specify which project to use:")
        sections.append("1. Check if there's only one project - use it automatically")
        sections.append("2. If multiple projects exist, ask the user which project to use")
        sections.append("3. Show available projects from the list above\n")

        # Valid field values - now dynamic per project
        sections.append("### Valid Field Values\n")

        # Show statuses per project
        if project_statuses and projects:
            sections.append("**Status (varies by project):**")
            for project in projects:
                key = project.get("project_identifier", "")
                if key in project_statuses and project_statuses[key]:
                    sections.append(f"- {key}: {', '.join(project_statuses[key])}")
            sections.append("")
        else:
            sections.append("**Status:** Run `janet context --json` to see valid statuses per project\n")

        sections.append("**Priority:** Low, Medium, High, Critical")
        sections.append("**Type:** Task, Bug, Story, Epic\n")

        # Common workflow examples
        sections.append("## Common Workflow Examples\n")

        sections.append("### Example 1: Bug Fix Workflow")
        sections.append("When you identify and fix a bug:\n")
        sections.append("```bash")
        sections.append("# 1. Create a bug ticket")
        sections.append('janet ticket create "Fix null pointer in user service" \\')
        sections.append('  --project BACK \\')
        sections.append('  --type Bug \\')
        sections.append('  --priority High \\')
        sections.append('  --description "getUserById throws NPE when user not found"')
        sections.append("")
        sections.append("# 2. Start working on it")
        sections.append('janet ticket update BACK-42 --status "In Progress"')
        sections.append("")
        sections.append("# 3. Mark as done after fixing")
        sections.append('janet ticket update BACK-42 --status "Done"')
        sections.append("```\n")

        sections.append("### Example 2: Feature Implementation")
        sections.append("When implementing a new feature:\n")
        sections.append("```bash")
        sections.append("# Create a story for the feature")
        sections.append('janet ticket create "Add dark mode support" \\')
        sections.append('  --project FRONT \\')
        sections.append('  --type Story \\')
        sections.append('  --priority Medium \\')
        sections.append('  --description "Implement dark mode toggle in settings" \\')
        sections.append('  --tag ui \\')
        sections.append('  --tag feature')
        sections.append("```\n")

        sections.append("### Example 3: Using JSON Output")
        sections.append("When you need to parse the response programmatically:\n")
        sections.append("```bash")
        sections.append("# Get project info as JSON")
        sections.append("janet context --json")
        sections.append("")
        sections.append("# Create ticket and capture the ticket key")
        sections.append('janet ticket create "Automated task" --project MAIN --json')
        sections.append("```\n")

        # Directory structure
        sections.append("## File Structure\n")
        sections.append("```")
        sections.append(f"{org_name}/")
        for project in projects[:5]:  # Show first 5 projects
            key = project.get("project_identifier", "")
            name = project.get("project_name", "")
            sections.append(f"└── {name}/")
            sections.append(f"    ├── {key}-1.md")
            sections.append(f"    └── ...")
        if len(projects) > 5:
            sections.append(f"└── ... ({len(projects) - 5} more projects)")
        sections.append("```\n")

        # Footer
        sections.append("---\n")
        sections.append(
            f"*Synced from [Janet AI](https://app.tryjanet.ai) "
            f"on {sync_time.strftime('%B %d, %Y at %I:%M %p')}*\n"
        )

        return "\n".join(sections)

    def write_readme(
        self,
        sync_dir: Path,
        org_name: str,
        projects: List[Dict],
        total_tickets: int,
        project_statuses: Optional[Dict[str, List[str]]] = None,
    ) -> Path:
        """
        Write README.md to sync directory.

        Args:
            sync_dir: Root sync directory
            org_name: Organization name
            projects: List of synced projects
            total_tickets: Total number of tickets synced
            project_statuses: Dict mapping project_identifier to list of valid statuses

        Returns:
            Path to created README
        """
        sync_time = datetime.utcnow()
        readme_content = self.generate(org_name, projects, total_tickets, sync_time, project_statuses)

        # Write to root of sync directory
        readme_path = sync_dir / "AI_AGENT_INSTRUCTIONS.md"
        readme_path.write_text(readme_content, encoding="utf-8")

        return readme_path
