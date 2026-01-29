"""Context management - CLAUDE.md parsing"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProjectContext:
    """Project context loaded from CLAUDE.md files"""

    system_prompt: str
    workspace_path: Path
    has_local_config: bool
    project_name: Optional[str] = None


def load_project_context(workspace_path: Path) -> Optional[ProjectContext]:
    """
    Load CLAUDE.md and CLAUDE.local.md context from workspace.

    CLAUDE.md is the main project context file (committed to repo).
    CLAUDE.local.md is for local/personal settings (gitignored).
    """
    context_parts = []
    has_local = False
    project_name = None

    # Load global CLAUDE.md
    claude_md = workspace_path / "CLAUDE.md"
    if claude_md.exists():
        content = claude_md.read_text()
        context_parts.append(content)

        # Try to extract project name from first heading
        for line in content.split("\n"):
            if line.startswith("# "):
                project_name = line[2:].strip()
                break

    # Load local CLAUDE.local.md (higher priority, gitignored)
    claude_local = workspace_path / "CLAUDE.local.md"
    if claude_local.exists():
        context_parts.append(claude_local.read_text())
        has_local = True

    if not context_parts:
        return None

    return ProjectContext(
        system_prompt="\n\n---\n\n".join(context_parts),
        workspace_path=workspace_path,
        has_local_config=has_local,
        project_name=project_name,
    )


def build_system_prompt(context: Optional[ProjectContext], workspace_path: Path) -> str:
    """Build the complete system prompt for the agent"""
    parts = [
        "You are Cosmux, an AI coding agent that helps developers write and modify code.",
        "You are running inside a web-based development environment.",
        "",
        "## Capabilities",
        "- Read, write, and edit files in the workspace",
        "- Execute bash commands",
        "- Search for files and content using glob and grep patterns",
        "",
        "## Guidelines",
        "- Always read files before editing them",
        "- Make minimal, focused changes",
        "- Explain what you're doing before making changes",
        "- Use appropriate tools for each task",
        "",
        f"## Workspace",
        f"Working directory: {workspace_path}",
    ]

    if context:
        parts.extend([
            "",
            "## Project Context",
            context.system_prompt,
        ])

    return "\n".join(parts)
