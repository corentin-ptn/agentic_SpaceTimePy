import datetime
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session as SqlAlchemySession

from spacetimepy.core import FunctionCall, MonitoringSession, ObjectManager, init_db
from spacetimepy.core.representation import PickleConfig
from spacetimepy.interface.globalapi.api.models import (
    CallData,
    FunctionCallModel,
    MonitoringSessionModel,
    ReplayResult,
    SessionRelationship,
    StroboscopicFrame,
    VariablesData,
)

# *****************************
# **                         **
# **     Helper Functions    **
# **                         **
# *****************************


def sqlalchemy_to_dict(obj: Any) -> dict[str, Any]:
    """Convertit un objet SQLAlchemy en dict, avec sérialisation des datetime."""
    result = {}
    for c in inspect(obj).mapper.column_attrs:
        value = getattr(obj, c.key)
        if isinstance(value, (datetime.datetime, datetime.date)):
            result[c.key] = value.isoformat()
        else:
            result[c.key] = value
    return result


# *****************************
# **                         **
# **      Repositories       **
# **                         **
# *****************************


class BaseRepository:
    def __init__(
        self,
        db_path: str,
        pickle_config: PickleConfig | None = None,
    ):
        self.db_path = db_path
        self.Session = init_db(db_path)
        self.pickle_config = pickle_config or PickleConfig()

    def _get_session(self) -> SqlAlchemySession:
        """Create a new SQLAlchemy session."""
        return self.Session()

    @contextmanager
    def _get_object_manager(self) -> Generator[ObjectManager, None, None]:
        """Context manager pour gérer la session SQLAlchemy et l'ObjectManager."""
        session = self._get_session()
        object_manager = ObjectManager(session, self.pickle_config)
        try:
            yield object_manager
        finally:
            session.close()

    def _rehydrate_refs(
        self,
        refs: dict[str, str],
        object_manager: ObjectManager,
        exclude_unserializable: bool = True,
        prefix_filter: str = "",
    ) -> dict[str, Any]:
        """Rehydrate un dictionnaire de références avec l'ObjectManager."""
        result = {}
        for var_name, ref in refs.items():
            if exclude_unserializable and ref == "<unserializable>":
                continue
            if prefix_filter and var_name.startswith(prefix_filter):
                continue
            try:
                value = object_manager.rehydrate(ref)
                # -----   Conversion des objets Pygame   -----
                value = self._serialize_pygame_object(value)
                # --------------------------------------------
                result[var_name] = value
            except Exception as e:
                result[var_name] = f"Error loading: {e}"
        return result

    def _serialize_pygame_object(self, obj: Any) -> Any:
        """Convertit un objet Pygame en dictionnaire ou chaîne."""

        if isinstance(obj, list):
            return [self._serialize_pygame_object(item) for item in obj]

        if "pygame" not in type(obj).__module__:
            return obj

        type_name = type(obj).__name__

        # Gestion des Rect
        if type_name == "Rect":
            return {
                "type": "pygame.Rect",
                "x": obj.x,
                "y": obj.y,
                "width": obj.width,
                "height": obj.height,
            }
        if type_name == "Surface":
            return {
                "type": "pygame.Surface",
                "width": obj.get_width(),
                "height": obj.get_height(),
            }
        if type_name == "Color":
            return {
                "type": "pygame.Color",
                "r": obj.r,
                "g": obj.g,
                "b": obj.b,
                "a": obj.a,
            }
        if type_name == "Vector2":
            return {
                "type": "pygame.Vector2",
                "x": obj.x,
                "y": obj.y,
            }
        return f"<pygame.{type_name}> (non-serializable)"


