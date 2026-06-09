import asyncio
import datetime
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from spacetimepy.core.models import Base, CodeDefinition, FunctionCall, StackSnapshot
from spacetimepy.interface.web import api


class TestTracePartsApi(unittest.TestCase):
    def setUp(self):
        self.previous_session = api.session
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        api.session = self.session

    def tearDown(self):
        api.session = self.previous_session
        self.session.close()

    def test_trace_parts_split_by_contiguous_code_definition(self):
        code_v1 = CodeDefinition(
            id="code-v1",
            name="target",
            type="function",
            module_path="/tmp/target.py",
            code_content="def target(x):\n    a = x + 1\n    return a\n",
            first_line_no=10,
        )
        code_v2 = CodeDefinition(
            id="code-v2",
            name="target",
            type="function",
            module_path="/tmp/target.py",
            code_content="def target(x):\n    a = x + 2\n    return a\n",
            first_line_no=20,
        )
        call = FunctionCall(
            function="target",
            file="/tmp/target.py",
            line=10,
            start_time=datetime.datetime.now(),
            code_definition_id="code-v1",
        )
        self.session.add_all([code_v1, code_v2, call])
        self.session.commit()

        snapshots = [
            StackSnapshot(function_call_id=call.id, code_definition_id="code-v1", line_number=11, order_in_call=0),
            StackSnapshot(function_call_id=call.id, code_definition_id="code-v1", line_number=12, order_in_call=1),
            StackSnapshot(function_call_id=call.id, code_definition_id="code-v2", line_number=21, order_in_call=2),
            StackSnapshot(function_call_id=call.id, code_definition_id="code-v2", line_number=22, order_in_call=3),
            StackSnapshot(function_call_id=call.id, code_definition_id="code-v1", line_number=12, order_in_call=4),
        ]
        self.session.add_all(snapshots)
        self.session.commit()

        with patch.object(
            api,
            "generate_line_mapping_from_string",
            return_value=({1: 1, 2: 2, 3: 3}, {1: 1, 2: 2, 3: 3}, [2]),
        ):
            result = asyncio.run(api.get_trace_parts_data(str(call.id), include_alignment=True))

        self.assertEqual(result["function"]["id"], str(call.id))
        self.assertEqual(result["function"]["code_definition_id"], "code-v1")
        self.assertEqual([part["code_definition_id"] for part in result["parts"]], ["code-v1", "code-v2", "code-v1"])
        self.assertEqual([part["frame_count"] for part in result["parts"]], [2, 2, 1])
        self.assertEqual(result["parts"][0]["frames"][0]["frame_id"], f"snapshot:{snapshots[0].id}")
        self.assertEqual(result["parts"][0]["frames"][0]["relative_line"], 2)
        self.assertEqual(result["parts"][1]["frames"][0]["relative_line"], 2)
        self.assertEqual(result["alignment"]["status"], "ok")
        self.assertEqual(result["alignment"]["mode"], "line_mapping")

        line_2_group = next(
            group
            for group in result["alignment"]["groups"]
            if len(group["members"]) == 2
            and all(member["line"] == 2 for member in group["members"])
        )
        self.assertEqual(line_2_group["kind"], "matched")
        self.assertEqual(
            [member["frame_ids"] for member in line_2_group["members"]],
            [
                [f"snapshot:{snapshots[0].id}"],
                [f"snapshot:{snapshots[2].id}"],
            ],
        )

        line_3_group = next(
            group
            for group in result["alignment"]["groups"]
            if len(group["members"]) == 3
            and all(member["line"] == 3 for member in group["members"])
        )
        self.assertEqual(line_3_group["kind"], "matched")
        self.assertEqual(
            [member["frame_ids"] for member in line_3_group["members"]],
            [
                [f"snapshot:{snapshots[1].id}"],
                [f"snapshot:{snapshots[3].id}"],
                [f"snapshot:{snapshots[4].id}"],
            ],
        )

    def test_alignment_uses_gumtree_mapping_for_modified_line(self):
        code_v1 = CodeDefinition(
            id="code-v1",
            name="target",
            type="function",
            module_path="/tmp/target.py",
            code_content="def target(x):\n    a = x + 1\n    return a\n",
            first_line_no=10,
        )
        code_v2 = CodeDefinition(
            id="code-v2",
            name="target",
            type="function",
            module_path="/tmp/target.py",
            code_content="def target(x):\n    a = x + 2\n    return a\n",
            first_line_no=20,
        )
        call = FunctionCall(
            function="target",
            file="/tmp/target.py",
            line=10,
            start_time=datetime.datetime.now(),
            code_definition_id="code-v1",
        )
        self.session.add_all([code_v1, code_v2, call])
        self.session.commit()

        snapshots = [
            StackSnapshot(function_call_id=call.id, code_definition_id="code-v1", line_number=11, order_in_call=0),
            StackSnapshot(function_call_id=call.id, code_definition_id="code-v2", line_number=21, order_in_call=1),
        ]
        self.session.add_all(snapshots)
        self.session.commit()

        with patch.object(
            api,
            "generate_line_mapping_from_string",
            return_value=({2: 2}, {2: 2}, [2]),
        ):
            result = asyncio.run(api.get_trace_parts_data(str(call.id), include_alignment=True))

        line_2_group = next(
            group
            for group in result["alignment"]["groups"]
            if len(group["members"]) == 2
            and all(member["line"] == 2 for member in group["members"])
        )
        self.assertEqual(line_2_group["kind"], "matched")
        self.assertEqual(
            [member["frame_ids"] for member in line_2_group["members"]],
            [[f"snapshot:{snapshots[0].id}"], [f"snapshot:{snapshots[1].id}"]],
        )
        self.assertEqual(
            result["alignment"]["mappings"][0]["strategy"],
            "gumtree_line_mapping",
        )
        self.assertEqual(result["alignment"]["mappings"][0]["v1_to_v2"]["2"], 2)


if __name__ == "__main__":
    unittest.main()
