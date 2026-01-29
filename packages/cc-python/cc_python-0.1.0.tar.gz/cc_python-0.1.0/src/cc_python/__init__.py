"""CC Python - Claude Code style TUI application."""

from cc_python.app import CCPythonApp

__version__ = "0.1.0"


def main() -> None:
    """Run the CC Python application."""
    app = CCPythonApp()
    app.run()


__all__ = ["CCPythonApp", "main", "__version__"]
