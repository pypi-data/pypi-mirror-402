"""Chat screen - main conversation interface."""

import asyncio
from typing import TYPE_CHECKING

from textual import on, work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.worker import Worker, WorkerState

from cc_python.api import AnthropicClient, APIError
from cc_python.api.client import ChatMessage, StreamEvent
from cc_python.config import get_settings
from cc_python.conversation import ConversationHistory, SessionManager, ProjectContext
from cc_python.models import Message, MessageRole
from cc_python.permissions import PermissionDecision, PermissionRequest
from cc_python.widgets import (
    HeaderWidget,
    InputAreaWidget,
    MessageListWidget,
    StatusBarWidget,
    PermissionDialog,
)

if TYPE_CHECKING:
    from cc_python.app import CCPythonApp


class ChatScreen(Screen):
    """Main chat screen for conversation."""

    DEFAULT_CSS = """
    ChatScreen {
        layout: vertical;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._settings = get_settings()
        self._session_manager = SessionManager()
        self._session = self._session_manager.get_or_create_session()
        self._history = self._session.history
        self._project_context = ProjectContext()
        self._client: AnthropicClient | None = None
        self._is_processing = False
        self._current_worker: Worker | None = None

    def compose(self) -> ComposeResult:
        """Compose the chat screen layout."""
        yield HeaderWidget()
        yield MessageListWidget(id="message-list")
        yield InputAreaWidget(id="input-area")
        yield StatusBarWidget()

    def on_mount(self) -> None:
        """Focus input when screen mounts."""
        self.query_one("#input-area", InputAreaWidget).focus_input()
        self._initialize_client()
        self._load_project_context()

    def _initialize_client(self) -> None:
        """Initialize the API client."""
        if self._settings.has_api_key:
            try:
                self._client = AnthropicClient()
            except APIError as e:
                self.add_system_message(f"API Error: {e}")
        else:
            self.add_system_message(
                "API key not configured. Set ANTHROPIC_API_KEY environment variable or use /config command."
            )

    def _load_project_context(self) -> None:
        """Load project context from CLAUDE.md."""
        if self._project_context.load_context():
            self._history.system_context = self._project_context.get_system_prompt_addition()
            self.add_system_message(
                f"Loaded project context from {self._project_context._context_file.name}"
            )

    @on(InputAreaWidget.Submitted)
    def on_input_submitted(self, event: InputAreaWidget.Submitted) -> None:
        """Handle user input submission."""
        if self._is_processing:
            return

        text = event.value

        # Check if it's a command
        if text.startswith("/"):
            self._handle_command(text)
        else:
            self._handle_message(text)

    def _handle_command(self, text: str) -> None:
        """Handle slash command."""
        result = self.app.command_registry.execute(self.app, text)

        if result is None:
            return

        if result.clear_messages:
            self.query_one("#message-list", MessageListWidget).clear_messages()
            self._history.clear()

        if result.message:
            self.add_system_message(result.message)

        if result.should_exit:
            self.app.exit()

    def _handle_message(self, text: str) -> None:
        """Handle regular message."""
        if not self._client:
            self.add_system_message(
                "API client not initialized. Please configure your API key."
            )
            return

        # Add user message
        self.add_user_message(text)
        self._history.add_user_message(text)

        # Start streaming response
        self._start_ai_response()

    def _start_ai_response(self) -> None:
        """Start getting AI response."""
        self._is_processing = True
        self._set_input_enabled(False)
        self._update_status("Thinking...")

        # Start streaming
        message_list = self.query_one("#message-list", MessageListWidget)
        message_list.start_streaming()

        # Run the async task
        self._current_worker = self._stream_response()

    @work(exclusive=True)
    async def _stream_response(self) -> None:
        """Stream the AI response."""
        if not self._client:
            return

        message_list = self.query_one("#message-list", MessageListWidget)
        full_response = ""
        thinking_content = ""

        try:
            messages = self._history.get_api_messages()

            # Get tools from app if available
            tools = None
            if hasattr(self.app, "tool_manager"):
                tools = self.app.tool_manager.get_tool_definitions()

            # Get system context
            system_context = self._history.system_context if self._history.system_context else None

            async for event in self._client.chat_stream(messages, system=system_context, tools=tools):
                if event.type == "text":
                    full_response += event.content
                    message_list.append_to_stream(event.content)

                elif event.type == "thinking":
                    thinking_content += event.content
                    # Optionally show thinking in UI
                    if self._settings.thinking_enabled:
                        self._update_status(f"Thinking: {thinking_content[:50]}...")

                elif event.type == "tool_use":
                    # Handle tool use
                    await self._handle_tool_use(
                        event.tool_name,
                        event.tool_id,
                        event.tool_input or {},
                    )

                elif event.type == "done":
                    break

                elif event.type == "error":
                    self.add_system_message(f"Error: {event.content}")
                    break

            # Finish streaming
            message_list.finish_streaming()

            # Add to history
            if full_response:
                self._history.add_assistant_message(
                    full_response, thinking=thinking_content
                )

        except APIError as e:
            message_list.cancel_streaming()
            self.add_system_message(f"API Error: {e}")

        except Exception as e:
            message_list.cancel_streaming()
            self.add_system_message(f"Error: {e}")

        finally:
            self._is_processing = False
            self._set_input_enabled(True)
            self._update_status("")

    async def _handle_tool_use(
        self,
        tool_name: str,
        tool_id: str,
        tool_input: dict,
    ) -> None:
        """Handle a tool use request from the AI."""
        # Get tool info
        tool = self.app.tool_manager.get(tool_name) if hasattr(self.app, "tool_manager") else None

        if not tool:
            self.add_system_message(f"Unknown tool: {tool_name}")
            self._history.add_tool_result(tool_id, f"Unknown tool: {tool_name}", is_error=True)
            return

        # Check if permission is needed
        if tool.requires_approval:
            # Create permission request
            request = PermissionRequest(
                tool_name=tool_name,
                tool_category=tool.category,
                description=tool.description,
                params=tool_input,
            )

            # Check with permission manager
            if hasattr(self.app, "permission_manager"):
                decision = self.app.permission_manager.check_permission(request)

                # If no automatic decision, show dialog
                if decision == PermissionDecision.DENY:
                    # Show permission dialog
                    decision = await self._show_permission_dialog(request)

                if decision == PermissionDecision.DENY:
                    self.add_system_message(f"Tool '{tool_name}' execution denied")
                    self._history.add_tool_result(
                        tool_id, "Tool execution denied by user", is_error=True
                    )
                    return

                # Handle the decision
                if decision == PermissionDecision.ALLOW_ALWAYS:
                    self.app.permission_manager.allow_tool(tool_name, session_only=False)
                elif decision == PermissionDecision.ALLOW_SESSION:
                    self.app.permission_manager.allow_tool(tool_name, session_only=True)

        # Show tool use in UI
        self.add_tool_message(f"Using tool: {tool_name}")

        # Execute tool
        result = await self.app.tool_manager.execute_tool(
            tool_name, tool_input, skip_approval=True
        )

        # Add tool result to history
        self._history.add_tool_result(
            tool_id, result.output, is_error=result.is_error
        )

        if result.is_error:
            self.add_system_message(f"Tool error: {result.output}")
        else:
            # Truncate long output for display
            display_output = result.output
            if len(display_output) > 500:
                display_output = display_output[:500] + "..."
            self.add_tool_message(f"Result:\n{display_output}")

    async def _show_permission_dialog(
        self, request: PermissionRequest
    ) -> PermissionDecision:
        """Show permission dialog and wait for user decision."""
        dialog = PermissionDialog(request)
        decision = await self.app.push_screen_wait(dialog)
        return decision if decision else PermissionDecision.DENY

    def _set_input_enabled(self, enabled: bool) -> None:
        """Enable or disable input."""
        input_area = self.query_one("#input-area", InputAreaWidget)
        if enabled:
            input_area.focus_input()

    def _update_status(self, status: str) -> None:
        """Update the status bar."""
        status_bar = self.query_one(StatusBarWidget)
        if status:
            status_bar.update_left(status)
        else:
            status_bar.update_left("? for shortcuts")

    def add_user_message(self, content: str) -> None:
        """Add a user message to the list."""
        message = Message(role=MessageRole.USER, content=content)
        self.query_one("#message-list", MessageListWidget).add_message(message)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the list."""
        message = Message(role=MessageRole.ASSISTANT, content=content)
        self.query_one("#message-list", MessageListWidget).add_message(message)

    def add_system_message(self, content: str) -> None:
        """Add a system message to the list."""
        message = Message(role=MessageRole.SYSTEM, content=content)
        self.query_one("#message-list", MessageListWidget).add_message(message)

    def add_tool_message(self, content: str) -> None:
        """Add a tool message to the list."""
        message = Message(role=MessageRole.TOOL, content=content)
        self.query_one("#message-list", MessageListWidget).add_message(message)

    def add_thinking_message(self, content: str) -> None:
        """Add a thinking message to the list."""
        message = Message(role=MessageRole.THINKING, content=content)
        self.query_one("#message-list", MessageListWidget).add_message(message)

    def toggle_thinking(self) -> None:
        """Toggle thinking mode."""
        self._settings.thinking_enabled = not self._settings.thinking_enabled
        self.query_one(StatusBarWidget).set_thinking(self._settings.thinking_enabled)

    @property
    def thinking_enabled(self) -> bool:
        """Check if thinking mode is enabled."""
        return self._settings.thinking_enabled

    @property
    def session(self):
        """Get current session."""
        return self._session

    @property
    def history(self) -> ConversationHistory:
        """Get conversation history."""
        return self._history
