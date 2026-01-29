"""Command system for CC Python."""

from .registry import CommandRegistry, Command, CommandResult
from .base import HelpCommand, ClearCommand, ExitCommand
from .model import ModelCommand, ConfigCommand
from .session import (
    SessionsCommand,
    ResumeCommand,
    SaveCommand,
    ContextCommand,
    CompactCommand,
    InitCommand,
)

__all__ = [
    "CommandRegistry",
    "Command",
    "CommandResult",
    "HelpCommand",
    "ClearCommand",
    "ExitCommand",
    "ModelCommand",
    "ConfigCommand",
    "SessionsCommand",
    "ResumeCommand",
    "SaveCommand",
    "ContextCommand",
    "CompactCommand",
    "InitCommand",
]
