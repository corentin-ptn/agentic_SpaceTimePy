from collections.abc import Generator
from typing import Any

from sqlalchemy import func

from spacetimepy.core.models import FunctionCall
from spacetimepy.interface.mcp.api.models.dto import FunctionCallDTO

from .base_repository import BaseRepository, sqlalchemy_to_dict


class FunctionCallRepository(BaseRepository):
    def get_call(self, call_id: int) -> FunctionCallDTO | None:
        """
        Retrieve a function call by its ID.

        Args:
            call_id: The unique identifier of the function call.

        Returns:
            FunctionCallDTO: The DTO representation of the function call, or None if not found.
        """
        with self._get_session() as session:
            call = session.query(FunctionCall).get(call_id)
            if not call:
                return None
            return FunctionCallDTO(**sqlalchemy_to_dict(call))

    def get_calls_count_by_session(self, session_id: int) -> dict[str, int]:
        """
        Retrieve the count of function calls for a specific session.

        Args:
            session_id: The unique identifier of the session.

        Returns:
            dict[str, int]: key: The name of the function called, value: The number of calls in the session.
        """
        with self._get_session() as session:
            results = (
                session.query(FunctionCall.function, func.count(FunctionCall.id))
                .where(FunctionCall.session_id == session_id)
                .group_by(FunctionCall.function)
                .all()
            )
            return dict(results)

    def list_calls_by_session(self, session_id: int) -> list[FunctionCallDTO]:
        """
        List all function calls for a specific session, ordered by their position in the session.

        Args:
            session_id: The unique identifier of the session.

        Returns:
            list[FunctionCallDTO]: A list of DTO representations of all function calls for the session.
        """
        with self._get_session() as session:
            calls = (
                session.query(FunctionCall)
                .filter(FunctionCall.session_id == session_id)
                .order_by(FunctionCall.order_in_session)
                .all()
            )
            return [FunctionCallDTO(**sqlalchemy_to_dict(c)) for c in calls]

    def get_calls_by_session_paginated(
        self,
        session_id: int,
        size: int = 50,
        offset: int = 0,
    ) -> list[FunctionCallDTO]:
        """
        Retrieve a paginated list of function calls for a specific session.

        Args:
            session_id: The unique identifier of the session.
            size: The maximum number of function calls to return per page. Defaults to 50.
            offset: The number of function calls to skip before returning results. Defaults to 0.

        Returns:
            list[FunctionCallDTO]: A paginated list of DTO representations of function calls for the session.
        """
        with self._get_session() as session:
            calls = (
                session.query(FunctionCall)
                .filter(FunctionCall.session_id == session_id)
                .order_by(FunctionCall.order_in_session)
                .offset(offset)
                .limit(size)
                .all()
            )
            return [FunctionCallDTO(**sqlalchemy_to_dict(c)) for c in calls]

    def get_all_calls_by_session_paginated(
        self,
        session_id: int,
        size: int = 50,
    ) -> Generator[list[FunctionCallDTO], None, None]:
        """
        Generator to retrieve all function calls for a session in batches.

        Args:
            session_id: The unique identifier of the session.
            size: The batch size for each iteration. Defaults to 50.

        Yields:
            list[FunctionCallDTO]: A batch of DTO representations of function calls for the session.
        """
        offset = 0
        while True:
            calls = self.get_calls_by_session_paginated(session_id, size, offset)
            if not calls:
                break
            yield calls
            offset += size

    def get_child_calls(self, parent_call_id: int) -> list[FunctionCallDTO]:
        """
        Retrieve all child function calls of a specific parent call.

        Args:
            parent_call_id: The unique identifier of the parent function call.

        Returns:
            list[FunctionCallDTO]: A list of DTO representations of child function calls, ordered by their position in the parent and start time.
        """
        with self._get_session() as session:
            return [
                FunctionCallDTO(**sqlalchemy_to_dict(call))
                for call in session.query(FunctionCall)
                .filter(FunctionCall.parent_call_id == parent_call_id)
                .order_by(FunctionCall.order_in_parent, FunctionCall.start_time)
                .all()
            ]

    def create_call(self, call_data: dict[str, Any]) -> FunctionCallDTO:
        """
        Create a new function call.

        Args:
            call_data: A dictionary containing the data for the new function call.

        Returns:
            FunctionCallDTO: The DTO representation of the newly created function call.
        """
        with self._get_session() as session:
            call = FunctionCall(**call_data)
            session.add(call)
            session.commit()
            return FunctionCallDTO(**sqlalchemy_to_dict(call))
