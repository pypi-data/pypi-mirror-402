"""Base tool framework for CC Python."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolResult:
    """Result of executing a tool."""

    output: str
    is_error: bool = False
    data: Any = None


@dataclass
class ToolParameter:
    """Parameter definition for a tool."""

    name: str
    type: str  # "string", "integer", "boolean", "array", "object"
    description: str
    required: bool = True
    default: Any = None
    enum: list[str] | None = None


class Tool(ABC):
    """Base class for all tools."""

    name: str
    description: str
    parameters: list[ToolParameter] = []

    # Permission settings
    requires_approval: bool = True
    category: str = "general"  # "read", "write", "execute", "general"

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    def get_definition(self) -> dict[str, Any]:
        """Get the tool definition for API."""
        properties = {}
        required = []

        for param in self.parameters:
            prop: dict[str, Any] = {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def validate_params(self, params: dict[str, Any]) -> tuple[bool, str]:
        """Validate parameters before execution."""
        for param in self.parameters:
            if param.required and param.name not in params:
                return False, f"Missing required parameter: {param.name}"

            if param.name in params:
                value = params[param.name]
                # Type validation
                if param.type == "string" and not isinstance(value, str):
                    return False, f"Parameter {param.name} must be a string"
                elif param.type == "integer" and not isinstance(value, int):
                    return False, f"Parameter {param.name} must be an integer"
                elif param.type == "boolean" and not isinstance(value, bool):
                    return False, f"Parameter {param.name} must be a boolean"
                elif param.type == "array" and not isinstance(value, list):
                    return False, f"Parameter {param.name} must be an array"

                # Enum validation
                if param.enum and value not in param.enum:
                    return False, f"Parameter {param.name} must be one of: {param.enum}"

        return True, ""


class ToolManager:
    """Manages tool registration and execution."""

    def __init__(self) -> None:
        """Initialize tool manager."""
        self._tools: dict[str, Tool] = {}
        self._permission_callback: Callable[[Tool, dict], bool] | None = None

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_all(self) -> list[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions for API."""
        return [tool.get_definition() for tool in self._tools.values()]

    def set_permission_callback(
        self, callback: Callable[[Tool, dict], bool]
    ) -> None:
        """Set callback for permission requests."""
        self._permission_callback = callback

    async def execute_tool(
        self,
        name: str,
        params: dict[str, Any],
        skip_approval: bool = False,
    ) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                output=f"Unknown tool: {name}",
                is_error=True,
            )

        # Validate parameters
        valid, error = tool.validate_params(params)
        if not valid:
            return ToolResult(output=error, is_error=True)

        # Check permission
        if tool.requires_approval and not skip_approval:
            if self._permission_callback:
                approved = self._permission_callback(tool, params)
                if not approved:
                    return ToolResult(
                        output="Tool execution denied by user",
                        is_error=True,
                    )

        # Execute tool
        try:
            return await tool.execute(**params)
        except Exception as e:
            return ToolResult(
                output=f"Tool execution error: {e}",
                is_error=True,
            )

    def get_tools_by_category(self, category: str) -> list[Tool]:
        """Get tools by category."""
        return [t for t in self._tools.values() if t.category == category]
