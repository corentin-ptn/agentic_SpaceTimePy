from types import SimpleNamespace
from unittest.mock import patch

from spacetimepy.codediff.graph_generator import generate_line_mapping


def test_gumtree_update_node_creates_bidirectional_line_mapping(tmp_path):
    old_code = "def target(x):\n    a = x + 1\n    return a\n"
    new_code = "def target(x):\n    a = x + 2\n    return a\n"
    old_path = tmp_path / "old.py"
    new_path = tmp_path / "new.py"
    old_path.write_text(old_code)
    new_path.write_text(new_code)

    update_index = old_code.index("1")
    gumtree_output = f"""
=== update-node
---
literal: 1 [{update_index},{update_index}]
replace 1 by 2
"""

    with patch("spacetimepy.codediff.graph_generator.ensure_gumtree_available", return_value="/fake/gumtree"):
        with patch(
            "spacetimepy.codediff.graph_generator.subprocess.run",
            return_value=SimpleNamespace(returncode=0, stdout=gumtree_output, stderr=""),
        ):
            mapping_v1_to_v2, mapping_v2_to_v1, modified_lines = generate_line_mapping(
                str(old_path),
                str(new_path),
            )

    assert mapping_v1_to_v2[2] == 2
    assert mapping_v2_to_v1[2] == 2
    assert modified_lines == [2]
