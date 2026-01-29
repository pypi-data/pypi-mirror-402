"""Session-related commands for CC Python."""

from typing import TYPE_CHECKING

from .registry import Command, CommandResult

if TYPE_CHECKING:
    from cc_python.app import CCPythonApp


class SessionsCommand(Command):
    """List saved sessions."""

    name = "sessions"
    description = "List saved conversation sessions"
    aliases = ["ls"]

    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """List all saved sessions."""
        from cc_python.conversation import SessionManager

        manager = SessionManager()
        sessions = manager.list_sessions()

        if not sessions:
            return CommandResult(
                success=True,
                message="No saved sessions found.",
            )

        lines = ["Saved sessions:", ""]
        for session in sessions[:10]:  # Show last 10
            lines.append(
                f"  {session['id']} - {session['name']} ({session['updated_at'][:10]})"
            )

        if len(sessions) > 10:
            lines.append(f"  ... and {len(sessions) - 10} more")

        lines.append("")
        lines.append("Use /resume <session_id> to restore a session")
        return CommandResult(success=True, message="\n".join(lines))


class ResumeCommand(Command):
    """Resume a saved session."""

    name = "resume"
    description = "Resume a saved conversation session"
    aliases = ["r"]

    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """Resume a saved session."""
        if not args:
            return CommandResult(
                success=False,
                message="Usage: /resume <session_id>\nUse /sessions to list available sessions.",
            )

        session_id = args[0]

        from cc_python.conversation import SessionManager

        manager = SessionManager()

        try:
            session = manager.load_session(session_id)
            return CommandResult(
                success=True,
                message=f"Resumed session: {session.name} ({len(session.history.turns)} messages)",
                clear_messages=True,  # Clear current messages first
            )
        except FileNotFoundError:
            return CommandResult(
                success=False,
                message=f"Session not found: {session_id}",
            )


class SaveCommand(Command):
    """Save the current session."""

    name = "save"
    description = "Save the current conversation session"
    aliases = []

    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """Save the current session."""
        from cc_python.screens import ChatScreen

        screen = app.screen
        if not isinstance(screen, ChatScreen):
            return CommandResult(
                success=False,
                message="Cannot save: not in chat screen",
            )

        # Update session name if provided
        if args:
            screen.session.name = " ".join(args)

        from cc_python.conversation import SessionManager

        manager = SessionManager()
        manager._current_session = screen.session
        path = manager.save_session()

        return CommandResult(
            success=True,
            message=f"Session saved: {screen.session.id} ({path.name})",
        )


class ContextCommand(Command):
    """Show current context information."""

    name = "context"
    description = "Show current conversation context"
    aliases = ["ctx"]

    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """Show context information."""
        from cc_python.screens import ChatScreen

        screen = app.screen
        if not isinstance(screen, ChatScreen):
            return CommandResult(
                success=False,
                message="Cannot show context: not in chat screen",
            )

        history = screen.history
        lines = [
            "Current Context:",
            "",
            f"  Messages: {len(history.turns)}",
            f"  Estimated tokens: ~{history.estimate_tokens():,}",
        ]

        if history.system_context:
            lines.append(f"  System context: {len(history.system_context)} chars")

        # Show project context info
        if hasattr(screen, "_project_context") and screen._project_context.has_context:
            lines.append(f"  Project context: {screen._project_context._context_file}")

        return CommandResult(success=True, message="\n".join(lines))


class CompactCommand(Command):
    """Compact the conversation history."""

    name = "compact"
    description = "Summarize and compact conversation history"
    aliases = []

    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """Compact the conversation history."""
        from cc_python.screens import ChatScreen

        screen = app.screen
        if not isinstance(screen, ChatScreen):
            return CommandResult(
                success=False,
                message="Cannot compact: not in chat screen",
            )

        history = screen.history
        before_count = len(history.turns)
        before_tokens = history.estimate_tokens()

        # Trim to fit
        removed = history.trim_to_fit(target_tokens=50000)

        after_count = len(history.turns)
        after_tokens = history.estimate_tokens()

        return CommandResult(
            success=True,
            message=f"Compacted: {before_count} → {after_count} messages, ~{before_tokens:,} → ~{after_tokens:,} tokens",
        )


class InitCommand(Command):
    """Initialize project with CLAUDE.md."""

    name = "init"
    description = "Create a CLAUDE.md file for project context"
    aliases = []

    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """Create CLAUDE.md file."""
        from pathlib import Path

        from cc_python.conversation import ProjectContext

        context = ProjectContext()

        # Check if file already exists
        for filename in context.CONTEXT_FILES:
            if (Path.cwd() / filename).exists():
                return CommandResult(
                    success=False,
                    message=f"Context file already exists: {filename}",
                )

        # Create default file
        path = context.create_default_context_file()
        return CommandResult(
            success=True,
            message=f"Created: {path}\nEdit this file to provide project context to the AI.",
        )
