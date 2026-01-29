"""Message data model."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageRole(Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    THINKING = "thinking"


@dataclass
class Message:
    """A single message in the conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_name: str = ""
    tool_id: str = ""
    tool_input: dict[str, Any] | None = None
    tool_result: str = ""
    is_error: bool = False

    @property
    def is_user(self) -> bool:
        """Check if message is from user."""
        return self.role == MessageRole.USER

    @property
    def is_assistant(self) -> bool:
        """Check if message is from assistant."""
        return self.role == MessageRole.ASSISTANT

    @property
    def is_tool(self) -> bool:
        """Check if message is a tool call/result."""
        return self.role == MessageRole.TOOL

    @property
    def is_thinking(self) -> bool:
        """Check if message is thinking content."""
        return self.role == MessageRole.THINKING
