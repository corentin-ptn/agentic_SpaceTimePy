from typing import Any

from sqlalchemy import desc

from spacetimepy.core.models import ObjectIdentity, StoredObject
from spacetimepy.interface.mcp.api.models.dto import (
    ObjectIdentityDTO,
    StoredObjectDTO,
)

from .base_repository import BaseRepository, sqlalchemy_to_dict


class ObjectIdentityRepository(BaseRepository):
    def get_identity(self, identity_id: int) -> ObjectIdentityDTO | None:
        """
        Retrieve an object entity by its ID.

        Args:
            identity_id: The unique identifier of the object entity.

        Returns:
            ObjectIdentityDTO: The DTO representation of the object entity, or None if not found.
        """
        with self._get_session() as session:
            identity = session.query(ObjectIdentity).get(identity_id)
            if not identity:
                return None
            return ObjectIdentityDTO(**sqlalchemy_to_dict(identity))

    def list_identities(self) -> list[ObjectIdentityDTO]:
        """
        List all object entities.

        Returns:
            list[ObjectIdentityDTO]: A list of DTO representations of all object entities.
        """
        with self._get_session() as session:
            identities = session.query(ObjectIdentity).all()
            return [ObjectIdentityDTO(**sqlalchemy_to_dict(i)) for i in identities]

    def create_identity(self, identity_data: dict[str, Any]) -> ObjectIdentityDTO:
        """
        Create a new object entity.

        Args:
            identity_data: A dictionary containing the data for the new object entity.

        Returns:
            ObjectIdentityDTO: The DTO representation of the newly created object entity.
        """
        with self._get_session() as session:
            identity = ObjectIdentity(**identity_data)
            session.add(identity)
            session.commit()
            return ObjectIdentityDTO(**sqlalchemy_to_dict(identity))


class StoredObjectRepository(BaseRepository):
    def _sqlalchemy_to_dict(self, obj: Any) -> dict[str, Any]:
        if obj is None:
            return None
        result = sqlalchemy_to_dict(obj)
        with self._get_object_manager() as object_manager:
            result["pickle_data"] = object_manager.get(result["id"])[0]
            return result

    def _unpickle(self, obj_id: int):
        with self._get_object_manager() as object_manager:
            return object_manager.get(obj_id)[0]

    def get_object(self, object_id: str) -> StoredObjectDTO | None:
        """
        Retrieve an object (object with its value) by its ID.

        Args:
            object_id: The unique identifier of the object.

        Returns:
            StoredObjectDTO: The DTO representation of the object, or None if not found.
        """
        with self._get_session() as session:
            data = session.query(StoredObject).get(object_id)
            if data is None:
                return None
            return StoredObjectDTO(**self._sqlalchemy_to_dict(data))

    def get_last_version_object(self, identity_id: str) -> StoredObjectDTO | None:
        """
        Retrieve the last version of an object.

        Args:
            identity_id: The unique identifier of the object entity.

        Returns:
            StoredObjectDTO: The DTO representation of the object entity, or None if not found.
        """
        with self._get_session() as session:
            data = (
                session.query(StoredObject)
                .filter(StoredObject.identity_id == identity_id)
                .order_by(desc(StoredObject.version_number))
                .first()
            )
            if data is None:
                return None
            return StoredObjectDTO(**self._sqlalchemy_to_dict(data))

    def get_object_history(self, identity_id: int) -> list[StoredObjectDTO]:
        """
        Retrieve all versions of an object associated with a given identity, ordered by version number.

        Args:
            identity_id: The unique identifier of the object entity.

        Returns:
            list[StoredObjectDTO]: A list of all versions of the object.
        """
        with self._get_session() as session:
            data = (
                session.query(StoredObject)
                .filter(StoredObject.identity_id == identity_id)
                .order_by(StoredObject.version_number)
                .all()
            )
            return [StoredObjectDTO(**self._sqlalchemy_to_dict(d)) for d in data]

    def list_objects(self) -> list[StoredObjectDTO]:
        """
        List all stored objects ordered by their starting time.

        Returns:
            list[StoredObjectDTO]: A list of DTO representations of all stored objects.
        """
        with self._get_session() as session:
            data = session.query(StoredObject).all()
            return [StoredObjectDTO(**self._sqlalchemy_to_dict(d)) for d in data]

    def create_object(self, object_data: dict[str, Any]) -> StoredObjectDTO:
        """
        Create a new stored object.

        Args:
            object_data: A dictionary containing the data for the new object.

        Returns:
            StoredObjectDTO: The DTO representation of the newly created object.
        """
        with self._get_session() as session:
            obj = StoredObject(**object_data)
            session.add(obj)
            session.commit()
            return StoredObjectDTO(**self._sqlalchemy_to_dict(obj))
