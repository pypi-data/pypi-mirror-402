"""Permission dialog widget for tool approval."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from cc_python.permissions import PermissionDecision, PermissionRequest


class PermissionDialog(ModalScreen[PermissionDecision]):
    """Modal dialog for requesting permission to execute a tool."""

    DEFAULT_CSS = """
    PermissionDialog {
        align: center middle;
    }

    PermissionDialog > Vertical {
        width: 70;
        height: auto;
        max-height: 80%;
        background: #2a2a2a;
        border: solid #5c8eff;
        padding: 1 2;
    }

    PermissionDialog .title {
        text-style: bold;
        color: #5c8eff;
        padding-bottom: 1;
    }

    PermissionDialog .content {
        height: auto;
        max-height: 20;
        overflow-y: auto;
        padding: 1;
        background: #1e1e1e;
        margin-bottom: 1;
    }

    PermissionDialog .tool-name {
        color: #ffa500;
        text-style: bold;
    }

    PermissionDialog .category {
        color: #888888;
    }

    PermissionDialog .params {
        color: #e0e0e0;
        padding-top: 1;
    }

    PermissionDialog .param-key {
        color: #5c8eff;
    }

    PermissionDialog .param-value {
        color: #e0e0e0;
    }

    PermissionDialog .buttons {
        height: auto;
        align: center middle;
        padding-top: 1;
    }

    PermissionDialog Button {
        margin: 0 1;
    }

    PermissionDialog .allow-btn {
        background: #2e7d32;
    }

    PermissionDialog .allow-btn:hover {
        background: #388e3c;
    }

    PermissionDialog .deny-btn {
        background: #c62828;
    }

    PermissionDialog .deny-btn:hover {
        background: #d32f2f;
    }

    PermissionDialog .always-btn {
        background: #1565c0;
    }

    PermissionDialog .always-btn:hover {
        background: #1976d2;
    }

    PermissionDialog .hint {
        color: #666666;
        text-align: center;
        padding-top: 1;
    }
    """

    BINDINGS = [
        ("y", "allow", "Allow"),
        ("n", "deny", "Deny"),
        ("a", "allow_always", "Always Allow"),
        ("s", "allow_session", "Allow for Session"),
        ("escape", "deny", "Deny"),
    ]

    def __init__(self, request: PermissionRequest, **kwargs) -> None:
        super().__init__(**kwargs)
        self.request = request

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        with Vertical():
            yield Label("Permission Required", classes="title")

            with Vertical(classes="content"):
                yield Static(f"Tool: {self.request.tool_name}", classes="tool-name")
                yield Static(f"Category: {self.request.tool_category}", classes="category")

                # Show parameters
                yield Static("Parameters:", classes="params")
                for key, value in self.request.params.items():
                    str_value = str(value)
                    if len(str_value) > 80:
                        str_value = str_value[:80] + "..."
                    yield Static(f"  {key}: {str_value}")

            with Horizontal(classes="buttons"):
                yield Button("Allow (y)", id="allow", classes="allow-btn")
                yield Button("Deny (n)", id="deny", classes="deny-btn")
                yield Button("Always (a)", id="always", classes="always-btn")
                yield Button("Session (s)", id="session")

            yield Static(
                "Press y/n/a/s or click a button",
                classes="hint",
            )

    @on(Button.Pressed, "#allow")
    def on_allow(self) -> None:
        """Handle allow button."""
        self.dismiss(PermissionDecision.ALLOW)

    @on(Button.Pressed, "#deny")
    def on_deny(self) -> None:
        """Handle deny button."""
        self.dismiss(PermissionDecision.DENY)

    @on(Button.Pressed, "#always")
    def on_always(self) -> None:
        """Handle always allow button."""
        self.dismiss(PermissionDecision.ALLOW_ALWAYS)

    @on(Button.Pressed, "#session")
    def on_session(self) -> None:
        """Handle session allow button."""
        self.dismiss(PermissionDecision.ALLOW_SESSION)

    def action_allow(self) -> None:
        """Allow action."""
        self.dismiss(PermissionDecision.ALLOW)

    def action_deny(self) -> None:
        """Deny action."""
        self.dismiss(PermissionDecision.DENY)

    def action_allow_always(self) -> None:
        """Always allow action."""
        self.dismiss(PermissionDecision.ALLOW_ALWAYS)

    def action_allow_session(self) -> None:
        """Session allow action."""
        self.dismiss(PermissionDecision.ALLOW_SESSION)
