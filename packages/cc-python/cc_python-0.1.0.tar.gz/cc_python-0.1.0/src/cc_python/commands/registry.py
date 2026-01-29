"""Command registry for managing slash commands."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cc_python.app import CCPythonApp


@dataclass
class CommandResult:
    """Result of executing a command."""

    success: bool
    message: str = ""
    should_exit: bool = False
    clear_messages: bool = False


class Command(ABC):
    """Base class for all commands."""

    name: str
    description: str
    aliases: list[str] = []

    @abstractmethod
    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """Execute the command."""
        pass


class CommandRegistry:
    """Registry for managing and executing commands."""

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        """Register a command."""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command

    def get(self, name: str) -> Command | None:
        """Get a command by name or alias."""
        return self._commands.get(name)

    def execute(self, app: "CCPythonApp", input_text: str) -> CommandResult | None:
        """Parse and execute a command from input text.

        Returns None if input is not a command.
        """
        if not input_text.startswith("/"):
            return None

        parts = input_text[1:].split()
        if not parts:
            return CommandResult(success=False, message="Empty command")

        command_name = parts[0].lower()
        args = parts[1:]

        command = self.get(command_name)
        if command is None:
            return CommandResult(
                success=False, message=f"Unknown command: /{command_name}"
            )

        return command.execute(app, args)

    def get_all_commands(self) -> list[Command]:
        """Get all unique registered commands."""
        seen = set()
        commands = []
        for cmd in self._commands.values():
            if cmd.name not in seen:
                seen.add(cmd.name)
                commands.append(cmd)
        return commands
