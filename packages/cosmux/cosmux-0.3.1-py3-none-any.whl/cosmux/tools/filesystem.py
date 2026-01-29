"""Filesystem tools: Read, Write, Edit, Glob, Grep"""

import re
from pathlib import Path
from typing import Optional, Tuple

from cosmux.tools.base import BaseTool, ToolOutput


def resolve_and_validate_path(
    file_path: str,
    workspace_path: str,
) -> Tuple[Optional[Path], Optional[ToolOutput]]:
    """
    Resolve a file path and validate it's within the workspace.

    Args:
        file_path: The file path to resolve (relative to workspace)
        workspace_path: The workspace root path

    Returns:
        Tuple of (resolved_path, error_output).
        If validation fails, resolved_path is None and error_output contains the error.
        If validation succeeds, error_output is None.
    """
    path = (Path(workspace_path) / file_path).resolve()
    workspace = Path(workspace_path).resolve()

    if not str(path).startswith(str(workspace)):
        return None, ToolOutput(success=False, error="Path outside workspace")

    return path, None


class ReadTool(BaseTool):
    """Read file contents from the filesystem"""

    name = "Read"
    description = "Read the contents of a file"

    async def execute(self, input_data: dict, workspace_path: str) -> ToolOutput:
        try:
            file_path = input_data.get("file_path", "")
            offset = input_data.get("offset")
            limit = input_data.get("limit")

            path, error = resolve_and_validate_path(file_path, workspace_path)
            if error:
                return error

            if not path.exists():
                return ToolOutput(success=False, error=f"File not found: {file_path}")

            if not path.is_file():
                return ToolOutput(success=False, error=f"Not a file: {file_path}")

            content = path.read_text()

            # Apply offset/limit
            if offset is not None or limit is not None:
                lines = content.splitlines(keepends=True)
                if offset:
                    lines = lines[offset:]
                if limit:
                    lines = lines[:limit]
                content = "".join(lines)

            return ToolOutput(success=True, result=content)

        except Exception as e:
            return ToolOutput(success=False, error=str(e))

    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read (relative to workspace)",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Line number to start reading from (0-indexed)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of lines to read",
                    },
                },
                "required": ["file_path"],
            },
        }


class WriteTool(BaseTool):
    """Write content to a file"""

    name = "Write"
    description = "Write content to a file, creating it if necessary"

    async def execute(self, input_data: dict, workspace_path: str) -> ToolOutput:
        try:
            file_path = input_data.get("file_path", "")
            content = input_data.get("content", "")

            path, error = resolve_and_validate_path(file_path, workspace_path)
            if error:
                return error

            # Create parent directories
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            path.write_text(content)

            return ToolOutput(
                success=True,
                result=f"Written {len(content)} bytes to {file_path}",
            )

        except Exception as e:
            return ToolOutput(success=False, error=str(e))

    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to write (relative to workspace)",
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file",
                    },
                },
                "required": ["file_path", "content"],
            },
        }


class EditTool(BaseTool):
    """Edit a file by replacing text"""

    name = "Edit"
    description = "Edit a file by replacing old_string with new_string"

    async def execute(self, input_data: dict, workspace_path: str) -> ToolOutput:
        try:
            file_path = input_data.get("file_path", "")
            old_string = input_data.get("old_string", "")
            new_string = input_data.get("new_string", "")
            replace_all = input_data.get("replace_all", False)

            path, error = resolve_and_validate_path(file_path, workspace_path)
            if error:
                return error

            if not path.exists():
                return ToolOutput(success=False, error=f"File not found: {file_path}")

            content = path.read_text()

            # Check if old_string exists
            if old_string not in content:
                return ToolOutput(
                    success=False,
                    error=f"String not found in file: {old_string[:50]}...",
                )

            # Check for uniqueness if not replace_all
            if not replace_all and content.count(old_string) > 1:
                return ToolOutput(
                    success=False,
                    error=f"String appears {content.count(old_string)} times. "
                    "Provide more context or use replace_all=true",
                )

            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
                count = content.count(old_string)
            else:
                new_content = content.replace(old_string, new_string, 1)
                count = 1

            path.write_text(new_content)

            return ToolOutput(
                success=True,
                result=f"Replaced {count} occurrence(s) in {file_path}",
            )

        except Exception as e:
            return ToolOutput(success=False, error=str(e))

    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to edit",
                    },
                    "old_string": {
                        "type": "string",
                        "description": "The exact string to replace",
                    },
                    "new_string": {
                        "type": "string",
                        "description": "The string to replace it with",
                    },
                    "replace_all": {
                        "type": "boolean",
                        "description": "Replace all occurrences (default: false)",
                        "default": False,
                    },
                },
                "required": ["file_path", "old_string", "new_string"],
            },
        }


