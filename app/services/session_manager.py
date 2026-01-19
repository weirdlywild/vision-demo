import time
import uuid
from typing import Dict, List, Optional
from threading import Lock
from app.config import settings


class Session:
    """Represents a user session with diagnosis history."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.diagnosis_history: List[Dict] = []
        self.context: str = ""

    def add_diagnosis(self, image_hash: str, diagnosis: Dict) -> None:
        """Add a diagnosis to session history."""
        self.diagnosis_history.append({
            "image_hash": image_hash,
            "diagnosis": diagnosis,
            "timestamp": time.time()
        })

        # Keep only last N diagnoses
        if len(self.diagnosis_history) > settings.max_session_history:
            self.diagnosis_history = self.diagnosis_history[-settings.max_session_history:]

        # Update context summary
        self._update_context()

    def _update_context(self) -> None:
        """Update context summary from diagnosis history."""
        if not self.diagnosis_history:
            self.context = ""
            return

        # Get the most recent diagnosis
        latest = self.diagnosis_history[-1]['diagnosis']

        # Create summary
        object_identified = latest.get('object_identified', 'unknown object')
        failure_mode = latest.get('failure_mode', 'unknown issue')
        steps_count = len(latest.get('repair_steps', []))

        self.context = (
            f"Object: {object_identified}\n"
            f"Issue: {failure_mode}\n"
            f"Steps provided: {steps_count}"
        )

    def get_latest_diagnosis(self) -> Optional[Dict]:
        """Get the most recent diagnosis."""
        if not self.diagnosis_history:
            return None
        return self.diagnosis_history[-1]['diagnosis']

    def is_expired(self) -> bool:
        """Check if session has expired based on TTL."""
        ttl_seconds = settings.session_ttl_minutes * 60
        return (time.time() - self.last_accessed) > ttl_seconds

    def touch(self) -> None:
        """Update last accessed time."""
        self.last_accessed = time.time()


class SessionManager:
    """Thread-safe session manager for multi-turn conversations."""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._lock = Lock()

    def create_session(self) -> str:
        """
        Create a new session.

        Returns:
            Session ID (UUID)
        """
        session_id = str(uuid.uuid4())

        with self._lock:
            self._sessions[session_id] = Session(session_id)

        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session object or None if not found/expired
        """
        with self._lock:
            session = self._sessions.get(session_id)

            if session is None:
                return None

            # Check if expired
            if session.is_expired():
                del self._sessions[session_id]
                return None

            # Update access time
            session.touch()
            return session

    def update_session(self, session_id: str, image_hash: str, diagnosis: Dict) -> None:
        """
        Update session with new diagnosis.

        Args:
            session_id: Session ID
            image_hash: Hash of diagnosed image
            diagnosis: Diagnosis result
        """
        with self._lock:
            session = self._sessions.get(session_id)

            if session is None:
                # Create new session if it doesn't exist
                session = Session(session_id)
                self._sessions[session_id] = session

            session.add_diagnosis(image_hash, diagnosis)
            session.touch()

    def get_context(self, session_id: str) -> str:
        """
        Get context summary for session.

        Args:
            session_id: Session ID

        Returns:
            Context string
        """
        session = self.get_session(session_id)
        return session.context if session else ""

    def get_latest_diagnosis(self, session_id: str) -> Optional[Dict]:
        """
        Get the most recent diagnosis for a session.

        Args:
            session_id: Session ID

        Returns:
            Latest diagnosis or None
        """
        session = self.get_session(session_id)
        return session.get_latest_diagnosis() if session else None

    def cleanup_expired(self) -> int:
        """
        Remove expired sessions.

        Returns:
            Number of sessions removed
        """
        removed = 0

        with self._lock:
            expired_ids = [
                session_id
                for session_id, session in self._sessions.items()
                if session.is_expired()
            ]

            for session_id in expired_ids:
                del self._sessions[session_id]
                removed += 1

        return removed

    def get_session_count(self) -> int:
        """Get current number of active sessions."""
        with self._lock:
            return len(self._sessions)


# Global session manager instance
session_manager = SessionManager()
