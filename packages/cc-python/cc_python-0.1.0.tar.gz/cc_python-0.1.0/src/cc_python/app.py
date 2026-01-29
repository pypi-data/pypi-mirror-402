"""Main application for CC Python TUI."""

from textual.app import App
from textual.binding import Binding

from cc_python.commands import (
    CommandRegistry,
    ClearCommand,
    ExitCommand,
    HelpCommand,
    ModelCommand,
    ConfigCommand,
    SessionsCommand,
    ResumeCommand,
    SaveCommand,
    ContextCommand,
    CompactCommand,
    InitCommand,
)
from cc_python.config import get_settings
from cc_python.permissions import PermissionManager
from cc_python.screens import ChatScreen
from cc_python.tools import (
    ToolManager,
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    SearchFilesTool,
    GlobTool,
    BashTool,
    GitStatusTool,
    GitDiffTool,
    GitLogTool,
    GitCommitTool,
    GitBranchTool,
    GitCheckoutTool,
)
from cc_python.tools.file_tools import EditFileTool
from cc_python.tools.shell_tools import PythonTool


class CCPythonApp(App):
    """CC Python Terminal User Interface Application."""

    TITLE = "CC Python"

    CSS = """
    Screen {
        background: #1e1e1e;
    }

    /* Global text styling */
    Static {
        color: #e0e0e0;
    }

    /* Scrollbar styling */
    Scrollbar {
        background: #2a2a2a;
    }

    ScrollBar > .scrollbar--bar {
        background: #444444;
    }

    ScrollBar > .scrollbar--bar:hover {
        background: #555555;
    }
    """

    BINDINGS = [
        Binding("tab", "toggle_thinking", "Toggle thinking", show=False),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("ctrl+l", "clear_screen", "Clear", show=False),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.settings = get_settings()
        self.command_registry = CommandRegistry()
        self.tool_manager = ToolManager()
        self.permission_manager = PermissionManager()
        self._register_commands()
        self._register_tools()

    def _register_commands(self) -> None:
        """Register all available commands."""
        # Basic commands
        self.command_registry.register(HelpCommand())
        self.command_registry.register(ClearCommand())
        self.command_registry.register(ExitCommand())

        # Model and config commands
        self.command_registry.register(ModelCommand())
        self.command_registry.register(ConfigCommand())

        # Session commands
        self.command_registry.register(SessionsCommand())
        self.command_registry.register(ResumeCommand())
        self.command_registry.register(SaveCommand())
        self.command_registry.register(ContextCommand())
        self.command_registry.register(CompactCommand())
        self.command_registry.register(InitCommand())

    def _register_tools(self) -> None:
        """Register all available tools."""
        # File tools
        self.tool_manager.register(ReadFileTool())
        self.tool_manager.register(WriteFileTool())
        self.tool_manager.register(EditFileTool())
        self.tool_manager.register(ListDirectoryTool())
        self.tool_manager.register(SearchFilesTool())
        self.tool_manager.register(GlobTool())

        # Shell tools
        self.tool_manager.register(BashTool())
        self.tool_manager.register(PythonTool())

        # Git tools
        self.tool_manager.register(GitStatusTool())
        self.tool_manager.register(GitDiffTool())
        self.tool_manager.register(GitLogTool())
        self.tool_manager.register(GitCommitTool())
        self.tool_manager.register(GitBranchTool())
        self.tool_manager.register(GitCheckoutTool())

    def on_mount(self) -> None:
        """Set up the app when mounted."""
        self.push_screen(ChatScreen())

    def action_toggle_thinking(self) -> None:
        """Toggle thinking mode."""
        screen = self.screen
        if isinstance(screen, ChatScreen):
            screen.toggle_thinking()

    def action_clear_screen(self) -> None:
        """Clear the message list."""
        screen = self.screen
        if isinstance(screen, ChatScreen):
            from cc_python.widgets import MessageListWidget

            screen.query_one("#message-list", MessageListWidget).clear_messages()
