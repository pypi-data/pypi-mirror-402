"""Base commands for CC Python."""

from typing import TYPE_CHECKING

from .registry import Command, CommandResult

if TYPE_CHECKING:
    from cc_python.app import CCPythonApp


class HelpCommand(Command):
    """Display available commands."""

    name = "help"
    description = "Show available commands"
    aliases = ["h", "?"]

    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """Show help message with all available commands."""
        commands = app.command_registry.get_all_commands()
        lines = ["Available commands:", ""]
        for cmd in sorted(commands, key=lambda c: c.name):
            aliases = f" (aliases: {', '.join(cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"  /{cmd.name}{aliases} - {cmd.description}")
        return CommandResult(success=True, message="\n".join(lines))


class ClearCommand(Command):
    """Clear the message history."""

    name = "clear"
    description = "Clear conversation history"
    aliases = ["c", "cls"]

    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """Clear all messages."""
        return CommandResult(
            success=True, message="Conversation cleared.", clear_messages=True
        )


class ExitCommand(Command):
    """Exit the application."""

    name = "exit"
    description = "Exit the application"
    aliases = ["quit", "q"]

    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """Exit the app."""
        return CommandResult(success=True, message="Goodbye!", should_exit=True)
