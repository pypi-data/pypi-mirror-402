"""Status bar widget for displaying hints and status."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


class StatusBarWidget(Static):
    """Status bar showing shortcuts and status information."""

    DEFAULT_CSS = """
    StatusBarWidget {
        height: 1;
        dock: bottom;
        background: #1a1a1a;
        padding: 0 2;
    }

    StatusBarWidget .status-container {
        height: 1;
        width: 100%;
    }

    StatusBarWidget .left-status {
        width: 1fr;
        color: #666666;
    }

    StatusBarWidget .center-status {
        width: auto;
        color: #555555;
        padding: 0 2;
    }

    StatusBarWidget .right-status {
        width: auto;
        color: #666666;
    }

    StatusBarWidget .key-hint {
        color: #888888;
    }

    StatusBarWidget .model-name {
        color: #5c8eff;
    }
    """

    def __init__(
        self,
        left_text: str = "? for shortcuts",
        right_text: str = "Thinking off (tab)",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._left_text = left_text
        self._center_text = ""
        self._right_text = right_text
        self._thinking_enabled = False
        self._model_name = ""
        self._token_count = 0

    def compose(self) -> ComposeResult:
        """Compose the status bar."""
        with Horizontal(classes="status-container"):
            yield Static(self._left_text, classes="left-status", id="left-status")
            yield Static(self._center_text, classes="center-status", id="center-status")
            yield Static(self._right_text, classes="right-status", id="right-status")

    def update_left(self, text: str) -> None:
        """Update left status text."""
        self._left_text = text
        self.query_one("#left-status", Static).update(text)

    def update_center(self, text: str) -> None:
        """Update center status text."""
        self._center_text = text
        self.query_one("#center-status", Static).update(text)

    def update_right(self, text: str) -> None:
        """Update right status text."""
        self._right_text = text
        self.query_one("#right-status", Static).update(text)

    def set_thinking(self, enabled: bool) -> None:
        """Update thinking status display."""
        self._thinking_enabled = enabled
        self._update_right_status()

    def set_model(self, model_name: str) -> None:
        """Set the current model name."""
        self._model_name = model_name
        self._update_center_status()

    def set_token_count(self, count: int) -> None:
        """Set the token count."""
        self._token_count = count
        self._update_center_status()

    def _update_center_status(self) -> None:
        """Update the center status with model and token info."""
        parts = []
        if self._model_name:
            # Shorten model name for display
            short_name = self._model_name.split("-")[0:2]
            parts.append("-".join(short_name))
        if self._token_count > 0:
            parts.append(f"{self._token_count:,} tokens")
        self.update_center(" | ".join(parts))

    def _update_right_status(self) -> None:
        """Update the right status with thinking mode."""
        status = "on" if self._thinking_enabled else "off"
        self.update_right(f"Thinking {status} (tab)")

    def set_processing(self, processing: bool, message: str = "") -> None:
        """Set processing state."""
        if processing:
            self.update_left(message or "Processing...")
        else:
            self.update_left("? for shortcuts")
