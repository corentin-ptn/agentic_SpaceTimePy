from spacetimepy.interface.mcp.api.models.dto import (
    CodeDefinitionDTO,
    CodeObjectLinkDTO,
)
from spacetimepy.interface.mcp.api.repositories.code_definition_repository import (
    CodeDefinitionRepository,
    CodeObjectLinkRepository,
)


class CodeDefinitionService:
    def __init__(self, code_def_repo: CodeDefinitionRepository):
        self.code_def_repo = code_def_repo

    def get_definition(self, definition_id: str) -> CodeDefinitionDTO | None:
        """
        Retrieve a code definition by its ID.

        Args:
            definition_id: The unique identifier of the code definition.

        Returns:
            CodeDefinitionDTO: The DTO representation of the code definition, or None if not found.
        """
        return self.code_def_repo.get_definition(definition_id)

    def list_definitions(self) -> list[CodeDefinitionDTO]:
        """
        List all code definitions.

        Returns:
            list[CodeDefinitionDTO]: A list of DTO representations of all code definitions.
        """
        return self.code_def_repo.list_definitions()


class CodeObjectLinkService:
    def __init__(self, code_object_repo: CodeObjectLinkRepository):
        self.code_object_repo = code_object_repo

    def get_link(self, link_id: int) -> CodeObjectLinkDTO | None:
        """
        Retrieve a link by its ID.

        Args:
            link_id: The unique identifier of the link.

        Returns:
            CodeObjectLinkDTO: The DTO representation of the link, or None if not found.
        """
        return self.code_object_repo.get_link(link_id)

    def list_links_by_object(self, object_id: str) -> list[CodeObjectLinkDTO]:
        """
        List all links associated with a specific object.

        Args:
            object_id: The unique identifier of the object.

        Returns:
            list[CodeObjectLinkDTO]: A list of DTO representations of all links for the object.
        """
        return self.code_object_repo.list_links_by_object(object_id)

    def list_links_by_definition(self, definition_id: str) -> list[CodeObjectLinkDTO]:
        """
        List all links associated with a specific code definition.

        Args:
            definition_id: The unique identifier of the code definition.

        Returns:
            list[CodeObjectLinkDTO]: A list of DTO representations of all links for the code definition.
        """
        return self.code_object_repo.list_links_by_definition(definition_id)
