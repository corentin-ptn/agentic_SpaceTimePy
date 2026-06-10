#!/usr/bin/env python3
"""
SpaceTimePy API

API endpoints for SpaceTimePy database access.
"""

import logging

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from spacetimepy.core.representation import PickleConfig
from spacetimepy.interface.globalapi.api.explorer_api_service import ExplorerApiService
from spacetimepy.interface.globalapi.api.game_explorer import GameExplorerFactory
from spacetimepy.interface.globalapi.api.models import (
    CallData,
    FunctionCallModel,
    SessionDetails,
    SessionListItem,
    StroboscopicFrame,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ********************************
# **        API ROUTES          **
# ********************************


def create_app(service: ExplorerApiService) -> FastAPI:
    app = FastAPI(
        title="SpaceTimePy (Game)Explorer API",
        description="REST endpoints for GameExplorer sessions",
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
    app.state.service = service

    # ********************************
    # **          DB INFO           **
    # ********************************

    @app.get("/api/db-info", response_model=dict[str, str])
    def get_db_info():
        """Get database path information."""
        try:
            return service.get_db_info()
        except Exception as e:
            logger.error(f"Error getting DB info: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ********************************
    # **         SESSIONS           **
    # ********************************

    @app.get("/api/sessions", response_model=list[SessionListItem])
    def list_sessions():
        """List all monitoring sessions."""
        return service.list_sessions()

    @app.get("/api/session/{session_id}", response_model=SessionDetails)
    def get_session_details(session_id: str):
        """Get detailed information about a specific session."""
        try:
            return service.get_session_details(session_id)
        except ValueError as e:
            raise HTTPException(
                status_code=404 if "not found" in str(e) else 400, detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error getting session details: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ********************************
    # **          CALLS             **
    # ********************************

    @app.get("/api/sessions/{session_id}/calls/{call_index}", response_model=CallData)
    def get_call_data(session_id: int, call_index: int):
        """Get data for a specific function call."""
        try:
            return service.get_call_data(session_id, call_index)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.get(
        "/api/sessions/{session_id}/compare/{comparison_session_id}/calls/{call_index}",
        response_model=dict[str, CallData],
    )
    def compare_call_data(session_id: int, comparison_session_id: int, call_index: int):
        """Compare call data between two sessions."""
        try:
            return service.compare_call_data(
                session_id, call_index, comparison_session_id
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    # ********************************
    # **     STROBOSCOPIC FRAMES    **
    # ********************************

    @app.get(
        "/api/sessions/{session_id}/stroboscopic/{call_index}",
        response_model=list[StroboscopicFrame],
    )
    def get_stroboscopic_frames(
        session_id: int,
        call_index: int,
        ghost_count: int = 4,
        offset: int = 2,
    ):
        """Get stroboscopic frames for a call."""
        try:
            return service.get_stroboscopic_frames(
                session_id, call_index, ghost_count, offset
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ********************************
    # **      STACK RECORDING       **
    # ********************************

    @app.get("/api/stack-recording/{function_id}")
    def get_stack_recording(function_id: str):
        """Get stack recording data for a function call."""
        try:
            # NOTE: Cette méthode lève NotImplementedError dans ExplorerApiService.
            # Si tu veux l'utiliser, il faut l'implémenter dans ExplorerApiService.
            return service.get_stack_recording_data(function_id)
        except NotImplementedError as e:
            raise HTTPException(status_code=501, detail=str(e))
        except ValueError as e:
            raise HTTPException(
                status_code=404 if "not found" in str(e) else 400, detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error getting stack recording: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ********************************
    # **       FUNCTION CALLS       **
    # ********************************

    @app.get("/api/function-calls", response_model=list[FunctionCallModel])
    def get_function_calls(
        search: str | None = Query(
            None, description="Search term to filter function calls"
        ),
        file: str | None = Query(None, description="File filter"),
        function: str | None = Query(None, description="Function name filter"),
    ):
        """Get a list of function calls with optional filtering."""
        try:
            return service.get_function_calls(search, file, function)
        except Exception as e:
            logger.error(f"Error getting function calls: {e}")
            raise HTTPException(status_code=500, detail=str(e))

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

    service = ExplorerApiService(
        game_explorer=GameExplorerFactory.create(
            db_path=db_file,
            pickle_config=PickleConfig(custom_picklers=["pygame"]),
            tracked_function=tracked_function,
            image_metadata_key=image_metadata_key,
        ),
        image_scale=image_scale,
    )

    try:
        app = create_app(service)
        logger.info(f"Starting API server at http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)
    except KeyboardInterrupt:
        logger.info("API server stopped.")
