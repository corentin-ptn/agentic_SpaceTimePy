from typing import Any

from spacetimepy.core.models import CodeDefinition, CodeObjectLink
from spacetimepy.interface.globalapi.api.models.dto import (
    CodeDefinitionDTO,
    CodeObjectLinkDTO,
)

from .base_repository import BaseRepository, sqlalchemy_to_dict


class CodeDefinitionRepository(BaseRepository):
    def get_definition(self, definition_id: str) -> CodeDefinitionDTO | None:
        """
        Retrieve a code definition by its ID.

        Args:
            definition_id: The unique identifier of the code definition.

        Returns:
            CodeDefinitionDTO: The DTO representation of the code definition, or None if not found.
        """
        with self._get_session() as session:
            definition = session.query(CodeDefinition).get(definition_id)
            if not definition:
                return None
            return CodeDefinitionDTO(**sqlalchemy_to_dict(definition))

    def list_definitions(self) -> list[CodeDefinitionDTO]:
        """
        List all code definitions.

        Returns:
            list[CodeDefinitionDTO]: A list of DTO representations of all code definitions.
        """
        with self._get_session() as session:
            definitions = session.query(CodeDefinition).all()
            return [CodeDefinitionDTO(**sqlalchemy_to_dict(d)) for d in definitions]

    def create_definition(self, definition_data: dict[str, Any]) -> CodeDefinitionDTO:
        """
        Create a new code definition.

        Args:
            definition_data: A dictionary containing the data for the new code definition.

        Returns:
            CodeDefinitionDTO: The DTO representation of the newly created code definition.
        """
        with self._get_session() as session:
            definition = CodeDefinition(**definition_data)
            session.add(definition)
            session.commit()
            return CodeDefinitionDTO(**sqlalchemy_to_dict(definition))

class CodeObjectLinkRepository(BaseRepository):
    def get_link(self, link_id: int) -> CodeObjectLinkDTO | None:
        """
        Retrieve a link by its ID.

        Args:
            link_id: The unique identifier of the link.

        Returns:
            CodeObjectLinkDTO: The DTO representation of the link, or None if not found.
        """
        with self._get_session() as session:
            link = session.query(CodeObjectLink).get(link_id)
            if not link:
                return None
            return CodeObjectLinkDTO(**sqlalchemy_to_dict(link))

    def list_links_by_object(self, object_id: str) -> list[CodeObjectLinkDTO]:
        """
        List all links associated with a specific object.

        Args:
            object_id: The unique identifier of the object.

        Returns:
            list[CodeObjectLinkDTO]: A list of DTO representations of all links for the object.
        """
        with self._get_session() as session:
            links = (
                session.query(CodeObjectLink)
                .filter(CodeObjectLink.object_id == object_id)
                .all()
            )
            return [CodeObjectLinkDTO(**sqlalchemy_to_dict(lnk)) for lnk in links]

    def list_links_by_definition(self, definition_id: str) -> list[CodeObjectLinkDTO]:
        """
        List all links associated with a specific code definition.

        Args:
            definition_id: The unique identifier of the code definition.

        Returns:
            list[CodeObjectLinkDTO]: A list of DTO representations of all links for the code definition.
        """
        with self._get_session() as session:
            links = (
                session.query(CodeObjectLink)
                .filter(CodeObjectLink.definition_id == definition_id)
                .all()
            )
            return [CodeObjectLinkDTO(**sqlalchemy_to_dict(lnk)) for lnk in links]

    def create_link(self, link_data: dict[str, Any]) -> CodeObjectLinkDTO:
        """
        Create a new link.

        Args:
            link_data: A dictionary containing the data for the new link.

        Returns:
            CodeObjectLinkDTO: The DTO representation of the newly created link.
        """
        with self._get_session() as session:
            link = CodeObjectLink(**link_data)
            session.add(link)
            session.commit()
            return CodeObjectLinkDTO(**sqlalchemy_to_dict(link))