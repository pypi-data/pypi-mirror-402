from pathlib import Path
from typing import Optional


class SessionState:
    """Holds the state for a single session."""

    def __init__(self):
        self.active_agent: Optional[str] = None
        self.project_root: Optional[Path] = None


class SessionManager:
    """Manages session state.
    Currently implements a Singleton pattern for local single-user context,
    but designed to be extensible for multi-session handling.
    """

    _instance = None
    _state = SessionState()

    @classmethod
    def get(cls) -> "SessionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def active_agent(self) -> Optional[str]:
        return self._state.active_agent

    @active_agent.setter
    def active_agent(self, agent: str) -> None:
        self._state.active_agent = agent

    @property
    def project_root(self) -> Optional[Path]:
        return self._state.project_root

    @project_root.setter
    def project_root(self, path: Path) -> None:
        self._state.project_root = path

    def clear(self) -> None:
        """Reset session state."""
        self._state = SessionState()
