"""Header widget displaying app info."""

import os
from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from cc_python.config import get_settings


class HeaderWidget(Static):
    """Header widget showing app logo, version, model, and working directory."""

    DEFAULT_CSS = """
    HeaderWidget {
        height: auto;
        padding: 1 2;
    }

    HeaderWidget .header-container {
        height: auto;
    }

    HeaderWidget .logo {
        width: auto;
        color: #ff6b9d;
    }

    HeaderWidget .info {
        padding-left: 2;
    }

    HeaderWidget .app-name {
        color: #ffffff;
        text-style: bold;
    }

    HeaderWidget .version {
        color: #888888;
    }

    HeaderWidget .model-info {
        color: #5c8eff;
    }

    HeaderWidget .directory {
        color: #888888;
    }

    HeaderWidget .api-status {
        color: #00aa00;
    }

    HeaderWidget .api-status-error {
        color: #ff4444;
    }
    """

    def __init__(
        self,
        app_name: str = "CC Python",
        version: str = "v0.1.0",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.app_name = app_name
        self.version = version
        self._settings = get_settings()
        self._info_widget: Static | None = None

    def compose(self) -> ComposeResult:
        """Compose the header layout."""
        with Horizontal(classes="header-container"):
            yield Static(self._get_logo(), classes="logo")
            self._info_widget = Static(self._get_info(), classes="info", id="header-info")
            yield self._info_widget

    def _get_logo(self) -> Text:
        """Get the pixel art logo."""
        # Simple pixel art logo similar to Claude Code
        logo_lines = [
            "╭─────╮",
            "│ ◉ ◉ │",
            "│  ▽  │",
            "╰─────╯",
        ]
        return Text("\n".join(logo_lines), style="bold #ff6b9d")

    def _get_info(self) -> Text:
        """Get the app info text."""
        cwd = Path.cwd()
        text = Text()

        # App name and version
        text.append(self.app_name, style="bold white")
        text.append(f" {self.version}", style="#888888")

        # Model info
        text.append(" · ", style="#666666")
        model_name = self._settings.model
        # Shorten model name for display
        short_model = model_name.replace("claude-", "").replace("-20250514", "")
        text.append(short_model, style="#5c8eff")

        # API status
        text.append(" · ", style="#666666")
        if self._settings.has_api_key:
            text.append("●", style="#00aa00")
        else:
            text.append("○", style="#ff4444")

        # Working directory
        text.append("\n")
        text.append(str(cwd), style="#888888")

        return text

    def update_info(self) -> None:
        """Update the info display."""
        if self._info_widget:
            self._info_widget.update(self._get_info())

    def set_model(self, model: str) -> None:
        """Update the displayed model."""
        self._settings.model = model
        self.update_info()
