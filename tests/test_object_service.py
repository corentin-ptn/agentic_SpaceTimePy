from datetime import datetime
import unittest
from unittest.mock import MagicMock

from spacetimepy.interface.mcp.api.models.dto import ObjectIdentityDTO, StoredObjectDTO
from spacetimepy.interface.mcp.api.services.object_service import (
    ObjectIdentityService,
    StoredObjectService,
)


def create_obj_identity(id=1, name="obj1"):
    return ObjectIdentityDTO(
        id=id, identity_hash="hash1", name=name, creation_time=datetime.now()
    )


class TestObjectIdentityService(unittest.TestCase):
    def test_get_identity(self):
        mock_repo = MagicMock()
        service = ObjectIdentityService(mock_repo)

        expected = create_obj_identity(id=1, name="obj1")
        mock_repo.get_identity.return_value = expected

        assert service.get_identity(1) == expected
        mock_repo.get_identity.assert_called_once_with(1)

    def test_list_identities(self):
        mock_repo = MagicMock()
        service = ObjectIdentityService(mock_repo)

        expected = [create_obj_identity(id=1, name="obj1")]
        mock_repo.list_identities.return_value = expected

        assert service.list_identities() == expected
        mock_repo.list_identities.assert_called_once()


def create_stored_obj(id="hash1", value="val"):
    return StoredObjectDTO(
        id=id,
        identity_id=1,
        version_number=1,
        type_name="int",
        is_primitive=True,
        primitive_value=1,
        pickle_data=None,
    )


class TestStoredObjectService(unittest.TestCase):
    def test_get_object(self):
        mock_repo = MagicMock()
        service = StoredObjectService(mock_repo)

        expected = create_stored_obj(id="obj1", value="val1")
        mock_repo.get_object.return_value = expected

        assert service.get_object("obj1") == expected
        mock_repo.get_object.assert_called_once_with("obj1")

    def test_get_latest_version(self):
        mock_repo = MagicMock()
        service = StoredObjectService(mock_repo)

        expected = create_stored_obj(id="obj1_v2", value="val2")
        mock_repo.get_last_version_object.return_value = expected

        assert service.get_latest_version(1) == expected
        mock_repo.get_last_version_object.assert_called_once_with(1)

    def test_list_objects(self):
        mock_repo = MagicMock()
        service = StoredObjectService(mock_repo)

        expected = [create_stored_obj(id="obj1", value="val1")]
        mock_repo.list_objects.return_value = expected

        assert service.list_objects() == expected
        mock_repo.list_objects.assert_called_once()
