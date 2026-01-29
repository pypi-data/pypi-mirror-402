"""Conversation history management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from cc_python.api.client import ChatMessage


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""

    role: str  # "user" or "assistant"
    content: str | list[dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    thinking: str = ""

    def to_api_message(self) -> ChatMessage:
        """Convert to API message format."""
        return ChatMessage(role=self.role, content=self.content)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "thinking": self.thinking,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationTurn":
        """Create from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            tool_calls=data.get("tool_calls", []),
            tool_results=data.get("tool_results", []),
            thinking=data.get("thinking", ""),
        )


class ConversationHistory:
    """Manages conversation history."""

    def __init__(self, max_tokens: int = 100000) -> None:
        """Initialize conversation history."""
        self._turns: list[ConversationTurn] = []
        self._max_tokens = max_tokens
        self._system_context: str = ""

    @property
    def turns(self) -> list[ConversationTurn]:
        """Get all turns."""
        return self._turns.copy()

    @property
    def system_context(self) -> str:
        """Get system context."""
        return self._system_context

    @system_context.setter
    def system_context(self, value: str) -> None:
        """Set system context."""
        self._system_context = value

    def add_user_message(self, content: str) -> ConversationTurn:
        """Add a user message."""
        turn = ConversationTurn(role="user", content=content)
        self._turns.append(turn)
        return turn

    def add_assistant_message(
        self,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
        thinking: str = "",
    ) -> ConversationTurn:
        """Add an assistant message."""
        turn = ConversationTurn(
            role="assistant",
            content=content,
            tool_calls=tool_calls or [],
            thinking=thinking,
        )
        self._turns.append(turn)
        return turn

    def add_tool_result(
        self,
        tool_use_id: str,
        result: str,
        is_error: bool = False,
    ) -> None:
        """Add a tool result to the conversation."""
        # Tool results are added as user messages with special content
        content: list[dict[str, Any]] = [
            {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result,
                "is_error": is_error,
            }
        ]
        turn = ConversationTurn(role="user", content=content)
        self._turns.append(turn)

    def get_api_messages(self) -> list[ChatMessage]:
        """Get messages in API format."""
        return [turn.to_api_message() for turn in self._turns]

    def clear(self) -> None:
        """Clear all conversation history."""
        self._turns.clear()

    def get_last_assistant_message(self) -> ConversationTurn | None:
        """Get the last assistant message."""
        for turn in reversed(self._turns):
            if turn.role == "assistant":
                return turn
        return None

    def estimate_tokens(self) -> int:
        """Estimate total tokens in conversation."""
        from cc_python.api.client import AnthropicClient

        total = 0
        for turn in self._turns:
            if isinstance(turn.content, str):
                total += len(turn.content) // 4  # Rough estimate
            else:
                # For complex content (tool results, etc.)
                import json

                total += len(json.dumps(turn.content)) // 4
        return total

    def trim_to_fit(self, target_tokens: int | None = None) -> int:
        """Trim old messages to fit within token limit.

        Returns the number of turns removed.
        """
        target = target_tokens or self._max_tokens
        removed = 0

        while self.estimate_tokens() > target and len(self._turns) > 2:
            # Keep at least the last user message and response
            self._turns.pop(0)
            removed += 1

        return removed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "turns": [turn.to_dict() for turn in self._turns],
            "system_context": self._system_context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationHistory":
        """Create from dictionary."""
        history = cls()
        history._turns = [
            ConversationTurn.from_dict(turn) for turn in data.get("turns", [])
        ]
        history._system_context = data.get("system_context", "")
        return history
