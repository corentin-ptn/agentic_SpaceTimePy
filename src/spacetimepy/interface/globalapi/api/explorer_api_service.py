#!/usr/bin/env python3
"""
SpaceTimePy Explorer API Service - Stateless Version
A stateless service layer for the SpaceTimePy API, using the stateless GameExplorer.
"""

from __future__ import annotations

import logging

from spacetimepy.interface.globalapi.api.game_explorer import GameExplorer
from spacetimepy.interface.globalapi.api.models import (
    CallData,
    FunctionCallModel,
    SessionDetails,
    SessionListItem,
    StackSnapshotModel,
    StroboscopicFrame,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ExplorerApiService:
    """Stateless service for the SpaceTimePy API, using stateless GameExplorer methods."""

    def __init__(
        self,
        game_explorer: GameExplorer,
        image_scale: float = 0.8,
    ) -> None:
        self.game_explorer = game_explorer
        self.image_scale = image_scale

    # ********************************
    # **     Helper Functions       **
    # ********************************

    # def _to_session_list_item(self, session_data: dict) -> SessionListItem:
    #     """Convertit un dict de session en SessionListItem (dataclass)."""
    #     return SessionListItem(
    #         session_id=session_data.get("session_id"),
    #         name=session_data.get("name"),
    #         start_time=self._serialize_datetime(session_data.start_time),
    #         call_count=session_data.get("call_count"),
    #         is_branch=session_data.get("is_branch"),
    #         parent_session_id=session_data.get("parent_session_id"),
    #         branch_point_index=session_data.get("branch_point_index"),
    #         child_sessions=session_data.get("child_sessions", []),
    #     )

    # def _to_call_data(self, call_data: dict) -> CallData:
    #     """Convertit un dict d'appel en CallData (dataclass)."""
    #     return CallData(
    #         image_data=call_data.get("image_data"),
    #         variables=VariablesData(
    #             locals=call_data.get("variables", {}).get("locals", {}),
    #             globals=call_data.get("variables", {}).get("globals", {}),
    #         ),
    #         call_id=call_data("call_id"),
    #         timestamp=self._serialize_datetime(call_data.get("timestamp")),
    #         session_id=call_data("session_id"),
    #         call_index=call_data("call_index"),
    #         file=call_data("file"),
    #         line=call_data("line"),
    #         function=call_data("function"),
    #     )

    # def _to_session_details(self, session_details: dict) -> SessionDetails:
    #     """Convertit un dict de détails de session en SessionDetails (dataclass)."""
    #     calls = [self._to_call_data(call) for call in session_details.get("calls", [])]
    #     return SessionDetails(
    #         id=session_details("id"),
    #         name=session_details("name"),
    #         start_time=self._serialize_datetime(session_details.get("start_time")),
    #         end_time=self._serialize_datetime(session_details.get("end_time")),
    #         call_count=session_details("call_count"),
    #         calls=calls,
    #     )

    # ********************************
    # **     Session Management     **
    # ********************************

    def list_sessions(self) -> list[SessionListItem]:
        """List all monitoring sessions."""
        return self.game_explorer.list_sessions()

    def get_session_details(self, session_id: str) -> SessionDetails:
        """Get detailed information about a specific monitoring session."""
        try:
            session_id_int = int(session_id)
        except ValueError:
            raise ValueError(f"Invalid session ID: {session_id}")

        session_details = self.game_explorer.get_session_details(
            session_id=session_id_int
        )
        if not session_details:
            raise ValueError(f"Session {session_id} not found")
        return session_details

    # ********************************
    # **        Call Data           **
    # ********************************

    def get_call_data(self, session_id: int, call_index: int) -> CallData:
        """Get data for a specific function call."""
        call_data = self.game_explorer.get_call_data(
            session_id=session_id,
            call_index=call_index,
        )
        if not call_data:
            raise ValueError(
                f"Call not found for session {session_id}, index {call_index}"
            )
        return call_data

    def compare_call_data(
        self, session_id: int, call_index: int, comparison_session_id: int
    ) -> dict:
        """Compare call data between two sessions."""
        current_call_data = self.get_call_data(session_id, call_index)

        comparison_call_data = self.get_call_data(
            comparison_session_id,
            call_index,
        )

        if not comparison_call_data:
            raise ValueError("No comparable frame found for the selected sessions")

        return {
            "current": current_call_data,
            "comparison": comparison_call_data,
        }

    # ********************************
    # **     Stroboscopic Frames    **
    # ********************************

    def get_stroboscopic_frames(
        self, session_id: int, call_index: int, ghost_count: int = 4, offset: int = 2
    ) -> list[StroboscopicFrame]:
        """Get stroboscopic frames for a call."""
        frames = self.game_explorer.get_stroboscopic_frames(
            session_id=session_id,
            current_call_index=call_index,
            ghost_count=ghost_count,
            offset=offset,
        )
        return [
            StroboscopicFrame(
                call_index=frame["call_index"],
                call_id=frame["call_id"],
                image_data=frame["image_data"],
            )
            for frame in frames
        ]

    # ********************************
    # **      Function Calls        **
    # ********************************

    def get_function_calls(
        self,
        search: str | None = None,
        file: str | None = None,
        function: str | None = None,
    ) -> list[FunctionCallModel]:
        """Get a list of function calls with optional filtering."""
        function_calls = []
        sessions = self.list_sessions()

        # TODO: c'est très long !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        for session in sessions:
            session_details = self.game_explorer.get_session_details(
                session.session_id, True
            )
            for call in session_details.calls:
                # Appliquer les filtres
                if search:
                    search_lower = search.lower()
                    if (
                        search_lower not in call.function.lower()
                        and search_lower not in call.file.lower()
                    ):
                        continue
                if file and file.lower() not in call.file.lower():
                    continue
                if function and function.lower() not in call.function.lower():
                    continue
                function_calls.append(call)
        return function_calls

    # ********************************
    # **       Database Info        **
    # ********************************

    def get_db_info(self) -> dict:
        """Get database path information."""
        return {"db_path": self.game_explorer.db_path}

    # ********************************
    # **     Stack Recording        **
    # ********************************

    def get_stack_recording_data(self, function_id: str) -> FunctionCallModel:
        """Get stack recording data for a function call."""
        raise NotImplementedError("get_stack_recording_data is not yet implemented")

    # ********************************
    # **      Snapshot Data         **
    # ********************************

    def get_snapshot_data(self, snapshot_id: str) -> StackSnapshotModel:
        """Get details of a specific stack snapshot."""
        raise NotImplementedError("get_snapshot_data is not yet implemented")

    # ********************************
    # **      Object Graph          **
    # ********************************

    def get_object_graph_data(self, show_isolated: bool = False) -> dict:
        """Get the object graph for visualization."""
        raise NotImplementedError("get_object_graph_data is not yet implemented")

    # ********************************
    # **      Execution Tree        **
    # ********************************

    def get_execution_tree_data(self, call_id: str, max_depth: int = 5) -> dict:
        """Get the hierarchical execution tree for a function call."""
        raise NotImplementedError("get_execution_tree_data is not yet implemented")

    # ********************************
    # **      Graph Data            **
    # ********************************

    def get_graph_data(self, call_id: str) -> dict:
        """Get the graph for a function call."""
        raise NotImplementedError("get_graph_data is not yet implemented")

    # ********************************
    # **      Compare Traces        **
    # ********************************

    def compare_traces_data(self, request_data: dict) -> dict:
        """Generate edit graph from two traces for comparison."""
        raise NotImplementedError("compare_traces_data is not yet implemented")
