import unittest
from dataclasses import dataclass
from datetime import datetime
from unittest.mock import MagicMock

from spacetimepy.interface.mcp.api.models.dto import MonitoringSessionDTO
from spacetimepy.interface.mcp.api.models.models import Relation
from spacetimepy.interface.mcp.api.services.session_service import SessionService


def create_session(id=1, name="S1"):
    return MonitoringSessionDTO(
        id=id,
        name=name,
        description="s_1",
        start_time=datetime.now(),
        end_time=datetime.now(),
        session_metadata={},
    )


@dataclass
class MockCall:
    id: int
    session_id: int
    parent_call_id: int | None
    order_in_session: int


class TestSessionService(unittest.TestCase):
    def test_get_session(self):
        mock_session_repo = MagicMock()
        mock_call_repo = MagicMock()
        service = SessionService(mock_session_repo, mock_call_repo)

        expected_session = create_session(id=1, name="Test Session")
        mock_session_repo.get_session.return_value = expected_session

        result = service.get_session(1)

        assert result == expected_session
        mock_session_repo.get_session.assert_called_once_with(1)

    def test_list_sessions(self):
        mock_session_repo = MagicMock()
        mock_call_repo = MagicMock()
        service = SessionService(mock_session_repo, mock_call_repo)

        expected_sessions = [
            create_session(id=1, name="S1"),
            create_session(id=2, name="S2"),
        ]
        mock_session_repo.list_sessions.return_value = expected_sessions

        result = service.list_sessions()

        assert result == expected_sessions
        mock_session_repo.list_sessions.assert_called_once()

    def test_get_sessions_relationships_no_relations(self):
        mock_session_repo = MagicMock()
        mock_call_repo = MagicMock()
        service = SessionService(mock_session_repo, mock_call_repo)

        session = create_session(id=1, name="S1")
        mock_session_repo.list_sessions.return_value = [session]

        mock_call_repo.get_all_calls_by_session_paginated.return_value = []

        result = service.get_sessions_relationships()

        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].relations == Relation()

    def test_get_sessions_relationships_with_cross_session_call(self):
        mock_session_repo = MagicMock()
        mock_call_repo = MagicMock()
        service = SessionService(mock_session_repo, mock_call_repo)

        s1 = create_session(id=1, name="S1")
        s2 = create_session(id=2, name="S2")
        mock_session_repo.list_sessions.return_value = [s1, s2]

        call_in_s2 = MockCall(id=10, session_id=2, parent_call_id=5, order_in_session=0)
        call_in_s1 = MockCall(
            id=5, session_id=1, parent_call_id=None, order_in_session=2
        )

        def mock_paginated(session_id, size):
            if session_id == 1:
                return [[call_in_s1]]
            if session_id == 2:
                return [[call_in_s2]]
            return []

        mock_call_repo.get_all_calls_by_session_paginated.side_effect = mock_paginated
        mock_call_repo.get_call.side_effect = lambda cid: (
            call_in_s1 if cid == 5 else None
        )

        result = service.get_sessions_relationships()

        s2_rel = next(r for r in result if r.id == 2)
        assert s2_rel.relations.parent_session_id == 1
        assert s2_rel.relations.branch_point_call_id == 5
        assert s2_rel.relations.branch_point_index == 2
