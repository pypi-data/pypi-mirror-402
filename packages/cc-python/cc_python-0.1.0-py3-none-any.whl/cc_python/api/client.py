"""Anthropic API client for CC Python."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import anthropic
from anthropic import APIError as AnthropicAPIError
from anthropic.types import (
    ContentBlock,
    Message,
    RawContentBlockDeltaEvent,
    RawContentBlockStartEvent,
    RawContentBlockStopEvent,
    RawMessageDeltaEvent,
    RawMessageStartEvent,
    RawMessageStopEvent,
    TextBlock,
    TextDelta,
    ToolUseBlock,
)

from cc_python.config import get_settings


class APIError(Exception):
    """Custom API error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class StreamEvent:
    """Event from streaming response."""

    type: str  # "text", "tool_use", "thinking", "done", "error"
    content: str = ""
    tool_name: str = ""
    tool_id: str = ""
    tool_input: dict[str, Any] | None = None


@dataclass
class ChatMessage:
    """Message for chat API."""

    role: str  # "user" or "assistant"
    content: str | list[dict[str, Any]]


class AnthropicClient:
    """Client for Anthropic API."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the client."""
        settings = get_settings()
        self.api_key = api_key or settings.api_key

        if not self.api_key:
            raise APIError("API key not configured. Set ANTHROPIC_API_KEY environment variable.")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.async_client = anthropic.AsyncAnthropic(api_key=self.api_key)

    def _build_messages(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Build messages for API request."""
        return [{"role": m.role, "content": m.content} for m in messages]

    def _build_system_prompt(self, system: str | None = None) -> str:
        """Build system prompt."""
        base_prompt = """You are Claude, an AI assistant created by Anthropic. You are helping the user with coding tasks in their terminal.

You have access to tools that allow you to:
- Read and write files
- Execute shell commands
- Search for files and content
- Interact with git repositories

Always be helpful, accurate, and concise. When making changes to files, explain what you're doing and why."""

        if system:
            return f"{base_prompt}\n\n{system}"
        return base_prompt

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Message:
        """Send a chat message and get a response."""
        settings = get_settings()

        try:
            kwargs: dict[str, Any] = {
                "model": settings.model,
                "max_tokens": settings.max_tokens,
                "system": self._build_system_prompt(system),
                "messages": self._build_messages(messages),
            }

            if tools:
                kwargs["tools"] = tools

            # Add thinking if enabled
            if settings.thinking_enabled:
                kwargs["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": settings.thinking_budget,
                }

            response = await self.async_client.messages.create(**kwargs)
            return response

        except AnthropicAPIError as e:
            raise APIError(str(e), getattr(e, "status_code", None)) from e

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[StreamEvent]:
        """Stream a chat response."""
        settings = get_settings()

        try:
            kwargs: dict[str, Any] = {
                "model": settings.model,
                "max_tokens": settings.max_tokens,
                "system": self._build_system_prompt(system),
                "messages": self._build_messages(messages),
            }

            if tools:
                kwargs["tools"] = tools

            # Add thinking if enabled
            if settings.thinking_enabled:
                kwargs["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": settings.thinking_budget,
                }

            current_tool_name = ""
            current_tool_id = ""
            current_tool_input = ""
            current_block_type = ""

            async with self.async_client.messages.stream(**kwargs) as stream:
                async for event in stream:
                    if isinstance(event, RawContentBlockStartEvent):
                        block = event.content_block
                        if hasattr(block, "type"):
                            current_block_type = block.type
                            if block.type == "tool_use":
                                current_tool_name = getattr(block, "name", "")
                                current_tool_id = getattr(block, "id", "")
                                current_tool_input = ""
                            elif block.type == "thinking":
                                yield StreamEvent(type="thinking", content="")

                    elif isinstance(event, RawContentBlockDeltaEvent):
                        delta = event.delta
                        if hasattr(delta, "type"):
                            if delta.type == "text_delta":
                                yield StreamEvent(
                                    type="text",
                                    content=getattr(delta, "text", ""),
                                )
                            elif delta.type == "thinking_delta":
                                yield StreamEvent(
                                    type="thinking",
                                    content=getattr(delta, "thinking", ""),
                                )
                            elif delta.type == "input_json_delta":
                                current_tool_input += getattr(
                                    delta, "partial_json", ""
                                )

                    elif isinstance(event, RawContentBlockStopEvent):
                        if current_block_type == "tool_use" and current_tool_name:
                            import json

                            try:
                                tool_input = (
                                    json.loads(current_tool_input)
                                    if current_tool_input
                                    else {}
                                )
                            except json.JSONDecodeError:
                                tool_input = {}

                            yield StreamEvent(
                                type="tool_use",
                                tool_name=current_tool_name,
                                tool_id=current_tool_id,
                                tool_input=tool_input,
                            )
                            current_tool_name = ""
                            current_tool_id = ""
                            current_tool_input = ""
                        current_block_type = ""

                    elif isinstance(event, RawMessageStopEvent):
                        yield StreamEvent(type="done")

        except AnthropicAPIError as e:
            yield StreamEvent(type="error", content=str(e))
            raise APIError(str(e), getattr(e, "status_code", None)) from e

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        import tiktoken

        # Use cl100k_base encoding (similar to Claude's tokenizer)
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            # Fallback: rough estimate
            return len(text) // 4
