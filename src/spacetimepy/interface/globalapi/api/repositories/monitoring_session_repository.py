from spacetimepy.core.models import MonitoringSession
from spacetimepy.interface.globalapi.api.models.dto import MonitoringSessionDTO

from .base_repository import BaseRepository, sqlalchemy_to_dict


class MonitoringSessionRepository(BaseRepository):
    def get_session(self, session_id: int) -> MonitoringSessionDTO | None:
        """
        Retrieve a monitoring session by its ID.

        Args:
            session_id: The unique identifier of the session.

        Returns:
            MonitoringSessionDTO: The DTO representation of the session, or None if not found.
        """
        with self._get_session() as session:
            session_obj = session.query(MonitoringSession).get(session_id)
            if not session_obj:
                return None
            return MonitoringSessionDTO(**sqlalchemy_to_dict(session_obj))

    def list_sessions(self) -> list[MonitoringSessionDTO]:
        """
        List all sessions ordered by their starting time.

        Returns:
            list[MonitoringSessionDTO]: A list of DTO representations of all sessions.
        """
        with self._get_session() as session:
            sessions = (
                session.query(MonitoringSession)
                .order_by(MonitoringSession.start_time)
                .all()
            )
            return [MonitoringSessionDTO(**sqlalchemy_to_dict(s)) for s in sessions]
