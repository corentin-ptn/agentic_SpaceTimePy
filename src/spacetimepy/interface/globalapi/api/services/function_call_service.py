from collections.abc import Generator
from dataclasses import asdict

from spacetimepy.interface.globalapi.api.models.dto import FunctionCallDTO
from spacetimepy.interface.globalapi.api.models.models import FunctionCallTree
from spacetimepy.interface.globalapi.api.repositories.function_call_repository import (
    FunctionCallRepository,
)


class FunctionCallService:
    """Service to manage function calls and their logic."""

    def __init__(self, call_repo: FunctionCallRepository):
        self.call_repo = call_repo

    # --- Direct calls to repository ---

    def get_call(self, call_id: int) -> FunctionCallDTO | None:
        """Retrieve a function call by its ID.

        Args:
            call_id: The ID of the function call to retrieve.

        Returns:
            The FunctionCallDTO if found, otherwise None.
        """
        return self.call_repo.get_call(call_id)

    def get_calls_count_by_session(self, session_id: int) -> int:
        """Retrieve the number of function calls for a session.

        Args:
            session_id: The ID of the session.

        Returns:
            The count of function calls for the session.
        """
        return self.call_repo.get_calls_count_by_session(session_id)

    def list_calls_by_session(self, session_id: int) -> list[FunctionCallDTO]:
        """List all function calls for a session.

        Args:
            session_id: The ID of the session.

        Returns:
            A list of FunctionCallDTOs for the session.
        """
        return self.call_repo.list_calls_by_session(session_id)

    def get_calls_by_session_paginated(
        self,
        session_id: int,
        size: int = 50,
        offset: int = 0,
    ) -> list[FunctionCallDTO]:
        """Retrieve a paginated list of function calls for a session.

        Args:
            session_id: The ID of the session.
            size: The number of calls to retrieve per page.
            offset: The offset for pagination.

        Returns:
            A paginated list of FunctionCallDTOs for the session.
        """
        return self.call_repo.get_calls_by_session_paginated(session_id, size, offset)

    def get_all_calls_by_session_paginated(
        self,
        session_id: int,
        size: int = 50,
    ) -> Generator[list[FunctionCallDTO], None, None]:
        """Generator to retrieve all function calls for a session in batches.

        Args:
            session_id: The ID of the session.
            size: The number of calls to retrieve per batch.

        Returns:
            A generator yielding batches of FunctionCallDTOs for the session.
        """
        return self.call_repo.get_all_calls_by_session_paginated(session_id, size)

    def get_child_calls(self, call_id: int) -> list[FunctionCallDTO]:
        """Retrieve the child calls of a function call.

        Args:
            call_id: The ID of the parent function call.

        Returns:
            A list of child FunctionCallDTOs.
        """
        return self.call_repo.get_child_calls(call_id)

    # --- Domain logic ---

    def get_execution_tree(
        self,
        call: FunctionCallDTO,
        max_depth: int | None = None,
        current_depth: int = 0,
    ) -> FunctionCallTree:
        """Recursively build the execution tree starting from a function call.

        Args:
            call: The FunctionCallDTO to start building the tree from.
            max_depth: Maximum depth to traverse (None for unlimited).
            current_depth: Current depth in the recursion.

        Returns:
            A FunctionCallTree representing the execution tree starting from the given call.
        """
        if call is None:
            return None

        # Stop recursion if we've reached max depth
        if max_depth is not None and current_depth >= max_depth:
            return call

        # Get child calls ordered by execution
        children = self.get_child_calls(call.id)

        # Build the current node
        node = FunctionCallTree(**asdict(call))

        # Recursively add children
        for child in children:
            child_node = self.get_execution_tree(
                child, max_depth=max_depth, current_depth=current_depth + 1
            )
            node.children.append(FunctionCallTree(**asdict(child_node)))

        return node
