#!/usr/bin/env python3
"""
SpaceTimePy API

API endpoints for SpaceTimePy database access.
"""

import logging
from dataclasses import asdict

from fastmcp import FastMCP

from spacetimepy.core.representation import PickleConfig
from spacetimepy.interface.mcp.api.models.dto import (
    FunctionCallDTO,
    StoredObjectDTO,
)
from spacetimepy.interface.mcp.api.models.models import (
    FunctionCallDTOSummary,
    FunctionCallTree,
    LaunchDebugRequest,
    SessionDetailsCalls,
    SessionSummaryRelations,
)
from spacetimepy.interface.mcp.api.repositories import (
    FunctionCallRepository,
    MonitoringSessionRepository,
)
from spacetimepy.interface.mcp.api.repositories.code_definition_repository import (
    CodeDefinitionRepository,
    CodeObjectLinkRepository,
)
from spacetimepy.interface.mcp.api.repositories.object_identity_repository import (
    ObjectIdentityRepository,
    StoredObjectRepository,
)
from spacetimepy.interface.mcp.api.repositories.stack_snapshot_repository import (
    StackSnapshotEdgeRepository,
    StackSnapshotRepository,
)
from spacetimepy.interface.mcp.api.services import SessionService
from spacetimepy.interface.mcp.api.services.code_def_service import (
    CodeDefinitionService,
    CodeObjectLinkService,
)
from spacetimepy.interface.mcp.api.services.debug_service import DebugService
from spacetimepy.interface.mcp.api.services.function_call_service import (
    FunctionCallService,
)
from spacetimepy.interface.mcp.api.services.object_service import (
    ObjectIdentityService,
    StoredObjectService,
)
from spacetimepy.interface.mcp.api.services.snapshot_service import (
    SnapshotEdgeService,
    SnapshotService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ********************************
# **         MCP TOOLS          **
# ********************************


def create_mcp(db_path: str, session=None) -> FastMCP:

    # ---------------------------------
    # --        Repositories         --
    # ---------------------------------

    pickle_config = PickleConfig(custom_picklers=["pygame"])

    session_repo = MonitoringSessionRepository(db_path, pickle_config, session)
    call_repo = FunctionCallRepository(db_path, pickle_config, session)
    snapshot_repo = StackSnapshotRepository(db_path, pickle_config, session)
    snapshot_edge_repo = StackSnapshotEdgeRepository(db_path, pickle_config, session)
    object_identity_repo = ObjectIdentityRepository(db_path, pickle_config, session)
    stored_object_repo = StoredObjectRepository(db_path, pickle_config, session)
    code_def_repo = CodeDefinitionRepository(db_path, pickle_config, session)
    code_obj_link_repo = CodeObjectLinkRepository(db_path, pickle_config, session)

    # ---------------------------------
    # --          Services           --
    # ---------------------------------

    session_service = SessionService(session_repo, call_repo)
    call_service = FunctionCallService(call_repo, snapshot_repo)
    snapshot_service = SnapshotService(snapshot_repo)
    snapshot_edge_service = SnapshotEdgeService(snapshot_edge_repo)
    object_identity_service = ObjectIdentityService(object_identity_repo)
    stored_object_service = StoredObjectService(stored_object_repo)
    code_def_service = CodeDefinitionService(code_def_repo)
    code_obj_link_service = CodeObjectLinkService(code_obj_link_repo)

    debug_service = DebugService()

    # ---------------------------------
    # --            MCP              --
    # ---------------------------------

    mcp = FastMCP(
        name="SpaceTimePy Explorer API",
        instructions="Provides Tools for analyzing traces, snapshots and previous state of a program. Allows to load to a specific execution state (if the debugger is launch) with load_snapshot().",
    )

    # ********************************
    # **          DB INFO           **
    # ********************************

    @mcp.tool(tags={"db", "info"})
    def db_get_info() -> dict[str, str]:
        """Get database path information."""
        try:
            return {"db_path": db_path}
        except Exception as e:
            logger.error(f"Error getting DB info: {e}")
            raise ValueError(f"Erreur while getting databse information: {e}")

    # ********************************
    # **       START DEBUGGING      **
    # ********************************

    @mcp.tool(tags={"debug", "start"})
    def start_debugging_spacetimepy(launch_debug_request: LaunchDebugRequest) -> bool:
        """
        Start debugging a specific function in the code with spacetimepy's debugger tools.
        This tool is intended to be used in conjunction with a MCP debugger.
        Args:
            launch_debug_request (LaunchDebugRequest): The request containing the file path, function name, range), and optional reanimation settings.
        Returns:
            bool: True if the request succeed, an error otherwise
        """
        try:
            return debug_service.start_debug_session(launch_debug_request)
        except Exception as e:
            logger.error(f"Error starting debugging: {e}")
            raise ValueError(f"Error while starting debugging: {e}")

    # ********************************
    # **         SESSIONS           **
    # ********************************

    @mcp.tool(tags={"session", "catalog"})
    def session_list() -> list[SessionSummaryRelations]:
        """
        List all registered sessions (allows getting details of past executions).
        Use this as the first step to identify which session ID to analyze.
        """
        return session_service.get_sessions_relationships()

    @mcp.tool(tags={"session", "details"})
    def session_get_details(session_id: int) -> SessionDetailsCalls:
        """
        Retrieve detailed metadata for a specific session.
        After calling this, you can use 'call_list_by_session' or 'call_get_paginated' to explore the function calls of this session.
        Args:
            session_id (int): The unique ID of the session to retrieve.
        """
        try:
            session = session_service.get_session(session_id)
            if not session:
                raise ValueError(f"session {session_id} not found")
            call_count = call_service.get_calls_count_by_session(session_id)
            return SessionDetailsCalls(**asdict(session), call_count=call_count)
        except Exception as e:
            logger.error(f"Error getting session details: {e}")
            raise ValueError(f"Error while getting session details: {e}")

    # ********************************
    # **       FUNCTION CALLS       **
    # ********************************

    @mcp.tool(tags={"call", "details"})
    def call_get_data(session_id: int, call_index: int) -> FunctionCallDTO:
        """
        Retrieve the full data for a specific function call within a session.
        Use this to inspect the exact arguments and return value of a call.
        Args:
            session_id (int): The session ID containing the call.
            call_index (int): The zero-based index of the call in the session's sequence.
        """
        call = call_service.get_calls_by_session_paginated(session_id, 1, call_index)
        if len(call) >= 1:
            return call[0]
        raise ValueError(f"session {session_id} or call n°{call_index} not found")

    @mcp.tool(tags={"call", "catalog"})
    def call_list_by_session(session_id: int) -> list[FunctionCallDTOSummary]:
        """
        List a summary of all function calls for a session.
        Use this to get an overview of the execution flow before diving into specific calls.
        Args:
            session_id (int): The ID of the session.
        """
        return call_service.list_calls_by_session(session_id)

    @mcp.tool(tags={"call", "catalog"})
    def call_get_paginated(session_id: int, size: int = 50, offset: int = 0):
        """
        Retrieve a paginated list of function calls for a session.
        Useful for browsing large sessions without overloading the context.
        Args:
            session_id (int): The ID of the session.
            size (int): Number of calls per page.
            offset (int): Starting point for pagination.
        """
        return call_service.get_calls_by_session_paginated(session_id, size, offset)

    @mcp.tool(tags={"call", "navigation"})
    def call_get_children(call_id: int):
        """
        Retrieve the immediate child calls of a function call.
        Use this to explore the execution tree one level at a time.
        Args:
            call_id (int): The ID of the parent function call.
        """
        return call_service.get_child_calls(call_id)

    @mcp.tool(tags={"call", "navigation"})
    def call_get_execution_tree(
        call_id: int, max_depth: int | None = None
    ) -> FunctionCallTree:
        """
        Retrieve the full execution hierarchy (call tree) starting from a specific call.
        This is the best tool to understand the nesting and sequence of function calls.
        Args:
            call_id (int): The ID of the root function call for the tree.
            max_depth (int | None): Maximum depth to traverse. If None, retrieves the entire subtree (deprecated).
        """
        call = call_service.get_call(call_id)
        if not call:
            raise ValueError(f"function call {call_id} not found")
        return call_service.get_execution_tree(call, max_depth)

    @mcp.tool(tags={"call", "search"})
    def call_search(session_id: int, function_name: str) -> list[FunctionCallDTO]:
        """
        Search for function calls by function name within a specific session.
        Use this to quickly find all occurrences of a specific function (e.g., 'update' or 'draw') without browsing all calls.
        Args:
            session_id (int): The ID of the session to search in.
            function_name (str): The name (or partial name) of the function to search for.
        """
        return call_service.search_calls(session_id, function_name)

    # ********************************
    # **          Snapshots         **
    # ********************************

    @mcp.tool(tags={"snapshot", "action"})
    def snapshot_load(snapshotId: int, ip: str = "localhost", port: int = 3000) -> bool:
        """
        Load a specific snapshot state into the active debugger session.
        WARNING: This action modifies the current state of the debugger and moves the execution point to the snapshot line.
        Args:
            snapshotId (int): The ID of the snapshot to load.
            ip (str): Target machine IP.
            port (int): Target machine port.
        """
        return snapshot_service.load_snapshot(snapshotId, ip=ip, port=port)

    @mcp.tool(tags={"snapshot", "details"})
    def snapshot_get(snapshot_id: int):
        """
        Retrieve a snapshot's details by its ID.
        Use this to analyze the program state at a specific point in time.
        Args:
            snapshot_id (int): The ID of the snapshot.
        """
        return snapshot_service.get_snapshot(snapshot_id)

    @mcp.tool(tags={"snapshot", "catalog"})
    def snapshot_list_by_call(function_call_id: int):
        """
        List all snapshots associated with a specific function call.
        Use this to find the exact state of the program when a specific function was executed.
        Args:
            function_call_id (int): The ID of the function call.
        """
        return snapshot_service.list_snapshots_by_call(function_call_id)

    @mcp.tool(tags={"snapshot", "navigation"})
    def snapshot_get_previous(snapshot_id: int):
        """
        Retrieve the snapshot immediately preceding the given one.
        Use this to trace the program state backwards in time.
        Args:
            snapshot_id (int): The ID of the snapshot.
        """
        return snapshot_service.get_previous_snapshot(snapshot_id)

    @mcp.tool(tags={"snapshot", "navigation"})
    def snapshot_get_successors(snapshot_id: int, edge_type: str | None = None):
        """
        Retrieve the list of snapshots that follow the current one.
        Args:
            snapshot_id (int): The ID of the snapshot.
            edge_type (str | None): Optional filter for the edge type (e.g., 'execution').
        """
        return snapshot_service.get_successors(snapshot_id, edge_type)

    # ********************************
    # **       Snapshots Edge       **
    # ********************************

    @mcp.tool(tags={"snapshot", "edge", "details"})
    def snapshot_edge_get(edge_id: int):
        """
        Retrieve a snapshot edge by its ID.
        Args:
            edge_id (int): The ID of the edge.
        """
        return snapshot_edge_service.get_edge(edge_id)

    @mcp.tool(tags={"snapshot", "edge", "catalog"})
    def snapshot_edge_list_by_type(edge_type: str):
        """
        Retrieve all snapshot edges of a specific type.
        Args:
            edge_type (str): The type of the edge.
        """
        return snapshot_edge_service.list_edges_by_type(edge_type)

    # ********************************
    # **         OBJECTS            **
    # ********************************

    @mcp.tool(tags={"object", "details"})
    def object_get_identity(identity_id: int):
        """
        Retrieve an object entity (identity) by its ID.
        The identity represents the object across its entire lifetime, regardless of its value changes.
        Args:
            identity_id (int): The unique identifier of the object entity.
        """
        return object_identity_service.get_identity(identity_id)

    @mcp.tool(tags={"object", "catalog"})
    def object_list_identities():
        """List all object entities tracked in the session."""
        return object_identity_service.list_identities()

    @mcp.tool(tags={"object", "details"})
    def object_get_stored(object_id: str):
        """
        Retrieve a specific version of an object (value and state) by its unique object_id.
        Use this to inspect the actual data held by an object at a specific point in time.
        Args:
            object_id (str): The unique identifier of the stored object version.
        """
        return stored_object_service.get_object(object_id)

    @mcp.tool(tags={"object", "details"})
    def object_get_latest_version(object_identity_id: int):
        """
        Retrieve the most recent version of an object associated with a given identity.
        Args:
            object_identity_id (int): The unique identifier of the object entity.
        """
        return stored_object_service.get_latest_version(object_identity_id)

    @mcp.tool(tags={"object", "details", "history"})
    def object_get_history(object_identity_id: int) -> list[StoredObjectDTO]:
        """
        Retrieve the full history of an object's versions associated with a given identity.
        Use this to track how an object's value evolves over time during the execution.
        Args:
            object_identity_id (int): The unique identifier of the object entity.
        """
        return stored_object_service.get_object_history(object_identity_id)

    @mcp.tool(tags={"object", "catalog"})
    def object_list_stored():
        """List all stored object versions ordered by their starting time."""
        return stored_object_service.list_objects()

    # ********************************
    # **           CODE             **
    # ********************************

    @mcp.tool(tags={"code", "details"})
    def code_get_definition(definition_id: str):
        """
        Retrieve a code definition by its unique ID.
        Use this to see the source code and metadata associated with a function or class.
        Args:
            definition_id (str): The unique identifier of the code definition.
        """
        return code_def_service.get_definition(definition_id)

    @mcp.tool(tags={"code", "catalog"})
    def code_list_definitions():
        """List all code definitions available in the session."""
        return code_def_service.list_definitions()

    @mcp.tool(tags={"code", "details"})
    def code_get_object_link(link_id: int):
        """
        Retrieve a link between a stored object and its code definition.
        Args:
            link_id (int): The unique identifier of the link.
        """
        return code_obj_link_service.get_link(link_id)

    @mcp.tool(tags={"code", "catalog"})
    def code_list_links_by_object(object_id: str):
        """
        List all code definitions associated with a specific stored object.
        Use this to find where an object is defined or used in the code.
        Args:
            object_id (str): The unique identifier of the stored object.
        """
        return code_obj_link_service.list_links_by_object(object_id)

    @mcp.tool(tags={"code", "catalog"})
    def code_list_links_by_definition(definition_id: str):
        """
        List all stored objects associated with a specific code definition.
        Use this to find all runtime instances of a specific class or function.
        Args:
            definition_id (str): The unique identifier of the code definition.
        """
        return code_obj_link_service.list_links_by_definition(definition_id)

    return mcp


# ********************************
# **        RUN SERVER          **
# ********************************


def run_mcp(
    db_file: str,
    host: str = "127.0.0.1",
    port: int = 3002,
    tracked_function: str | None = None,  # Ex: "display_game"
    image_metadata_key: str | None = None,  # Ex: "image"
    image_scale: float = 0.8,
):
    """Run the MPC server."""

    try:
        mcp = create_mcp(db_file)
        logger.info(f"Starting MCP server at http://{host}:{port}")
        mcp.run(transport="streamable-http", host=host, port=port)
    except KeyboardInterrupt:
        logger.info("API server stopped.")
