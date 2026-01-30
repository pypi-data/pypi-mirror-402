"""Session management - storing and loading SDK session IDs."""

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List


@dataclass
class Session:
    """Session data storing SDK session ID for resume functionality."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sdk_session_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    working_directory: str = field(default_factory=lambda: str(Path.cwd()))
    model: str = "claude-sonnet-4-20250514"

    def update(self, sdk_session_id: str):
        """Update session with new SDK session ID."""
        self.sdk_session_id = sdk_session_id
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create Session from dictionary."""
        return cls(**data)


class SessionManager:
    """Manages session persistence."""

    def __init__(self, session_dir: str = ".assiworks/sessions"):
        self.session_dir = Path(session_dir)

    def _ensure_dir(self):
        """Ensure session directory exists."""
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, session_id: str) -> Path:
        """Get file path for session."""
        return self.session_dir / f"{session_id}.json"

    def save(self, session: Session):
        """Save session to disk."""
        self._ensure_dir()
        path = self._get_path(session.id)
        with open(path, "w") as f:
            json.dump(session.to_dict(), f, indent=2)

    def load(self, session_id: str) -> Optional[Session]:
        """Load session from disk."""
        path = self._get_path(session_id)
        if not path.exists():
            return None

        with open(path, "r") as f:
            data = json.load(f)
        return Session.from_dict(data)

    def delete(self, session_id: str) -> bool:
        """Delete session from disk."""
        path = self._get_path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_sessions(self) -> List[Session]:
        """List all saved sessions."""
        self._ensure_dir()
        sessions = []
        for path in self.session_dir.glob("*.json"):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                sessions.append(Session.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue

        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions

    def get_latest(self) -> Optional[Session]:
        """Get most recently updated session."""
        sessions = self.list_sessions()
        return sessions[0] if sessions else None
