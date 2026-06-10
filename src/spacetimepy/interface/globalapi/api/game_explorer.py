#!/usr/bin/env python3
"""
Game Explorer - Stateless Core Logic for Session and Call Management
"""

from datetime import datetime

from spacetimepy.core.representation import PickleConfig
from spacetimepy.interface.globalapi.api.models import (
    CallData,
    ReplayResult,
    SessionDetails,
    SessionListItem,
    SessionRelationship,
    StroboscopicFrame,
)
from spacetimepy.interface.globalapi.api.repositories import (
    FunctionCallRepository,
    ReplayRepository,
    SessionRepository,
)


def _serialize_datetime(value: datetime | str | None) -> str | None:
    """Convertit un datetime en ISO format (pour l'API)."""
    if isinstance(value, datetime):
        return value.isoformat() if value else None
    if isinstance(value, str):
        return value if value else None
    return None


class GameExplorer:
    """
    API stateless pour gérer et rejouer des sessions de jeu.
    Utilise le Repository Pattern pour accéder aux données.
    """

    def __init__(
        self,
        db_path: str,
        session_repo: SessionRepository,
        call_repo: FunctionCallRepository,
        replay_repo: ReplayRepository,
        tracked_function: str | None = None,
        image_metadata_key: str | None = None,
    ):
        """
        Initialise GameExplorer avec les repositories nécessaires.

        Args:
            db_path: Chemin vers la base de données.
        """
        self.db_path = db_path
        self.session_repo = session_repo
        self.call_repo = call_repo
        self.replay_repo = replay_repo
        self.tracked_function = tracked_function
        self.image_metadata_key = image_metadata_key

    def list_sessions(self) -> list[SessionListItem]:
        """Liste toutes les sessions avec leurs appels suivis."""
        sessions_data = self.session_repo.list_sessions(self.tracked_function)
        session_relationships = self.session_repo.get_session_relationships(
            sessions_data
        )

        sessions = []
        for session_id, data in sessions_data.items():
            relationship = session_relationships.get(session_id, SessionRelationship())
            sessions.append(
                SessionListItem(
                    session_id=session_id,
                    name=data.session.name or f"Session {session_id}",
                    start_time=data.session.start_time,
                    call_count=len(data.calls),
                    is_branch=relationship.parent_session_id is not None,
                    parent_session_id=relationship.parent_session_id,
                    branch_point_index=relationship.branch_point_index,
                    child_sessions=relationship.child_sessions,
                )
            )
        return sessions

    def get_session_details(self, session_id: int) -> SessionDetails | None:
        """Récupère les détails complets d'une session."""
        sessions_data = self.session_repo.list_sessions(self.tracked_function)
        if session_id not in sessions_data:
            return None

        data = sessions_data[session_id]
        calls = []
        for call_index in range(len(data.calls)):
            call_data = self.call_repo.get_call_data(
                session_id, call_index, self.tracked_function, self.image_metadata_key
            )
            if call_data:
                calls.append(call_data)

        return SessionDetails(
            id=session_id,
            name=data.session.name,
            start_time=_serialize_datetime(data.session.start_time),
            end_time=(
                _serialize_datetime(data.session.end_time)
                if data.session.end_time
                else None
            ),
            call_count=len(calls),
            calls=calls,
        )

    def get_call_data(
        self,
        session_id: int,
        call_index: int,
    ) -> CallData | None:
        """Récupère les données d'un appel spécifique."""
        return self.call_repo.get_call_data(
            session_id, call_index, self.tracked_function, self.image_metadata_key
        )

    def get_comparison_call_data(
        self,
        current_session_id: int,
        current_call_index: int,
        comparison_session_id: int,
    ) -> CallData | None:
        """Récupère les données d'un appel de comparaison."""
        return self.call_repo.get_comparison_call_data(
            current_session_id,
            current_call_index,
            comparison_session_id,
            self.tracked_function,
            self.image_metadata_key,
        )

    def get_stroboscopic_frames(
        self,
        session_id: int,
        current_call_index: int,
        ghost_count: int = 4,
        offset: int = 2,
        start_pos: int = 0,
    ) -> list[StroboscopicFrame]:
        """Récupère les cadres pour l'effet stroboscopique."""
        return self.call_repo.get_stroboscopic_frames(
            session_id,
            current_call_index,
            self.tracked_function,
            self.image_metadata_key,
            ghost_count,
            offset,
            start_pos,
        )

    def replay_all(
        self,
        session_id: int,
        ignored_globals: list[str] | None = None,
        mocked_functions: list[str] | None = None,
    ) -> ReplayResult:
        """Rejoue une session depuis le début."""
        return self.replay_repo.replay_all(
            session_id,
            self.tracked_function,
            ignored_globals,
            mocked_functions,
        )

    def replay_from_call(
        self,
        session_id: int,
        call_index: int,
        ignored_globals: list[str] | None = None,
        mocked_functions: list[str] | None = None,
    ) -> ReplayResult:
        """Rejoue une session depuis un appel spécifique."""
        return self.replay_repo.replay_from_call(
            session_id,
            call_index,
            self.tracked_function,
            ignored_globals,
            mocked_functions,
        )

    def replay_subsequence(
        self,
        session_id: int,
        start_call_index: int,
        end_call_index: int,
        tracked_function: str = "display_game",
        ignored_globals: list[str] | None = None,
        mocked_functions: list[str] | None = None,
    ) -> ReplayResult:
        """Rejoue une sous-séquence d'appels."""
        return self.replay_repo.replay_subsequence(
            session_id,
            start_call_index,
            end_call_index,
            tracked_function,
            ignored_globals,
            mocked_functions,
        )


class GameExplorerFactory:
    @staticmethod
    def create(
        db_path: str,
        tracked_function: str | None = None,
        image_metadata_key: str | None = None,
        pickle_config: PickleConfig | None = None,
    ) -> GameExplorer:
        session_repo = SessionRepository(db_path, pickle_config)
        call_repo = FunctionCallRepository(db_path, pickle_config, session_repo)
        replay_repo = ReplayRepository(db_path, pickle_config, call_repo)

        session_repo.call_repo = call_repo

        return GameExplorer(
            db_path=db_path,
            session_repo=session_repo,
            call_repo=call_repo,
            replay_repo=replay_repo,
            tracked_function=tracked_function,
            image_metadata_key=image_metadata_key,
        )
