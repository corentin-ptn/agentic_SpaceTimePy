#!/usr/bin/env python3
"""
SpaceTimePy API

API endpoints for SpaceTimePy database access.
"""

import logging
from dataclasses import asdict

from fastmcp import FastMCP

from spacetimepy.core.models import init_db
from spacetimepy.core.representation import PickleConfig
from spacetimepy.interface.mcp.api.models.dto import (
    FunctionCallDTO,
)
from spacetimepy.interface.mcp.api.models.models import (
    FunctionCallDTOSummary,
    FunctionCallTree,
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
    if not session:
        session = init_db(
            db_path
        )()  # add '()' to create a session, and not get a sessionmaker

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
    call_service = FunctionCallService(call_repo)
    snapshot_service = SnapshotService(snapshot_repo)
    snapshot_edge_service = SnapshotEdgeService(snapshot_edge_repo)
    object_identity_service = ObjectIdentityService(object_identity_repo)
    stored_object_service = StoredObjectService(stored_object_repo)
    code_def_service = CodeDefinitionService(code_def_repo)
    code_obj_link_service = CodeObjectLinkService(code_obj_link_repo)

    # ---------------------------------
    # --            MCP              --
    # ---------------------------------

    mcp = FastMCP(
        name="SpaceTimePy Explorer API",
    )

    # ********************************
    # **          DB INFO           **
    # ********************************

    @mcp.tool
    def get_db_info_tool() -> dict[str, str]:
        """Get database path information."""
        try:
            return {"db_path": db_path}
        except Exception as e:
            logger.error(f"Error getting DB info: {e}")
            raise ValueError(f"Erreur while getting databse information: {e}")

    # ********************************
    # **         SESSIONS           **
    # ********************************

    @mcp.tool
    def list_sessions() -> list[SessionSummaryRelations]:
        """List all monitoring sessions."""
        return session_service.get_sessions_relationships()

    @mcp.tool
    def get_session_details(session_id: int) -> SessionDetailsCalls:
        """
        Get detailed information about a specific session.
        Args:
            session_id (int): Retrieve the details of the session with this specific ID
        """
        try:
            session = session_service.get_session(session_id)
            if not session:
                raise ValueError(f"session {session_id} not found")
            call_count = call_service.get_calls_count_by_session(session_id)
            return SessionDetailsCalls(**asdict(session), call_count=call_count)
        except Exception as e:
            logger.error(f"Error getting session details: {e}")
            raise ValueError(f"Error while getting : {e}")

    # ********************************
    # **       FUNCTION CALLS       **
    # ********************************

    @mcp.tool
    def get_call_data(session_id: int, call_index: int) -> FunctionCallDTO:
        """
        Get data for a specific function call.
        Args:
            session_id (int): The session ID to get the function call from
            call_index (int): The FunctionCall index to retrieve (`call_index` >= 0)
        """
        call = call_service.get_calls_by_session_paginated(session_id, 1, call_index)
        if len(call) >= 1:
            return call[0]
        raise ValueError(f"session {session_id} or call n°{call_index} not found")

    @mcp.tool
    def list_calls_by_session(session_id: int) -> list[FunctionCallDTOSummary]:
        """
        List all function calls for a session.
        Args:
            session_id (int): The ID of the session.
        """
        return call_service.list_calls_by_session(session_id)

    @mcp.tool
    def get_calls_paginated(session_id: int, size: int = 50, offset: int = 0):
        """
        Retrieve a paginated list of function calls for a session.
        Args:
            session_id (int): The ID of the session.
            size (int): The number of calls to retrieve per page.
            offset (int): The offset for pagination.
        """
        return call_service.get_calls_by_session_paginated(session_id, size, offset)

    @mcp.tool
    def get_child_calls(call_id: int):
        """
        Retrieve the child calls of a function call.
        Args:
            call_id (int): The ID of the parent function call.
        """
        return call_service.get_child_calls(call_id)

    @mcp.tool
    def get_execution_tree(
        call_id: int, max_depth: int | None = None
    ) -> FunctionCallTree:
        """
        Get stack recording data for a function call.
        Args:
            call_id (int): The FunctionCall Id to look at (will be the parent of the tree)
            max_depth (int | None): the maximum depth of the tree. If `None`, there will be no maximum depth.
        """
        call = call_service.get_call(call_id)
        if not call:
            raise ValueError(f"function call {call_id} not found")
        return call_service.get_execution_tree(call, max_depth)

    # ********************************
    # **          Snapshots         **
    # ********************************

    @mcp.tool
    def load_snapshot(snapshotId: int, ip: str = "localhost", port: int = 3000) -> bool:
        """
        Modify the current debug session to load the state of the snapshot Id and place the debugger to the snapshot line corresponding.
        Args:
            snapshotId (int): The ID of the snapshot to load.
            ip (str): The IP address of the target machine.
            port (int): The port of the target machine.
        """
        return snapshot_service.load_snapshot(snapshotId, ip=ip, port=port)

    @mcp.tool
    def get_snapshot(snapshot_id: int):
        """
        Retrieve a snapshot by its ID.
        Args:
            snapshot_id (int): The ID of the snapshot.
        """
        return snapshot_service.get_snapshot(snapshot_id)

    @mcp.tool
    def list_snapshots_by_call(function_call_id: int):
        """
        List all snapshots depending of a function call.
        Args:
            function_call_id (int): The ID of the function call.
        """
        return snapshot_service.list_snapshots_by_call(function_call_id)

    @mcp.tool
    def get_previous_snapshot(snapshot_id: int):
        """
        Retrieve the predecessor snapshot.
        Args:
            snapshot_id (int): The ID of the snapshot.
        """
        return snapshot_service.get_previous_snapshot(snapshot_id)

    @mcp.tool
    def get_snapshot_successors(snapshot_id: int, edge_type: str | None = None):
        """
        Retrieve the list of next snapshots.
        Args:
            snapshot_id (int): The ID of the snapshot.
            edge_type (str | None): Optional filter for the edge type.
        """
        return snapshot_service.get_successors(snapshot_id, edge_type)

    # ********************************
    # **       Snapshots Edge       **
    # ********************************

    @mcp.tool
    def get_snapshot_edge(edge_id: int):
        """
        Retrieve a snapshot edge by its ID.
        Args:
            edge_id (int): The ID of the edge.
        """
        return snapshot_edge_service.get_edge(edge_id)

    @mcp.tool
    def list_snapshot_edges_by_type(edge_type: str):
        """
        Retrieve all snapshot edges of a specific type.
        Args:
            edge_type (str): The type of the edge.
        """
        return snapshot_edge_service.list_edges_by_type(edge_type)

    # ********************************
    # **         OBJECTS            **
    # ********************************

    @mcp.tool
    def get_object_identity(identity_id: int):
        """
        Retrieve an object entity by its ID.
        Args:
            identity_id (int): The unique identifier of the object entity.
        """
        return object_identity_service.get_identity(identity_id)

    @mcp.tool
    def list_object_identities():
        """List all object entities."""
        return object_identity_service.list_identities()

    @mcp.tool
    def get_stored_object(object_id: str):
        """
        Retrieve an object (object with its value) by its ID.
        Args:
            object_id (str): The unique identifier of the object.
        """
        return stored_object_service.get_object(object_id)

    @mcp.tool
    def get_latest_object_version(object_identity_id: int):
        """
        Retrieve the last version of an object.
        Args:
            object_identity_id (int): The unique identifier of the object entity.
        """
        return stored_object_service.get_latest_version(object_identity_id)

    @mcp.tool
    def list_stored_objects():
        """List all stored objects ordered by their starting time."""
        return stored_object_service.list_objects()

    # ********************************
    # **           CODE             **
    # ********************************

    @mcp.tool
    def get_code_definition(definition_id: str):
        """
        Retrieve a code definition by its ID.
        Args:
            definition_id (str): The unique identifier of the code definition.
        """
        return code_def_service.get_definition(definition_id)

    @mcp.tool
    def list_code_definitions():
        """List all code definitions."""
        return code_def_service.list_definitions()

    @mcp.tool
    def get_code_object_link(link_id: int):
        """
        Retrieve a link by its ID.
        Args:
            link_id (int): The unique identifier of the link.
        """
        return code_obj_link_service.get_link(link_id)

    @mcp.tool
    def list_links_by_object(object_id: str):
        """
        List all links associated with a specific object.
        Args:
            object_id (str): The unique identifier of the object.
        """
        return code_obj_link_service.list_links_by_object(object_id)

    @mcp.tool
    def list_links_by_definition(definition_id: str):
        """
        List all links associated with a specific code definition.
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
