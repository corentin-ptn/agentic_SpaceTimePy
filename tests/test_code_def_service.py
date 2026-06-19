import unittest
from datetime import datetime
from unittest.mock import MagicMock

from spacetimepy.interface.mcp.api.models.dto import (
    CodeDefinitionDTO,
    CodeObjectLinkDTO,
)
from spacetimepy.interface.mcp.api.services.code_def_service import (
    CodeDefinitionService,
    CodeObjectLinkService,
)


def create_code_def(id="hash1", name="test_func", line=1):
    return CodeDefinitionDTO(
        id=id,
        name=name,
        type="type",
        module_path="module/test.py",
        code_content="def foo(): pass",
        first_line_no=line,
        creation_time=datetime.now(),
    )


class TestCodeDefinitionService(unittest.TestCase):
    def test_get_definition(self):
        mock_repo = MagicMock()
        service = CodeDefinitionService(mock_repo)

        expected = create_code_def(id="def1", name="test_func", line=10)
        mock_repo.get_definition.return_value = expected

        assert service.get_definition("def1") == expected
        mock_repo.get_definition.assert_called_once_with("def1")

    def test_list_definitions(self):
        mock_repo = MagicMock()
        service = CodeDefinitionService(mock_repo)

        expected = [create_code_def(id="def1", name="f1", line=1)]
        mock_repo.list_definitions.return_value = expected

        assert service.list_definitions() == expected
        mock_repo.list_definitions.assert_called_once()


def create_code_lnk(id=1, object_id="obj1", def_id="hash1"):
    return CodeObjectLinkDTO(
        id=id, object_id=object_id, definition_id=def_id, timestamp=datetime.now
    )


class TestCodeObjectLinkService(unittest.TestCase):
    def test_get_link(self):
        mock_repo = MagicMock()
        service = CodeObjectLinkService(mock_repo)

        expected = create_code_lnk(id=1, object_id="obj1", def_id="def1")
        mock_repo.get_link.return_value = expected

        assert service.get_link(1) == expected
        mock_repo.get_link.assert_called_once_with(1)

    def test_list_links_by_object(self):
        mock_repo = MagicMock()
        service = CodeObjectLinkService(mock_repo)

        expected = [create_code_lnk(id=1, object_id="obj1", def_id="def1")]
        mock_repo.list_links_by_object.return_value = expected

        assert service.list_links_by_object("obj1") == expected
        mock_repo.list_links_by_object.assert_called_once_with("obj1")

    def test_list_links_by_definition(self):
        mock_repo = MagicMock()
        service = CodeObjectLinkService(mock_repo)

        expected = [create_code_lnk(id=1, object_id="obj1", def_id="def1")]
        mock_repo.list_links_by_definition.return_value = expected

        assert service.list_links_by_definition("def1") == expected
        mock_repo.list_links_by_definition.assert_called_once_with("def1")
