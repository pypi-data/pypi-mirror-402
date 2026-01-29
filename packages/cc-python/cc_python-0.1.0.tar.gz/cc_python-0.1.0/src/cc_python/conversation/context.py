"""Project context management for CC Python."""

from pathlib import Path
from typing import Any


class ProjectContext:
    """Manages project-specific context like CLAUDE.md files."""

    CONTEXT_FILES = [
        "CLAUDE.md",
        ".claude/CLAUDE.md",
        "claude.md",
        ".claude.md",
    ]

    def __init__(self, working_directory: Path | None = None) -> None:
        """Initialize project context."""
        self._working_dir = working_directory or Path.cwd()
        self._context_content: str = ""
        self._context_file: Path | None = None
        self._project_info: dict[str, Any] = {}

    @property
    def working_directory(self) -> Path:
        """Get the working directory."""
        return self._working_dir

    @working_directory.setter
    def working_directory(self, path: Path) -> None:
        """Set the working directory and reload context."""
        self._working_dir = path
        self.load_context()

    @property
    def context_content(self) -> str:
        """Get the loaded context content."""
        return self._context_content

    @property
    def has_context(self) -> bool:
        """Check if context is loaded."""
        return bool(self._context_content)

    def load_context(self) -> bool:
        """Load context from CLAUDE.md or similar files.

        Returns True if context was loaded successfully.
        """
        self._context_content = ""
        self._context_file = None

        for filename in self.CONTEXT_FILES:
            context_path = self._working_dir / filename
            if context_path.exists() and context_path.is_file():
                try:
                    self._context_content = context_path.read_text(encoding="utf-8")
                    self._context_file = context_path
                    return True
                except (OSError, UnicodeDecodeError):
                    continue

        return False

    def get_system_prompt_addition(self) -> str:
        """Get context as addition to system prompt."""
        if not self._context_content:
            return ""

        return f"""
## Project Context (from {self._context_file.name if self._context_file else 'CLAUDE.md'})

{self._context_content}
"""

    def analyze_project(self) -> dict[str, Any]:
        """Analyze the project structure and return info."""
        info: dict[str, Any] = {
            "working_directory": str(self._working_dir),
            "has_context_file": self._context_file is not None,
            "context_file": str(self._context_file) if self._context_file else None,
        }

        # Check for common project files
        project_markers = {
            "python": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile"],
            "node": ["package.json", "package-lock.json", "yarn.lock"],
            "rust": ["Cargo.toml"],
            "go": ["go.mod"],
            "ruby": ["Gemfile"],
            "java": ["pom.xml", "build.gradle"],
        }

        detected_languages = []
        for lang, markers in project_markers.items():
            for marker in markers:
                if (self._working_dir / marker).exists():
                    detected_languages.append(lang)
                    break

        info["detected_languages"] = detected_languages

        # Check for git
        info["is_git_repo"] = (self._working_dir / ".git").exists()

        # Count files
        try:
            files = list(self._working_dir.rglob("*"))
            info["total_files"] = len([f for f in files if f.is_file()])
        except (OSError, PermissionError):
            info["total_files"] = -1

        self._project_info = info
        return info

    def get_project_summary(self) -> str:
        """Get a summary of the project for context."""
        if not self._project_info:
            self.analyze_project()

        lines = [
            f"Working Directory: {self._project_info['working_directory']}",
        ]

        if self._project_info.get("detected_languages"):
            langs = ", ".join(self._project_info["detected_languages"])
            lines.append(f"Detected Languages: {langs}")

        if self._project_info.get("is_git_repo"):
            lines.append("Git Repository: Yes")

        if self._project_info.get("has_context_file"):
            lines.append(f"Context File: {self._project_info['context_file']}")

        return "\n".join(lines)

    def create_default_context_file(self) -> Path:
        """Create a default CLAUDE.md file."""
        content = """# Project Context

## Overview
<!-- Describe your project here -->

## Tech Stack
<!-- List the main technologies used -->

## Conventions
<!-- Describe coding conventions, style guides, etc. -->

## Important Files
<!-- List important files and their purposes -->

## Notes
<!-- Any other notes for the AI assistant -->
"""
        context_path = self._working_dir / "CLAUDE.md"
        context_path.write_text(content, encoding="utf-8")
        self._context_file = context_path
        self._context_content = content
        return context_path
