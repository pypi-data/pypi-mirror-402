"""Base tool interface and registry"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolInput:
    """Base class for tool inputs"""

    pass


@dataclass
class ToolOutput:
    """Standard tool output"""

    success: bool
    result: Any = None
    error: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for all tools"""

    name: str
    description: str

    @abstractmethod
    async def execute(self, input_data: dict, workspace_path: str) -> ToolOutput:
        """Execute the tool with given input"""
        pass

    @abstractmethod
    def get_schema(self) -> dict:
        """Return the tool schema for Claude API"""
        pass


@dataclass
class ToolRegistry:
    """Registry for available tools"""

    _tools: dict[str, BaseTool] = field(default_factory=dict)

    def register(self, tool: BaseTool) -> None:
        """Register a tool"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self._tools.get(name)

    def get_schemas(self) -> list[dict]:
        """Get all tool schemas for Claude API"""
        return [tool.get_schema() for tool in self._tools.values()]

    def list_tools(self) -> list[str]:
        """List all registered tool names"""
        return list(self._tools.keys())