class SessionRepository(BaseRepository):
    """Repository to manage sessions (MonitoringSession)."""

    def __init__(
        self,
        db_path,
        pickle_config=None,
        call_repo: "FunctionCallRepository | None" = None,
    ):
        super().__init__(db_path, pickle_config)
        self.call_repo = call_repo

    def get_session(self, session_id: int) -> MonitoringSessionModel | None:
        """Get a session by its id."""
        with self._get_object_manager() as object_manager:
            session = object_manager.session
            session_obj = session.query(MonitoringSession).get(session_id)
            if session_obj:
                session_dict = sqlalchemy_to_dict(session_obj)
                return MonitoringSessionModel(**session_dict)
            return None

    def list_sessions(self) -> dict[int, MonitoringSessionModel]:
        """List all sessions."""
        with self._get_object_manager() as object_manager:
            session = object_manager.session
            sessions = (
                session.query(MonitoringSession)
                .order_by(MonitoringSession.start_time)
                .all()
            )

            sessions_data = {}
            for s in sessions:
                s_dict = sqlalchemy_to_dict(s)
                sessions_data[s.id] = MonitoringSessionModel(**s_dict)
            return sessions_data

    def get_session_relationships(
        self, sessions_data: dict[int, MonitoringSessionModel] | None
    ) -> dict[int, SessionRelationship]:
        """Analyse les relations parent/enfant entre les sessions, avec pagination."""
        with self._get_object_manager() as object_manager:
            session = object_manager.session

            # Initialise les relations pour toutes les sessions
            session_relationships: dict[int, SessionRelationship] = {
                session_id: SessionRelationship(
                    parent_session_id=None,
                    branch_point_call_id=None,
                    branch_point_index=None,
                    child_sessions=[],
                )
                for session_id in sessions_data
            }

            # map entre parent_call_id -> (session_id, order_in_session)
            parent_call_to_info: dict[int, tuple[int, int]] = {}

            size = 100
            for session_id in sessions_data:
                offset = 0
                while True:
                    calls_batch = (
                        session.query(
                            FunctionCall.id,
                            FunctionCall.parent_call_id,
                            FunctionCall.order_in_session,
                        )
                        .filter(FunctionCall.session_id == session_id)
                        .offset(offset)
                        .limit(size)
                        .all()
                    )

                    if not calls_batch:
                        break  # Plus d'appels pour cette session

                    for call in calls_batch:
                        if call.parent_call_id:
                            if call.parent_call_id in parent_call_to_info:
                                parent_session_id, parent_call_order = (
                                    parent_call_to_info[call.parent_call_id]
                                )
                            else:
                                parent_call = (
                                    session.query(
                                        FunctionCall.session_id,
                                        FunctionCall.order_in_session,
                                    )
                                    .filter(FunctionCall.id == call.parent_call_id)
                                    .first()
                                )

                                if parent_call:
                                    parent_session_id = parent_call.session_id
                                    parent_call_order = parent_call.order_in_session
                                    parent_call_to_info[call.parent_call_id] = (
                                        parent_session_id,
                                        parent_call_order,
                                    )
                                else:
                                    continue  # Parent introuvable

                            # Màj de la relation si le parent est dans une autre session
                            if parent_session_id != session_id:
                                session_relationships[
                                    session_id
                                ].parent_session_id = parent_session_id
                                session_relationships[
                                    session_id
                                ].branch_point_call_id = call.parent_call_id
                                session_relationships[
                                    session_id
                                ].branch_point_index = parent_call_order

                    offset += size  # Passe au lot suivant

            # Ajoute les enfants aux parents
            for session_id, rel in session_relationships.items():
                if rel.parent_session_id:
                    parent_id = rel.parent_session_id
                    if parent_id in session_relationships:
                        session_relationships[parent_id].child_sessions.append(
                            session_id
                        )

            return session_relationships


