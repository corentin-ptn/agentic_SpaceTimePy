import unittest
from dataclasses import asdict
from datetime import datetime
from unittest.mock import MagicMock

from spacetimepy.interface.mcp.api.models.dto import FunctionCallDTO
from spacetimepy.interface.mcp.api.models.models import (
    FunctionCallDTOSummary,
    FunctionCallTree,
)
from spacetimepy.interface.mcp.api.services.function_call_service import (
    FunctionCallService,
)


def create_mock_call(id=1, session_id=1, order_in_session=0):
    return FunctionCallDTO(
        id=id,
        function="test_func",
        file="test.py",
        line=10,
        start_time=datetime.now(),
        end_time=datetime.now(),
        call_metadata={},
        locals_refs={},
        globals_refs={},
        return_ref=None,
        code_definition_id="def_1",
        session_id=session_id,
        parent_call_id=None,
        order_in_parent=0,
        order_in_session=order_in_session,
        first_snapshot_id=1,
    )


class TestFunctionCallService(unittest.TestCase):
    def test_get_call(self):
        mock_repo = MagicMock()
        service = FunctionCallService(mock_repo)

        expected_call = create_mock_call()
        mock_repo.get_call.return_value = expected_call

        assert service.get_call(1) == expected_call
        mock_repo.get_call.assert_called_once_with(1)

    def test_get_calls_count_by_session(self):
        mock_repo = MagicMock()
        service = FunctionCallService(mock_repo)

        expected_count = {"fun_name": 10}
        mock_repo.get_calls_count_by_session.return_value = expected_count

        assert service.get_calls_count_by_session(1) == expected_count
        mock_repo.get_calls_count_by_session.assert_called_once_with(1)

    def test_list_calls_by_session(self):
        mock_repo = MagicMock()
        service = FunctionCallService(mock_repo)

        mock_calls = [
            create_mock_call(id=1, session_id=1, order_in_session=0),
            create_mock_call(id=2, session_id=1, order_in_session=1),
        ]
        mock_repo.list_calls_by_session.return_value = mock_calls

        result = service.list_calls_by_session(1)

        assert len(result) == 2
        assert isinstance(result[0], FunctionCallDTOSummary)
        assert result.sort(key=lambda f_c: f_c.id) == [
            FunctionCallDTOSummary.from_dict(asdict(m_call)) for m_call in mock_calls
        ].sort(key=lambda f_c: f_c.id)
        mock_repo.list_calls_by_session.assert_called_once_with(1)

    def test_get_calls_by_session_paginated(self):
        mock_repo = MagicMock()
        service = FunctionCallService(mock_repo)

        expected_calls = [create_mock_call(id=1, session_id=1, order_in_session=0)]
        mock_repo.get_calls_by_session_paginated.return_value = expected_calls

        assert service.get_calls_by_session_paginated(1, 50, 0) == expected_calls
        mock_repo.get_calls_by_session_paginated.assert_called_once_with(1, 50, 0)

    def test_get_all_calls_by_session_paginated(self):
        mock_repo = MagicMock()
        service = FunctionCallService(mock_repo)

        expected_calls = [create_mock_call(id=1, session_id=1, order_in_session=0)]
        mock_repo.get_all_calls_by_session_paginated.return_value = expected_calls

        assert service.get_all_calls_by_session_paginated(1, 50) == expected_calls
        mock_repo.get_all_calls_by_session_paginated.assert_called_once_with(1, 50)

    def test_get_execution_tree(self):
        mock_repo = MagicMock()
        service = FunctionCallService(mock_repo)

        calls = [create_mock_call(id=i) for i in range(1, 5)]
        calls_tree = [FunctionCallTree.from_dict(asdict(call)) for call in calls]
        calls_tree[0].children = [calls_tree[1], calls_tree[2]]
        calls_tree[2].children = [calls_tree[3]]

        def mock_get_children(call_id):
            if call_id == 1:
                return [calls[1], calls[2]]
            if call_id == 2:
                return []
            if call_id == 3:
                return [calls[3]]
            if call_id == 4:
                return []
            return []

        mock_repo.get_child_calls.side_effect = mock_get_children

        result = service.get_execution_tree(calls[0])
        assert result == calls_tree[0]

        mock_repo.get_child_calls.assert_any_call(1)
        mock_repo.get_child_calls.assert_any_call(2)
        mock_repo.get_child_calls.assert_any_call(3)
        mock_repo.get_child_calls.assert_any_call(4)
