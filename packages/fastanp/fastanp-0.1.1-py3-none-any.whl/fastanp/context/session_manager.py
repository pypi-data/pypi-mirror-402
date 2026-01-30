"""Session 管理器。"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from .session import Session

logger = logging.getLogger(__name__)


class SessionManager:
    """负责 Session 生命周期与存储。"""

    def __init__(
        self,
        session_timeout_minutes: int = 60,
        cleanup_interval_minutes: int = 10,
    ):
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self.last_cleanup = datetime.now()

    def _generate_session_id(self, did: str) -> str:
        return hashlib.sha256(did.encode()).hexdigest()

    def _cleanup_if_needed(self) -> None:
        """定期清理过期 Session。"""
        now = datetime.now()
        if now - self.last_cleanup < self.cleanup_interval:
            return

        expired_ids = [
            session_id
            for session_id, session in self.sessions.items()
            if now - session.last_accessed > self.session_timeout
        ]
        for session_id in expired_ids:
            logger.debug("Removing expired session: %s", session_id[:8])
            self.sessions.pop(session_id, None)

        self.last_cleanup = now

    def get_or_create(self, did: str, anonymous: bool = False) -> Session:
        """基于 DID 创建或返回 Session。"""
        self._cleanup_if_needed()
        session_id = self._generate_session_id(did)

        session = self.sessions.get(session_id)
        if session:
            session.touch()
            logger.debug("Reusing session %s for DID %s", session_id[:8], did)
            return session

        session = Session(session_id, did)
        self.sessions[session_id] = session
        status = "anonymous" if anonymous else "authenticated"
        logger.info(
            "Created new session %s for DID %s (%s)", session_id[:8], did, status
        )
        return session

    def get(self, session_id: str) -> Optional[Session]:
        session = self.sessions.get(session_id)
        if session:
            session.touch()
        return session

    def clear_all(self) -> None:
        """Clear all existing sessions."""
        self.sessions.clear()
        self.last_cleanup = datetime.now()

    def remove(self, session_id: str) -> None:
        if session_id in self.sessions:
            logger.info("Removing session %s", session_id[:8])
            self.sessions.pop(session_id, None)
