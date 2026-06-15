from typing import Any

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

    def get_latest_version(self, identity_id: int) -> StoredObjectDTO | None:
        """
        Retrieve the last version of an object.

        Args:
            identity_id: The unique identifier of the object entity.

        Returns:
            ObjectIdentityDTO: The DTO representation of the object entity, or None if not found.
        """
        with self._get_session() as session:
            identity = session.query(ObjectIdentity).get(identity_id)
            if not identity:
                return None
            latest_version = identity.get_latest_version(session)
            if not latest_version:
                return None
            return StoredObjectDTO(**sqlalchemy_to_dict(latest_version))


class StoredObjectRepository(BaseRepository):
    def get_object(self, object_id: str) -> StoredObjectDTO | None:
        """
        Retrieve an object (object with its value) by its ID.

        Args:
            object_id: The unique identifier of the object.

        Returns:
            StoredObjectDTO: The DTO representation of the object, or None if not found.
        """
        with self._get_session() as session:
            obj = session.query(StoredObject).get(object_id)
            if not obj:
                return None
            return StoredObjectDTO(**sqlalchemy_to_dict(obj))

    def list_objects(self) -> list[StoredObjectDTO]:
        """
        List all stored objects ordered by their starting time.

        Returns:
            list[StoredObjectDTO]: A list of DTO representations of all stored objects.
        """
        with self._get_session() as session:
            objects = session.query(StoredObject).all()
            return [StoredObjectDTO(**sqlalchemy_to_dict(o)) for o in objects]

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
            return StoredObjectDTO(**sqlalchemy_to_dict(obj))
