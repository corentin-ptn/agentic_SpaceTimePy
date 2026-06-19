import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from spacetimepy.interface.mcp.api.models.dto import StackSnapshotDTO
from spacetimepy.interface.mcp.api.services.snapshot_service import SnapshotService


def create_snapshot(id=1):
    return StackSnapshotDTO(
        id=1,
        function_call_id=1,
        code_definition_id=1,
        line_number=1,
        timestamp=datetime.now(),
        locals_refs={},
        globals_refs={},
        order_in_call=1,
        next_snapshot_id=2,
    )


class TestSnapshotService(unittest.TestCase):
    def test_get_snapshot(self):
        mock_repo = MagicMock()
        service = SnapshotService(mock_repo)

        expected = create_snapshot(id=1)
        mock_repo.get_snapshot.return_value = expected

        assert service.get_snapshot(1) == expected
        mock_repo.get_snapshot.assert_called_once_with(1)

    def test_list_snapshots_by_call(self):
        mock_repo = MagicMock()
        service = SnapshotService(mock_repo)

        expected = [create_snapshot(id=1)]
        mock_repo.list_snapshots_by_call.return_value = expected

        assert service.list_snapshots_by_call(100) == expected
        mock_repo.list_snapshots_by_call.assert_called_once_with(100)

    def test_get_previous_snapshot(self):
        mock_repo = MagicMock()
        service = SnapshotService(mock_repo)

        expected = create_snapshot(id=0)
        mock_repo.get_previous_snapshot.return_value = expected

        assert service.get_previous_snapshot(1) == expected
        mock_repo.get_previous_snapshot.assert_called_once_with(1)

    def test_get_successors(self):
        mock_repo = MagicMock()
        service = SnapshotService(mock_repo)

        expected = [create_snapshot(id=2)]
        mock_repo.get_previous_snapshot.return_value = expected

        assert service.get_successors(1, "type") == expected
        mock_repo.get_previous_snapshot.assert_called_once_with(1, "type")

    @patch("requests.post")
    def test_load_snapshot_success(self, mock_post):
        mock_repo = MagicMock()
        mock_repo.db_path = "test.db"
        service = SnapshotService(mock_repo)

        mock_repo.get_snapshot.return_value = create_snapshot(id=1)

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        assert service.load_snapshot(1) is True
        mock_post.assert_called_once()

    def test_load_snapshot_not_found(self):
        mock_repo = MagicMock()
        service = SnapshotService(mock_repo)

        mock_repo.get_snapshot.return_value = None

        with self.assertRaises(ValueError):
            service.load_snapshot(1)
