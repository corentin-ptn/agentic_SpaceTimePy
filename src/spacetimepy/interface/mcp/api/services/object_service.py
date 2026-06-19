from spacetimepy.interface.mcp.api.models.dto import ObjectIdentityDTO, StoredObjectDTO
from spacetimepy.interface.mcp.api.repositories.object_identity_repository import (
    ObjectIdentityRepository,
    StoredObjectRepository,
)


class ObjectIdentityService:
    """Service to manage objects identities and their logic."""

    def __init__(
        self,
        object_identity_repo: ObjectIdentityRepository,
    ):
        self.object_identity_repo = object_identity_repo

    # --- Direct calls to repository ---

    def get_identity(self, identity_id: int) -> ObjectIdentityDTO | None:
        """
        Retrieve an object entity by its ID.

        Args:
            identity_id: The unique identifier of the object entity.

        Returns:
            ObjectIdentityDTO: The DTO representation of the object entity, or None if not found.
        """
        return self.object_identity_repo.get_identity(identity_id)

    def list_identities(self) -> list[ObjectIdentityDTO]:
        """
        List all object entities.

        Returns:
            list[ObjectIdentityDTO]: A list of DTO representations of all object entities.
        """
        return self.object_identity_repo.list_identities()


class StoredObjectService:
    """Service to manage objects values stored and their logic."""

    def __init__(
        self,
        stored_object_repo: StoredObjectRepository,
    ):
        self.stored_object_repo = stored_object_repo

    # --- Direct calls to repository ---

    def get_object(self, object_id: str) -> StoredObjectDTO | None:
        """
        Retrieve an object (object with its value) by its ID.

        Args:
            object_id: The unique identifier of the object.

        Returns:
            StoredObjectDTO: The DTO representation of the object, or None if not found.
        """
        return self.stored_object_repo.get_object(object_id)

    def get_latest_version(self, object_identity_id: int) -> StoredObjectDTO | None:
        """
        Retrieve the last version of an object.

        Args:
            object_identity_id: The unique identifier of the object entity.

        Returns:
            StoredObjectDTO: The DTO representation of the object entity, or None if not found.
        """
        return self.stored_object_repo.get_last_version_object(object_identity_id)

    def list_objects(self) -> list[StoredObjectDTO]:
        """
        List all stored objects ordered by their starting time.

        Returns:
            list[StoredObjectDTO]: A list of DTO representations of all stored objects.
        """
        return self.stored_object_repo.list_objects()
