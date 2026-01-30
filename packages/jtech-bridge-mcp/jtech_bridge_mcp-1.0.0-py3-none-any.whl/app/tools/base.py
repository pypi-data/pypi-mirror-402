"""
Base Tool Module

Provides base classes and registry for MCP tools.
Implements the Strategy Pattern for tool handling.
"""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from mcp.types import TextContent, Tool

from app.logging_config import get_logger

logger = get_logger(__name__)
T = TypeVar("T")


class BaseTool(ABC):
    """
    Abstract base class for MCP tools.

    Provides a common interface for all tools following
    the Template Method Pattern.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable tool description."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input parameters."""
        pass

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> list[TextContent]:
        """
        Execute the tool with given arguments.

        Args:
            arguments: Tool input arguments.

        Returns:
            List of TextContent responses.
        """
        pass

    def to_mcp_tool(self) -> Tool:
        """Convert to MCP Tool definition."""
        return Tool(
            name=self.name,
            description=self.description,
            inputSchema=self.input_schema,
        )


class ToolRegistry:
    """
    Registry for MCP tools.

    Manages tool registration and dispatching.
    Implements the Registry Pattern for dynamic tool management.
    """

    def __init__(self) -> None:
        """Initialize the tool registry."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool instance to register.
        """
        if tool.name in self._tools:
            logger.warning(f"Tool already registered, overwriting: {tool.name}")
        self._tools[tool.name] = tool
        logger.debug(f"Tool registered: {tool.name}")

    def register_all(self, tools: list[BaseTool]) -> None:
        """
        Register multiple tools.

        Args:
            tools: List of tool instances.
        """
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> BaseTool | None:
        """
        Get a tool by name.

        Args:
            name: Tool name.

        Returns:
            Tool instance or None if not found.
        """
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        """
        Get all registered tools as MCP Tool definitions.

        Returns:
            List of MCP Tool definitions.
        """
        return [tool.to_mcp_tool() for tool in self._tools.values()]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """
        Call a registered tool.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            Tool execution result.

        Raises:
            ValueError: If tool is not found.
        """
        tool = self.get(name)
        if tool is None:
            logger.error(f"Unknown tool called: {name}")
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        logger.debug(f"Executing tool: {name} with args: {arguments}")
        return await tool.execute(arguments)

    @property
    def tool_names(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())