class FunctionCallRepository(BaseRepository):
    """Repository pour gérer les appels de fonction (FunctionCall)."""

    def __init__(
        self, db_path, pickle_config=None, session_repo: SessionRepository | None = None
    ):
        super().__init__(db_path, pickle_config)
        self.session_repo = session_repo

    def get_calls_by_session_paginated(
        self,
        session_id: int,
        tracked_function: str | None = None,
        size: int = 50,
        offset: int = 0,
    ) -> list[FunctionCallModel]:
        """Récupère une page d'appels d'une session, avec pagination."""
        with self._get_object_manager() as object_manager:
            session = object_manager.session
            query = session.query(FunctionCall).filter(
                FunctionCall.session_id == session_id
            )
            if tracked_function:
                query = query.filter(FunctionCall.function == tracked_function)
            query = query.order_by(FunctionCall.order_in_session)
            calls = query.offset(offset).limit(size).all()
            return [FunctionCallModel(**sqlalchemy_to_dict(c)) for c in calls]

    def get_all_calls_by_session_paginated(
        self,
        session_id: int,
        tracked_function: str | None = None,
        size: int = 50,
    ) -> Generator[list[FunctionCallModel], None, None]:
        """Générateur pour récupérer tous les appels d'une session par lots de taille `size`."""
        offset = 0
        while True:
            calls = self.get_calls_by_session_paginated(
                session_id, tracked_function, size, offset
            )
            if not calls:
                break
            yield calls
            offset += size

    def get_call(self, call_id: int) -> FunctionCallModel | None:
        """Récupère un appel par son ID."""
        with self._get_object_manager() as object_manager:
            session = object_manager.session
            call = session.query(FunctionCall).get(call_id)
            if call:
                call_dict = sqlalchemy_to_dict(call)
                return FunctionCallModel(**call_dict)
            return None

    def get_calls_by_session(
        self,
        session_id: int,
        tracked_function: str | None = None,
        size: int = 50,
    ) -> list[FunctionCallModel]:
        """Récupère tous les appels d'une session en utilisant la pagination."""
        all_calls = []
        for calls_page in self.get_all_calls_by_session_paginated(
            session_id, tracked_function, size
        ):
            all_calls.extend(calls_page)
        return all_calls

    def get_call_data(
        self,
        session_id: int,
        call_index: int,
        tracked_function: str = "display_game",
        image_metadata_key: str = "image",
    ) -> CallData | None:
        """Récupère les données d'un appel spécifique (avec variables et image)."""
        calls = self.get_calls_by_session(session_id, tracked_function)
        if call_index < 0 or call_index >= len(calls):
            return None

        call = calls[call_index]

        with self._get_object_manager() as object_manager:
            # Récupère l'image
            image_data = None
            if call.call_metadata and image_metadata_key in call.call_metadata:
                image_data = call.call_metadata[image_metadata_key]

            # Rehydrate les variables
            variables = VariablesData()
            if call.locals_refs:
                variables.locals = self._rehydrate_refs(
                    call.locals_refs, object_manager
                )
            if call.globals_refs:
                variables.globals = self._rehydrate_refs(
                    call.globals_refs, object_manager, prefix_filter="__"
                )

            return CallData(
                image_data=image_data,
                variables=variables,
                call_id=call.id,
                start_time=call.start_time,
                session_id=session_id,
                call_index=call_index,
                file=call.file,
                line=call.line,
                function=call.function,
                code_definition_id=call.code_definition_id,
            )

    def get_call_count(
        self,
        session_id: int,
    ) -> int:
        with self._get_object_manager() as object_manager:
            session = object_manager.session
            return (
                session.query(FunctionCall)
                .where(FunctionCall.session_id == session_id)
                .count()
            )


    # TODO: peut etre à enlever ?  | voir comment trouver les bons index !!!!
    def get_comparison_call_data(
        self,
        current_session_id: int,
        current_call_index: int,
        comparison_session_id: int,
        tracked_function: str = "display_game",
        image_metadata_key: str = "image",
    ) -> CallData | None:
        """Récupère les données d'un appel de comparaison."""
        if not comparison_session_id:
            return None

        if not self.session_repo:
            self.session_repo = SessionRepository(self.db_path, self.pickle_config)
        sessions_data = self.session_repo.list_sessions()
        session_relationships = self.session_repo.get_session_relationships(
            sessions_data
        )

        # si 'current' est le pere de 'comparaison'
        comparison_rel = session_relationships.get(
            comparison_session_id, SessionRelationship()
        )
        if comparison_rel.parent_session_id == current_session_id:
            return self.get_call_data(
                current_session_id,
                current_call_index,
                tracked_function,
                image_metadata_key,
            )

        # si 'current' est le fils de 'comparaison'
        current_rel = session_relationships.get(
            current_session_id, SessionRelationship()
        )
        if current_rel.parent_session_id == comparison_session_id:
            return self.get_call_data(
                comparison_session_id,
                current_call_index,
                tracked_function,
                image_metadata_key,
            )

        return None

    # TODO: peut etre à enlever ?
    def get_stroboscopic_frames(
        self,
        session_id: int,
        current_call_index: int,
        tracked_function: str = "display_game",
        image_metadata_key: str = "image",
        ghost_count: int = 4,
        offset: int = 2,
        start_pos: int = 0,
    ) -> list[StroboscopicFrame]:
        """Récupère les cadres pour l'effet stroboscopique."""
        if not self.session_repo:
            self.session_repo = SessionRepository(self.db_path, self.pickle_config)
        sessions_data = self.session_repo.list_sessions(tracked_function)

        if session_id not in sessions_data:
            return []

        calls = sessions_data[session_id].calls
        stroboscopic_frames = []
        total_frames = ghost_count * offset

        if start_pos <= -50:
            start_index = max(0, current_call_index - total_frames)
            end_index = current_call_index
        elif start_pos >= 50:
            start_index = current_call_index + 1
            end_index = min(len(calls), current_call_index + total_frames + 1)
        else:
            past_bias = (50 - start_pos) / 100.0
            past_frames = int(total_frames * past_bias)
            future_frames = total_frames - past_frames
            start_index = max(0, current_call_index - past_frames)
            end_index = min(len(calls), current_call_index + future_frames + 1)

        frame_indices = []
        for i in range(start_index, end_index, offset):
            if i != current_call_index:
                frame_indices.append(i)

        if len(frame_indices) > ghost_count:
            step = len(frame_indices) / ghost_count
            frame_indices = [frame_indices[int(i * step)] for i in range(ghost_count)]

        for i in frame_indices:
            if 0 <= i < len(calls):
                frame_data = self.get_call_data(
                    session_id, i, tracked_function, image_metadata_key
                )
                if frame_data and frame_data.image_data:
                    stroboscopic_frames.append(
                        StroboscopicFrame(
                            call_index=i,
                            call_id=frame_data.call_id,
                            image_data=frame_data.image_data,
                        )
                    )

        return stroboscopic_frames


