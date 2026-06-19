import unittest
from unittest.mock import MagicMock, patch

from spacetimepy.interface.mcp.api.repositories.code_definition_repository import (
    CodeDefinitionRepository,
)
from spacetimepy.interface.mcp.api.repositories.function_call_repository import (
    FunctionCallRepository,
)
from spacetimepy.interface.mcp.api.repositories.monitoring_session_repository import (
    MonitoringSessionRepository,
)
from spacetimepy.interface.mcp.api.repositories.object_identity_repository import (
    ObjectIdentityRepository,
)
from spacetimepy.interface.mcp.api.repositories.stack_snapshot_repository import (
    StackSnapshotRepository,
)


class TestRepositories(unittest.TestCase):
    def setUp(self):
        # Mock the session and the session manager
        self.mock_session = MagicMock()
        self.mock_repo_base = MagicMock()

    @patch(
        "spacetimepy.interface.mcp.api.repositories.base_repository.BaseRepository._get_session"
    )
    def test_code_definition_repo(self, mock_get_session):
        mock_get_session.return_value.__enter__.return_value = MagicMock()
        repo = CodeDefinitionRepository("db_path")

        # Mock query.get
        mock_session = mock_get_session.return_value.__enter__.return_value
        mock_session.query.return_value.get.return_value = None

        assert repo.get_definition("none") is None

        # Mock list
        mock_session.query.return_value.all.return_value = []
        assert repo.list_definitions() == []

    @patch(
        "spacetimepy.interface.mcp.api.repositories.base_repository.BaseRepository._get_session"
    )
    def test_function_call_repo(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        repo = FunctionCallRepository("db_path")

        mock_session.query.return_value.get.return_value = None
        assert repo.get_call(1) is None

        mock_session.query.return_value.all.return_value = []
        assert repo.list_calls_by_session(1) == []

    @patch(
        "spacetimepy.interface.mcp.api.repositories.base_repository.BaseRepository._get_session"
    )
    def test_monitoring_session_repo(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        repo = MonitoringSessionRepository("db_path")

        mock_session.query.return_value.get.return_value = None
        assert repo.get_session(1) is None

        mock_session.query.return_value.all.return_value = []
        assert repo.list_sessions() == []

    @patch(
        "spacetimepy.interface.mcp.api.repositories.base_repository.BaseRepository._get_session"
    )
    def test_object_identity_repo(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        repo = ObjectIdentityRepository("db_path")

        mock_session.query.return_value.get.return_value = None
        assert repo.get_identity(1) is None

        mock_session.query.return_value.all.return_value = []
        assert repo.list_identities() == []

    @patch(
        "spacetimepy.interface.mcp.api.repositories.base_repository.BaseRepository._get_session"
    )
    def test_stack_snapshot_repo(self, mock_get_session):
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        repo = StackSnapshotRepository("db_path")

        mock_session.query.return_value.get.return_value = None
        assert repo.get_snapshot(1) is None

        mock_session.query.return_value.all.return_value = []
        assert repo.list_snapshots_by_call(1) == []
