from dataclasses import asdict

from spacetimepy.interface.mcp.api.models.dto import (
    MonitoringSessionDTO,
)
from spacetimepy.interface.mcp.api.models.models import (
    SessionSummaryRelations,
)
from spacetimepy.interface.mcp.api.repositories.function_call_repository import (
    FunctionCallRepository,
)
from spacetimepy.interface.mcp.api.repositories.monitoring_session_repository import (
    MonitoringSessionRepository,
)


class SessionService:
    """Service to manage sessions and their logic."""

    def __init__(
        self,
        session_repo: MonitoringSessionRepository,
        call_repo: FunctionCallRepository,
    ):
        self.session_repo = session_repo
        self.call_repo = call_repo

    # --- Direct calls to repository ---

    def get_session(self, session_id: int) -> MonitoringSessionDTO | None:
        """Retrieve a session by its ID.

        Args:
            session_id: The ID of the session to retrieve.

        Returns:
            The MonitoringSessionDTO if found, otherwise None.
        """
        return self.session_repo.get_session(session_id)

    def list_sessions(self) -> list[MonitoringSessionDTO]:
        """List all sessions.

        Returns:
            A list of all MonitoringSessionDTOs.
        """
        return self.session_repo.list_sessions()

    # --- Domain logic ---

    def get_sessions_relationships(self) -> list[SessionSummaryRelations]:
        """Analyze parent/child relationships between sessions.

        Returns:
            A list of SessionDetailsRelations representing the relationships between sessions.
        """
        sessions_data = self.list_sessions()
        session_relationships: dict[int, SessionSummaryRelations] = {
            session.id: SessionSummaryRelations.from_dict(asdict(session))
            for session in sessions_data
        }

        parent_call_to_info: dict[int, tuple[int, int]] = {}
        size = 100

        for session in sessions_data:
            for calls_batch in self.call_repo.get_all_calls_by_session_paginated(
                session.id, size
            ):
                for call in calls_batch:
                    if not call.parent_call_id:
                        continue

                    if call.parent_call_id in parent_call_to_info:
                        parent_session_id, parent_call_order = parent_call_to_info[
                            call.parent_call_id
                        ]
                    else:
                        parent_call = self.call_repo.get_call(call.parent_call_id)
                        if parent_call:
                            parent_session_id = parent_call.session_id
                            parent_call_order = parent_call.order_in_session
                            parent_call_to_info[call.parent_call_id] = (
                                parent_session_id,
                                parent_call_order,
                            )
                        else:
                            continue

                    if parent_session_id != session.id:
                        session_relationships[
                            session.id
                        ].relations.parent_session_id = parent_session_id
                        session_relationships[
                            session.id
                        ].relations.branch_point_call_id = call.parent_call_id
                        session_relationships[
                            session.id
                        ].relations.branch_point_index = parent_call_order

        for _, s_details in session_relationships.items():
            if s_details.relations.parent_session_id:
                parent_id = s_details.relations.parent_session_id
                if parent_id in session_relationships:
                    session_relationships[parent_id].relations.child_sessions.append(
                        s_details.id
                    )

        return list(session_relationships.values())
