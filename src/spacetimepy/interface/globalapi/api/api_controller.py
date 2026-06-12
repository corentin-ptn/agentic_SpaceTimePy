#!/usr/bin/env python3
"""
SpaceTimePy API

API endpoints for SpaceTimePy database access.
"""

import logging
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from spacetimepy.core.representation import PickleConfig
from spacetimepy.interface.globalapi.api.models.dto import (
    FunctionCallDTO,
)
from spacetimepy.interface.globalapi.api.models.models import (
    FunctionCallTree,
    SessionDetailsCalls,
    SessionDetailsRelations,
)
from spacetimepy.interface.globalapi.api.repositories import (
    FunctionCallRepository,
    MonitoringSessionRepository,
)
from spacetimepy.interface.globalapi.api.services import SessionService
from spacetimepy.interface.globalapi.api.services.function_call_service import (
    FunctionCallService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ********************************
# **        API ROUTES          **
# ********************************


def create_app(db_path: str, session=None) -> FastAPI:

    # ---------------------------------
    # --        Repositories         --
    # ---------------------------------
    pickle_config = (PickleConfig(custom_picklers=["pygame"]),)

    session_repo = MonitoringSessionRepository(db_path, pickle_config, session=session)
    call_repo = FunctionCallRepository(db_path, pickle_config, session=session)

    # ---------------------------------
    # --          Services           --
    # ---------------------------------

    session_service = SessionService(session_repo, call_repo)
    call_service = FunctionCallService(call_repo)

    # ---------------------------------
    # --            App              --
    # ---------------------------------

    app = FastAPI(
        title="SpaceTimePy Explorer API",
        description="REST endpoints for Explorer sessions",
        version="1.0.0",
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ********************************
    # **          DB INFO           **
    # ********************************

    @app.get("/api/db-info", response_model=dict[str, str])
    def get_db_info():
        """Get database path information."""
        try:
            return {"db_path": db_path}
        except Exception as e:
            logger.error(f"Error getting DB info: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    # ********************************
    # **         SESSIONS           **
    # ********************************

    @app.get("/api/sessions", response_model=list[SessionDetailsRelations])
    def list_sessions():
        """List all monitoring sessions."""
        return session_service.get_sessions_relationships()

    @app.get("/api/session/{session_id}", response_model=SessionDetailsCalls)
    def get_session_details(session_id: str):
        """Get detailed information about a specific session."""
        try:
            session = session_service.get_session(session_id)
            if not session:
                raise ValueError(f"session {session_id} not found")
            call_count = call_service.get_calls_count_by_session(session_id)
            return SessionDetailsCalls(**asdict(session), call_count=call_count)
        except Exception as e:
            logger.error(f"Error getting session details: {e}")
            raise HTTPException(
                status_code=404 if "not found" in str(e) else 400, detail=str(e)
            ) from e

    # ********************************
    # **          CALLS             **
    # ********************************

    @app.get(
        "/api/sessions/{session_id}/calls/{call_index}", response_model=FunctionCallDTO
    )
    def get_call_data(session_id: int, call_index: int):
        """Get data for a specific function call."""
        try:
            call = call_service.get_calls_by_session_paginated(
                session_id, 1, call_index
            )
            if len(call) >= 1:
                return call[0]
            raise ValueError("not found")
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

    # @app.get(
    #     "/api/sessions/{session_id}/compare/{comparison_session_id}/calls/{call_index}",
    #     response_model=dict[str, FunctionCallDTO],
    # )
    # def compare_call_data(session_id: int, comparison_session_id: int, call_index: int):
    #     """Compare call data between two sessions."""
    #     try:
    #         return {}
    #     except ValueError as e:
    #         raise HTTPException(status_code=404, detail=str(e))

    # ********************************
    # **     STROBOSCOPIC FRAMES    **
    # ********************************

    # @app.get(
    #     "/api/sessions/{session_id}/stroboscopic/{call_index}",
    #     response_model=list[StroboscopicFrame],
    # )
    # def get_stroboscopic_frames(
    #     session_id: int,
    #     call_index: int,
    #     ghost_count: int = 4,
    #     offset: int = 2,
    # ):
    #     """Get stroboscopic frames for a call."""
    #     try:
    #         return service.get_stroboscopic_frames(
    #             session_id, call_index, ghost_count, offset
    #         )
    #     except ValueError as e:
    #         raise HTTPException(status_code=400, detail=str(e))

    # ********************************
    # **      STACK RECORDING       **
    # ********************************

    # @app.get("/api/stack-recording/{function_id}")
    # def get_stack_recording(function_id: str):
    #     """Get stack recording data for a function call."""
    #     try:
    #         # return call.(function_id)
    #         pass
    #     except NotImplementedError as e:
    #         raise HTTPException(status_code=501, detail=str(e))
    #     except ValueError as e:
    #         raise HTTPException(
    #             status_code=404 if "not found" in str(e) else 400, detail=str(e)
    #         ) from e
    #     except Exception as e:
    #         logger.error(f"Error getting stack recording: {e}")
    #         raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/execution-tree/{call_id}", response_model=FunctionCallTree)
    def get_execution_tree(
        call_id: int,
        max_depth: int | None = Query(
            None, description="Search term to filter function calls"
        ),
    ):
        """Get stack recording data for a function call."""
        try:
            call = call_service.get_call(call_id)
            if not call:
                raise ValueError(f"function call {call_id} not found")
            return call_service.get_execution_tree(call, max_depth)
        except ValueError as e:
            raise HTTPException(
                status_code=404 if "not found" in str(e) else 400, detail=str(e)
            ) from e
        except Exception as e:
            logger.error(f"Error getting execution tree: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    # ********************************
    # **       FUNCTION CALLS       **
    # ********************************

    # @app.get("/api/function-calls", response_model=list[FunctionCallModel])
    # def get_function_calls(
    #     search: str | None = Query(
    #         None, description="Search term to filter function calls"
    #     ),
    #     file: str | None = Query(None, description="File filter"),
    #     function: str | None = Query(None, description="Function name filter"),
    # ):
    #     """Get a list of function calls with optional filtering."""
    #     try:
    #         return service.(search, file, function)
    #     except Exception as e:
    #         logger.error(f"Error getting function calls: {e}")
    #         raise HTTPException(status_code=500, detail=str(e))

    return app


# ********************************
# **        RUN SERVER          **
# ********************************


def run_api(
    db_file: str,
    host: str = "127.0.0.1",
    port: int = 8000,
    tracked_function: str | None = None,  # Ex: "display_game"
    image_metadata_key: str | None = None,  # Ex: "image"
    image_scale: float = 0.8,
):
    """Run the API server."""
    import uvicorn

    try:
        app = create_app(db_file)
        logger.info(f"Starting API server at http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)
    except KeyboardInterrupt:
        logger.info("API server stopped.")
