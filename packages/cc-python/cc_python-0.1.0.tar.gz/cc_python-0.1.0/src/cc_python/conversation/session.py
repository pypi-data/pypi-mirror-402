"""Session management for CC Python."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from cc_python.config import get_settings
from cc_python.conversation.history import ConversationHistory


@dataclass
class Session:
    """A conversation session."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    working_directory: str = ""
    history: ConversationHistory = field(default_factory=ConversationHistory)

    def __post_init__(self) -> None:
        """Initialize session."""
        if not self.name:
            self.name = f"Session {self.id}"
        if not self.working_directory:
            self.working_directory = str(Path.cwd())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "working_directory": self.working_directory,
            "history": self.history.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Create from dictionary."""
        session = cls(
            id=data["id"],
            name=data.get("name", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            working_directory=data.get("working_directory", ""),
        )
        if "history" in data:
            session.history = ConversationHistory.from_dict(data["history"])
        return session

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()


class SessionManager:
    """Manages conversation sessions."""

    def __init__(self) -> None:
        """Initialize session manager."""
        self._settings = get_settings()
        self._current_session: Session | None = None

    @property
    def session_dir(self) -> Path:
        """Get session directory."""
        return self._settings.session_dir

    @property
    def current_session(self) -> Session | None:
        """Get current session."""
        return self._current_session

    def create_session(self, name: str = "") -> Session:
        """Create a new session."""
        session = Session(name=name)
        self._current_session = session
        return session

    def save_session(self, session: Session | None = None) -> Path:
        """Save a session to disk."""
        session = session or self._current_session
        if session is None:
            raise ValueError("No session to save")

        session.touch()
        session_file = self.session_dir / f"{session.id}.json"

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

        return session_file

    def load_session(self, session_id: str) -> Session:
        """Load a session from disk."""
        session_file = self.session_dir / f"{session_id}.json"

        if not session_file.exists():
            raise FileNotFoundError(f"Session not found: {session_id}")

        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = Session.from_dict(data)
        self._current_session = session
        return session

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all saved sessions."""
        sessions = []

        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append(
                    {
                        "id": data["id"],
                        "name": data.get("name", ""),
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                        "working_directory": data.get("working_directory", ""),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by updated_at descending
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        session_file = self.session_dir / f"{session_id}.json"

        if session_file.exists():
            session_file.unlink()
            if self._current_session and self._current_session.id == session_id:
                self._current_session = None
            return True
        return False

    def get_or_create_session(self) -> Session:
        """Get current session or create a new one."""
        if self._current_session is None:
            self._current_session = self.create_session()
        return self._current_session
