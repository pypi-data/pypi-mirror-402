"""Message list widget for displaying conversation."""

from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static

from cc_python.models import Message, MessageRole


class MessageWidget(Static):
    """Widget for displaying a single message."""

    DEFAULT_CSS = """
    MessageWidget {
        height: auto;
        padding: 0 2 1 2;
    }

    MessageWidget.user-message .marker {
        color: #888888;
    }

    MessageWidget.assistant-message .marker {
        color: #5c8eff;
    }

    MessageWidget.system-message .marker {
        color: #ffa500;
    }

    MessageWidget.tool-message .marker {
        color: #00aa00;
    }

    MessageWidget.thinking-message {
        color: #666666;
        text-style: italic;
    }

    MessageWidget.streaming {
        border-left: solid #5c8eff;
        padding-left: 1;
    }
    """

    def __init__(self, message: Message, use_markdown: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self.message = message
        self.use_markdown = use_markdown
        self._content_widget: Static | None = None
        self._set_message_class()

    def _set_message_class(self) -> None:
        """Set CSS class based on message role."""
        if self.message.role == MessageRole.USER:
            self.add_class("user-message")
        elif self.message.role == MessageRole.ASSISTANT:
            self.add_class("assistant-message")
        elif self.message.role == MessageRole.TOOL:
            self.add_class("tool-message")
        elif self.message.role == MessageRole.THINKING:
            self.add_class("thinking-message")
        else:
            self.add_class("system-message")

    def compose(self) -> ComposeResult:
        """Compose the message display."""
        self._content_widget = Static(self._format_message(), id="content")
        yield self._content_widget

    def _get_marker(self) -> Text:
        """Get the marker for this message type."""
        text = Text()
        if self.message.role == MessageRole.USER:
            text.append("> ", style="#888888")
        elif self.message.role == MessageRole.ASSISTANT:
            text.append("● ", style="#5c8eff")
        elif self.message.role == MessageRole.TOOL:
            text.append("⚙ ", style="#00aa00")
        elif self.message.role == MessageRole.THINKING:
            text.append("💭 ", style="#666666")
        else:
            text.append("! ", style="#ffa500")
        return text

    def _format_message(self) -> Text | Group:
        """Format the message with appropriate marker."""
        marker = self._get_marker()

        # Use markdown for assistant messages
        if self.use_markdown and self.message.role == MessageRole.ASSISTANT:
            try:
                md = Markdown(self.message.content, code_theme="monokai")
                return Group(marker, md)
            except Exception:
                # Fallback to plain text
                pass

        # Plain text for other messages
        text = Text()
        text.append_text(marker)
        text.append(self.message.content)
        return text

    def update_content(self, content: str) -> None:
        """Update the message content (for streaming)."""
        self.message.content = content
        if self._content_widget:
            self._content_widget.update(self._format_message())

    def append_content(self, content: str) -> None:
        """Append to the message content (for streaming)."""
        self.message.content += content
        if self._content_widget:
            self._content_widget.update(self._format_message())

    def set_streaming(self, streaming: bool) -> None:
        """Set streaming state."""
        if streaming:
            self.add_class("streaming")
        else:
            self.remove_class("streaming")


class StreamingMessageWidget(Static):
    """Widget for displaying a streaming message with typing indicator."""

    DEFAULT_CSS = """
    StreamingMessageWidget {
        height: auto;
        padding: 0 2 1 2;
    }

    StreamingMessageWidget .content {
        color: #e0e0e0;
    }

    StreamingMessageWidget .typing-indicator {
        color: #5c8eff;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._content = ""
        self._is_streaming = True
        self._content_widget: Static | None = None

    def compose(self) -> ComposeResult:
        """Compose the streaming message display."""
        self._content_widget = Static(self._format_content(), id="stream-content")
        yield self._content_widget

    def _format_content(self) -> Text:
        """Format the streaming content."""
        text = Text()
        text.append("● ", style="#5c8eff")
        text.append(self._content)
        if self._is_streaming:
            text.append("▌", style="#5c8eff blink")
        return text

    def append_text(self, text: str) -> None:
        """Append text to the streaming content."""
        self._content += text
        if self._content_widget:
            self._content_widget.update(self._format_content())

    def finish_streaming(self) -> str:
        """Finish streaming and return the final content."""
        self._is_streaming = False
        if self._content_widget:
            self._content_widget.update(self._format_content())
        return self._content

    @property
    def content(self) -> str:
        """Get the current content."""
        return self._content


class MessageListWidget(VerticalScroll):
    """Scrollable container for messages."""

    DEFAULT_CSS = """
    MessageListWidget {
        height: 1fr;
        scrollbar-size: 1 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._messages: list[Message] = []
        self._streaming_widget: StreamingMessageWidget | None = None

    def add_message(self, message: Message) -> MessageWidget:
        """Add a message to the list."""
        self._messages.append(message)
        widget = MessageWidget(message)
        self.mount(widget)
        self.scroll_end(animate=False)
        return widget

    def start_streaming(self) -> StreamingMessageWidget:
        """Start a streaming message."""
        self._streaming_widget = StreamingMessageWidget()
        self.mount(self._streaming_widget)
        self.scroll_end(animate=False)
        return self._streaming_widget

    def append_to_stream(self, text: str) -> None:
        """Append text to the current streaming message."""
        if self._streaming_widget:
            self._streaming_widget.append_text(text)
            self.scroll_end(animate=False)

    def finish_streaming(self) -> Message | None:
        """Finish the current streaming message."""
        if self._streaming_widget:
            content = self._streaming_widget.finish_streaming()
            self._streaming_widget.remove()
            self._streaming_widget = None

            # Add as a regular message
            message = Message(role=MessageRole.ASSISTANT, content=content)
            self.add_message(message)
            return message
        return None

    def cancel_streaming(self) -> None:
        """Cancel the current streaming message."""
        if self._streaming_widget:
            self._streaming_widget.remove()
            self._streaming_widget = None

    def clear_messages(self) -> None:
        """Clear all messages."""
        self._messages.clear()
        self._streaming_widget = None
        self.remove_children()

    @property
    def messages(self) -> list[Message]:
        """Get all messages."""
        return self._messages.copy()

    @property
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self._streaming_widget is not None
