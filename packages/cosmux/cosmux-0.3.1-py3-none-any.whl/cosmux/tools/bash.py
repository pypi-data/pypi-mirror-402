"""Bash tool for command execution"""

import asyncio
import os
from pathlib import Path
from typing import Optional

from cosmux.tools.base import BaseTool, ToolOutput


class BashTool(BaseTool):
    """Execute bash commands in the workspace"""

    name = "Bash"
    description = "Execute a bash command in the workspace directory"

    # Commands that require extra caution
    DANGEROUS_PATTERNS = [
        "rm -rf /",
        "rm -rf /*",
        "dd if=",
        "> /dev/",
        "mkfs",
        ":(){:|:&};:",  # Fork bomb
        "chmod -R 777 /",
        "chown -R",
    ]

    # Commands that are blocked entirely
    BLOCKED_COMMANDS = [
        "sudo",
        "su ",
        "reboot",
        "shutdown",
        "halt",
        "poweroff",
    ]

    async def execute(self, input_data: dict, workspace_path: str) -> ToolOutput:
        command = input_data.get("command", "")
        timeout = input_data.get("timeout", 120)  # 2 minutes default
        description = input_data.get("description", "")

        # Security: Check for blocked commands
        for blocked in self.BLOCKED_COMMANDS:
            if command.strip().startswith(blocked):
                return ToolOutput(
                    success=False,
                    error=f"Command blocked: '{blocked}' is not allowed",
                )

        # Security: Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in command:
                return ToolOutput(
                    success=False,
                    error=f"Command blocked: contains dangerous pattern",
                )

        try:
            # Set up environment
            env = os.environ.copy()
            env["HOME"] = str(Path.home())
            env["PWD"] = workspace_path

            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=workspace_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolOutput(
                    success=False,
                    error=f"Command timed out after {timeout} seconds",
                )

            # Decode output
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")

            # Truncate very long output
            max_output = 50000  # 50KB
            if len(stdout_str) > max_output:
                stdout_str = stdout_str[:max_output] + "\n... (output truncated)"
            if len(stderr_str) > max_output:
                stderr_str = stderr_str[:max_output] + "\n... (output truncated)"

            # Check return code
            if process.returncode != 0:
                error_msg = stderr_str or f"Command exited with code {process.returncode}"
                return ToolOutput(
                    success=False,
                    result=stdout_str if stdout_str else None,
                    error=error_msg,
                )

            # Combine output
            output = stdout_str
            if stderr_str:
                output = output + "\n[stderr]\n" + stderr_str if output else stderr_str

            return ToolOutput(success=True, result=output or "(no output)")

        except Exception as e:
            return ToolOutput(success=False, error=str(e))

    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to execute",
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of what this command does",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default: 120)",
                        "default": 120,
                    },
                },
                "required": ["command"],
            },
        }
