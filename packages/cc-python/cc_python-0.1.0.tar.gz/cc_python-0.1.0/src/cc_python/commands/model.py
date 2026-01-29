"""Model-related commands for CC Python."""

from typing import TYPE_CHECKING

from .registry import Command, CommandResult

if TYPE_CHECKING:
    from cc_python.app import CCPythonApp


class ModelCommand(Command):
    """Change or display the current model."""

    name = "model"
    description = "Change or display the current AI model"
    aliases = ["m"]

    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """Change or show the current model."""
        settings = app.settings

        if not args:
            # Show current model and available models
            lines = [
                f"Current model: {settings.model}",
                "",
                "Available models:",
            ]
            for model in settings.AVAILABLE_MODELS:
                marker = "→" if model == settings.model else " "
                lines.append(f"  {marker} {model}")
            lines.append("")
            lines.append("Usage: /model <model_name>")
            return CommandResult(success=True, message="\n".join(lines))

        # Set new model
        new_model = args[0]

        # Check for partial match
        matching = [m for m in settings.AVAILABLE_MODELS if new_model.lower() in m.lower()]

        if len(matching) == 1:
            new_model = matching[0]
        elif len(matching) > 1:
            return CommandResult(
                success=False,
                message=f"Ambiguous model name. Matches: {', '.join(matching)}",
            )
        elif new_model not in settings.AVAILABLE_MODELS:
            return CommandResult(
                success=False,
                message=f"Unknown model: {new_model}\nAvailable: {', '.join(settings.AVAILABLE_MODELS)}",
            )

        settings.model = new_model
        return CommandResult(
            success=True,
            message=f"Model changed to: {new_model}",
        )


class ConfigCommand(Command):
    """Display or modify configuration."""

    name = "config"
    description = "Display or modify configuration settings"
    aliases = ["cfg"]

    def execute(self, app: "CCPythonApp", args: list[str]) -> CommandResult:
        """Show or modify configuration."""
        settings = app.settings

        if not args:
            # Show current configuration
            config = settings.to_dict()
            lines = ["Current configuration:", ""]
            for key, value in config.items():
                lines.append(f"  {key}: {value}")
            lines.append("")
            lines.append("Usage: /config <key> <value>")
            return CommandResult(success=True, message="\n".join(lines))

        if len(args) < 2:
            return CommandResult(
                success=False,
                message="Usage: /config <key> <value>",
            )

        key = args[0]
        value = " ".join(args[1:])

        # Handle specific settings
        if key == "max_tokens":
            try:
                settings.max_tokens = int(value)
                return CommandResult(
                    success=True,
                    message=f"max_tokens set to: {settings.max_tokens}",
                )
            except ValueError:
                return CommandResult(
                    success=False,
                    message="max_tokens must be an integer",
                )

        elif key == "thinking_budget":
            try:
                settings.thinking_budget = int(value)
                return CommandResult(
                    success=True,
                    message=f"thinking_budget set to: {settings.thinking_budget}",
                )
            except ValueError:
                return CommandResult(
                    success=False,
                    message="thinking_budget must be an integer",
                )

        elif key in ("auto_approve_read", "auto_approve_write", "auto_approve_shell"):
            bool_value = value.lower() in ("true", "1", "yes", "on")
            setattr(settings, key, bool_value)
            return CommandResult(
                success=True,
                message=f"{key} set to: {bool_value}",
            )

        else:
            return CommandResult(
                success=False,
                message=f"Unknown configuration key: {key}",
            )