class ReplayRepository(BaseRepository):
    """Repository pour gérer les opérations de replay."""

    def __init__(
        self,
        db_path,
        pickle_config=None,
        call_repo: FunctionCallRepository | None = None,
    ):
        super().__init__(db_path, pickle_config)
        self.call_repo = call_repo

    def replay_all(
        self,
        session_id: int,
        tracked_function: str = "display_game",
        ignored_globals: list[str] | None = None,
        mocked_functions: list[str] | None = None,
    ) -> ReplayResult:
        """Rejoue une session depuis le début."""
        with self._get_object_manager() as object_manager:
            session = object_manager.session
            session_obj = session.query(MonitoringSession).get(session_id)
            if not session_obj:
                return ReplayResult(new_branch_id=None, error="Session not found")

            if not self.call_repo:
                self.call_repo = FunctionCallRepository(
                    self.db_path, self.pickle_config
                )
            calls = self.call_repo.get_calls_by_session(session_id, tracked_function)
            if not calls:
                return ReplayResult(new_branch_id=None, error="No calls found")

            first_call_id = calls[0].id

            try:
                from spacetimepy.core.monitoring import init_monitoring
                from spacetimepy.core.reanimation import replay_session_sequence
                from spacetimepy.core.session import end_session, start_session

                init_monitoring(db_path=self.db_path, custom_picklers=["pygame"])
                replay_session = start_session(f"Replay of Session {session_id}")
                if replay_session:
                    new_branch_id = replay_session_sequence(
                        first_call_id,
                        self.db_path,
                        ignore_globals=ignored_globals or [],
                        mock_functions=mocked_functions or [],
                    )
                    end_session()
                    return ReplayResult(new_branch_id=new_branch_id, error=None)
                return ReplayResult(
                    new_branch_id=None, error="Failed to start replay session"
                )
            except Exception as e:
                return ReplayResult(new_branch_id=None, error=str(e))

    def replay_from_call(
        self,
        session_id: int,
        call_index: int,
        tracked_function: str = "display_game",
        ignored_globals: list[str] | None = None,
        mocked_functions: list[str] | None = None,
    ) -> ReplayResult:
        """Rejoue une session depuis un appel spécifique."""
        if not self.call_repo:
            self.call_repo = FunctionCallRepository(self.db_path, self.pickle_config)
        calls = self.call_repo.get_calls_by_session(session_id, tracked_function)
        if call_index < 0 or call_index >= len(calls):
            return ReplayResult(new_branch_id=None, error="Invalid call index")

        call_id = calls[call_index].id

        try:
            from spacetimepy.core.monitoring import init_monitoring
            from spacetimepy.core.reanimation import replay_session_sequence
            from spacetimepy.core.session import end_session, start_session

            init_monitoring(db_path=self.db_path, custom_picklers=["pygame"])
            replay_session = start_session(
                f"Replay from Session {session_id} Frame {call_index + 1}"
            )
            if replay_session:
                new_branch_id = replay_session_sequence(
                    call_id,
                    self.db_path,
                    ignore_globals=ignored_globals or [],
                    mock_functions=mocked_functions or [],
                )
                end_session()
                return ReplayResult(new_branch_id=new_branch_id, error=None)
            return ReplayResult(
                new_branch_id=None, error="Failed to start replay session"
            )
        except Exception as e:
            return ReplayResult(new_branch_id=None, error=str(e))

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
        if not self.call_repo:
            self.call_repo = FunctionCallRepository(self.db_path, self.pickle_config)
        calls = self.call_repo.get_calls_by_session(session_id, tracked_function)
        if not calls:
            return ReplayResult(new_branch_id=None, error="No calls found")

        start_call_index = max(0, min(start_call_index, len(calls) - 1))
        end_call_index = max(0, min(end_call_index, len(calls) - 1))
        if start_call_index > end_call_index:
            start_call_index, end_call_index = end_call_index, start_call_index

        start_call_id = calls[start_call_index].id
        end_call_id = calls[end_call_index].id

        try:
            from spacetimepy.core.monitoring import init_monitoring
            from spacetimepy.core.reanimation import replay_session_subsequence
            from spacetimepy.core.session import end_session, start_session

            init_monitoring(db_path=self.db_path, custom_picklers=["pygame"])
            replay_session = start_session(
                f"Replay subsequence from Session {session_id} Frames {start_call_index + 1}-{end_call_index + 1}"
            )
            if replay_session:
                new_branch_id = replay_session_subsequence(
                    start_call_id,
                    end_call_id,
                    self.db_path,
                    ignore_globals=ignored_globals or [],
                    mock_functions=mocked_functions or [],
                )
                end_session()
                return ReplayResult(new_branch_id=new_branch_id, error=None)
            return ReplayResult(
                new_branch_id=None, error="Failed to start replay session"
            )
        except Exception as e:
            return ReplayResult(new_branch_id=None, error=str(e))
