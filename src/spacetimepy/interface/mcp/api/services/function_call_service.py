from collections.abc import Generator
from dataclasses import asdict

from spacetimepy.interface.mcp.api.models.dto import FunctionCallDTO
from spacetimepy.interface.mcp.api.models.models import (
    FunctionCallDetails,
    FunctionCallDTOSummary,
    FunctionCallTree,
)
from spacetimepy.interface.mcp.api.repositories.function_call_repository import (
    FunctionCallRepository,
)
from spacetimepy.interface.mcp.api.repositories.object_identity_repository import (
    StoredObjectRepository,
)
from spacetimepy.interface.mcp.api.repositories.stack_snapshot_repository import (
    StackSnapshotRepository,
)


class FunctionCallService:
    """Service to manage function calls and their logic."""

    def __init__(
        self,
        call_repo: FunctionCallRepository,
        snapshot_service: StackSnapshotRepository,
        object_repo: StoredObjectRepository,
    ):
        self.call_repo = call_repo
        self.snapshot_service = snapshot_service
        self.object_repo = object_repo

    # --- Direct calls to repository ---

    def get_call(self, call_id: int) -> FunctionCallDetails | None:
        """Retrieve a function call by its ID.

        Args:
            call_id: The ID of the function call to retrieve.

        Returns:
            The FunctionCallDetails if found, otherwise None.
        """
        f_call = self.call_repo.get_call(call_id)
        if not f_call:
            return None

        return FunctionCallDetails.from_dict(
            {
                **asdict(f_call),
                "nb_snapshots": self.snapshot_service.get_snapshot_count_by_call(
                    f_call.id
                ),
                "locals_var": {
                    k: self.object_repo.get_object(v).pickle_data
                    for k, v in f_call.locals_refs.items()
                },
                "return_var": self.object_repo.get_object(f_call.return_ref).pickle_data
                if f_call.return_ref
                else None,
            }
        )

    def get_call_by_index(
        self, session_id: int, order_in_session: int
    ) -> FunctionCallDetails | None:
        """Retrieve a function call by its session ID and order in session.

        Args:
            session_id: The ID of the session.
            order_in_session: The order of the function call in the session.
        Returns:
            The FunctionCallDetails if found, otherwise None.
        """
        f_call = self.call_repo.get_calls_by_session_paginated(
            session_id, 1, order_in_session
        )[0]
        if not f_call:
            return None

        return FunctionCallDetails.from_dict(
            {
                **asdict(f_call),
                "nb_snapshots": self.snapshot_service.get_snapshot_count_by_call(
                    f_call.id
                ),
                "locals_var": {
                    k: self.object_repo.get_object(v).pickle_data
                    for k, v in f_call.locals_refs.items()
                },
                "return_var": self.object_repo.get_object(f_call.return_ref).pickle_data
                if f_call.return_ref
                else None,
            }
        )

    def get_calls_count_by_session(self, session_id: int) -> dict[str, int]:
        """Retrieve the number of function calls for a session.

        Args:
            session_id: The ID of the session.

        Returns:
            The count of function calls for the session.
        """
        return self.call_repo.get_calls_count_by_session(session_id)

    def list_calls_by_session(self, session_id: int) -> list[FunctionCallDTOSummary]:
        """List all function calls for a session.

        Args:
            session_id: The ID of the session.

        Returns:
            A list of FunctionCallDTOSummary for the session.
        """
        return [
            FunctionCallDTOSummary.from_dict(
                {
                    **asdict(f_call),
                    "nb_snapshots": self.snapshot_service.get_snapshot_count_by_call(
                        f_call.id
                    ),
                }
            )
            for f_call in self.call_repo.list_calls_by_session(session_id)
        ]

    def list_calls_detailed_by_session(
        self, session_id: int
    ) -> list[FunctionCallDetails]:
        """
        List all function calls for a session with detailed information.

        Args:
            session_id: The ID of the session.

        Returns:
            A list of FunctionCallDetails for the session.
        """
        return [
            FunctionCallDetails.from_dict(
                {
                    **asdict(f_call),
                    "nb_snapshots": self.snapshot_service.get_snapshot_count_by_call(
                        f_call.id
                    ),
                    "locals_var": {
                        k: self.object_repo.get_object(v).pickle_data
                        for k, v in f_call.locals_refs.items()
                    },
                    "return_var": self.object_repo.get_object(f_call.return_ref).pickle_data
                    if f_call.return_ref
                    else None,
                }
            )
            for f_call in self.call_repo.list_calls_by_session(session_id)
        ]

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

    def search_calls(
        self, session_id: int, function_name: str
    ) -> list[FunctionCallDTO]:
        """
        Search for function calls by function name within a session.

        Args:
            session_id: The ID of the session.
            function_name: The name of the function to search for.

        Returns:
            A list of matching FunctionCallDTOs.
        """
        return self.call_repo.search_calls_by_function_name(session_id, function_name)

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
            return FunctionCallTree.from_dict(
                {
                    **asdict(call),
                    "nb_snapshots": self.snapshot_service.get_snapshot_count_by_call(
                        call.id
                    ),
                }
            )

        # Get child calls ordered by execution
        children = self.get_child_calls(call.id)

        # Build the current node
        node = FunctionCallTree.from_dict(
            {
                **asdict(call),
                "nb_snapshots": self.snapshot_service.get_snapshot_count_by_call(
                    call.id
                ),
            }
        )

        # Recursively add children
        for child in children:
            child_node = self.get_execution_tree(
                child, max_depth=max_depth, current_depth=current_depth + 1
            )
            node.children.append(child_node)

        return node