class GlobTool(BaseTool):
    """Find files matching a glob pattern"""

    name = "Glob"
    description = "Find files matching a glob pattern"

    async def execute(self, input_data: dict, workspace_path: str) -> ToolOutput:
        try:
            pattern = input_data.get("pattern", "")
            search_path = input_data.get("path", "")

            base_path, error = resolve_and_validate_path(search_path, workspace_path)
            if error:
                return error

            # Find matches
            matches = list(base_path.glob(pattern))
            workspace = Path(workspace_path).resolve()

            # Convert to relative paths and filter files only
            relative_paths = []
            for p in matches:
                if p.is_file():
                    try:
                        rel = p.relative_to(workspace)
                        relative_paths.append(str(rel))
                    except ValueError:
                        pass

            # Sort by modification time (newest first)
            relative_paths.sort(
                key=lambda x: workspace.joinpath(x).stat().st_mtime,
                reverse=True,
            )

            return ToolOutput(success=True, result=relative_paths)

        except Exception as e:
            return ToolOutput(success=False, error=str(e))

    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g., '**/*.py', 'src/**/*.ts')",
                    },
                    "path": {
                        "type": "string",
                        "description": "Base directory for search (relative to workspace)",
                    },
                },
                "required": ["pattern"],
            },
        }


class GrepTool(BaseTool):
    """Search for patterns in files"""

    name = "Grep"
    description = "Search for a regex pattern in files"

    async def execute(self, input_data: dict, workspace_path: str) -> ToolOutput:
        try:
            pattern = input_data.get("pattern", "")
            search_path = input_data.get("path", "")
            glob_pattern = input_data.get("glob", "**/*")
            max_results = input_data.get("max_results", 100)

            base_path, error = resolve_and_validate_path(search_path, workspace_path)
            if error:
                return error

            workspace = Path(workspace_path).resolve()

            # Compile regex
            try:
                regex = re.compile(pattern)
            except re.error as e:
                return ToolOutput(success=False, error=f"Invalid regex: {e}")

            # Find and search files
            matches = []
            for file_path in base_path.glob(glob_pattern):
                if not file_path.is_file() or len(matches) >= max_results:
                    continue

                try:
                    content = file_path.read_text()
                    for i, line in enumerate(content.splitlines(), 1):
                        if regex.search(line):
                            matches.append({
                                "file": str(file_path.relative_to(workspace)),
                                "line": i,
                                "content": line.strip()[:200],
                            })
                            if len(matches) >= max_results:
                                break
                except (UnicodeDecodeError, PermissionError):
                    continue

            return ToolOutput(success=True, result=matches)

        except Exception as e:
            return ToolOutput(success=False, error=str(e))

    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for",
                    },
                    "path": {
                        "type": "string",
                        "description": "Directory to search in (relative to workspace)",
                    },
                    "glob": {
                        "type": "string",
                        "description": "Glob pattern to filter files (default: **/*)",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 100)",
                    },
                },
                "required": ["pattern"],
            },
        }
