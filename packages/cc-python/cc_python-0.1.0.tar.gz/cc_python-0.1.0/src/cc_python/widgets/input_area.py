"""Input area widget for user input."""

from pathlib import Path
from typing import TYPE_CHECKING, cast

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option

if TYPE_CHECKING:
    from cc_python.app import CCPythonApp


class InputAreaWidget(Static):
    """Input area with prompt marker."""

    DEFAULT_CSS = """
    InputAreaWidget {
        height: auto;
        padding: 0 2;
    }

    InputAreaWidget .input-container {
        height: auto;
    }

    InputAreaWidget .input-row {
        height: auto;
    }

    InputAreaWidget .prompt-marker {
        width: 2;
        color: #888888;
    }

    InputAreaWidget Input {
        border: none;
        background: transparent;
        width: 1fr;
        padding: 0;
    }

    InputAreaWidget Input:focus {
        border: none;
    }

    InputAreaWidget .suggestions {
        margin-left: 2;
        border: solid #333333;
        height: auto;
        max-height: 6;
    }

    InputAreaWidget .suggestions.hidden {
        display: none;
    }
    """

    class Submitted(Message):
        """Message sent when input is submitted."""

        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    def __init__(self, **kwargs) -> None:
        """Initialize the input area."""
        super().__init__(**kwargs)
        self._current_files: list[str] = []
        self._git_files_loaded = False

    def _get_all_commands(self) -> list:
        """Get all registered commands from the app."""
        try:
            app = cast("CCPythonApp", self.app)
            return app.command_registry.get_all_commands()
        except (AttributeError, TypeError):
            return []

    def _get_all_files(self) -> list[str]:
        """Get all files in git workspace."""
        if self._git_files_loaded:
            return self._current_files

        try:
            import git

            # Try to find git repository from current working directory
            try:
                repo = git.Repo(Path.cwd(), search_parent_directories=True)
            except git.InvalidGitRepositoryError:
                return []

            # Get all tracked files
            files = []
            for item in repo.tree():
                if item.type == "blob":
                    # Convert to relative path from repo root
                    rel_path = item.path
                    files.append(rel_path)
                elif item.type == "tree":
                    # For directories, add trailing slash
                    rel_path = item.path + "/"
                    files.append(rel_path)

            self._current_files = sorted(files)
            self._git_files_loaded = True
            return self._current_files

        except ImportError:
            # GitPython not available, fallback to local directory
            return []
        except Exception:
            return []

    def _suggestion_list(self) -> OptionList:
        """Get the suggestion list widget."""
        return self.query_one("#suggestion-list", OptionList)

    def _show_suggestions(self, options: list[Option]) -> None:
        """Show suggestions in the dropdown list."""
        suggestion_list = self._suggestion_list()
        suggestion_list.clear_options()
        if options:
            suggestion_list.add_options(options)
            suggestion_list.highlighted = 0
            suggestion_list.remove_class("hidden")
        else:
            suggestion_list.add_class("hidden")

    def _hide_suggestions(self) -> None:
        """Hide the suggestions dropdown."""
        suggestion_list = self._suggestion_list()
        suggestion_list.clear_options()
        suggestion_list.add_class("hidden")

    def _build_command_options(self, search: str) -> list[Option]:
        """Build command options for the dropdown."""
        commands = self._get_all_commands()
        options: list[Option] = []
        seen: set[str] = set()

        for cmd in sorted(commands, key=lambda c: c.name):
            if cmd.name.lower().startswith(search) and cmd.name not in seen:
                label = f"/{cmd.name} - {cmd.description}"
                options.append(Option(label, id=f"/{cmd.name}"))
                seen.add(cmd.name)
            for alias in cmd.aliases:
                if alias.lower().startswith(search) and alias not in seen:
                    label = f"/{alias} - {cmd.description}"
                    options.append(Option(label, id=f"/{alias}"))
                    seen.add(alias)

        return options

    def _build_file_options(self, search: str) -> list[Option]:
        """Build file options for the dropdown."""
        files = self._get_all_files()
        options: list[Option] = []

        for file_path in sorted(files):
            if file_path.lower().startswith(search):
                options.append(Option(f"@{file_path}", id=f"@{file_path}"))

        return options

    def compose(self) -> ComposeResult:
        """Compose the input area."""
        with Vertical(classes="input-container"):
            with Horizontal(classes="input-row"):
                yield Static("> ", classes="prompt-marker")
                yield Input(placeholder="", id="user-input")
            yield OptionList(id="suggestion-list", classes="suggestions hidden")

    def focus_input(self) -> None:
        """Focus the input field."""
        input_widget = self.query_one("#user-input", Input)
        input_widget.focus()

    def clear_input(self) -> None:
        """Clear the input field."""
        input_widget = self.query_one("#user-input", Input)
        input_widget.value = ""

    @on(Input.Submitted, "#user-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        value = event.value.strip()
        if value:
            self.post_message(self.Submitted(value))
            self.clear_input()
            self._hide_suggestions()

    @on(Input.Changed, "#user-input")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for autocomplete."""
        value = event.value
        if not value:
            self._hide_suggestions()
            return

        # Check for special prefixes
        if value.startswith("/"):
            search = value[1:].lower()
            self._show_suggestions(self._build_command_options(search))
        elif value.startswith("@"):
            search = value[1:].lower()
            self._show_suggestions(self._build_file_options(search))
        else:
            self._hide_suggestions()

    @on(OptionList.OptionSelected, "#suggestion-list")
    def on_suggestion_selected(self, event: OptionList.OptionSelected) -> None:
        """Apply the selected suggestion to the input."""
        if event.option.id is None:
            return

        input_widget = self.query_one("#user-input", Input)
        input_widget.value = event.option.id
        input_widget.cursor_position = len(input_widget.value)
        self._hide_suggestions()
        input_widget.focus()
