import datetime
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session as SqlAlchemySession

from spacetimepy.core import ObjectManager, init_db
from spacetimepy.core.representation import PickleConfig


def sqlalchemy_to_dict(obj: Any) -> dict[str, Any]:
    """Convert an SQLAlchemy object into a dictionary, with serialization of datetime."""
    if obj is None:
        return None
    result = {}
    for c in inspect(obj).mapper.column_attrs:
        value = getattr(obj, c.key)
        if isinstance(value, (datetime.datetime, datetime.date)):
            result[c.key] = value.isoformat()
        else:
            result[c.key] = value
    return result


class BaseRepository:
    """An 'abstract' class for the differents Repository, manages the session and object manager creation"""

    def __init__(
        self,
        db_path: str,
        pickle_config: PickleConfig | None = None,
        session: SqlAlchemySession | None = None,
    ):
        """
        Args:
            db_path (str): the sqlite database path
            pickle_config (PickleConfig | None): a pickle config (can be for the module `["pygame"]` if the database contains pygame objects)
            session (SqlAlchemySession | None): a session if a database is already loaded and can be shared between repositories.
        """
        self.db_path = db_path
        self.Session = init_db(db_path)  # default session
        self.pickle_config = pickle_config or PickleConfig()
        self.external_session = session  # external session (optional)

    @contextmanager
    def _get_session(self) -> Generator[SqlAlchemySession, None, None]:
        """Retrieve and manage a SqlAlchemySession"""
        if self.external_session:
            yield self.external_session
        else:
            session = self.Session()
            try:
                yield session
            finally:
                session.close()

    @contextmanager
    def _get_object_manager(self) -> Generator[ObjectManager, None, None]:
        """Retrieve and manage an ObjectManager depending on a SQLAlchemy."""
        with self._get_session() as session:
            object_manager = ObjectManager(session, self.pickle_config)
            yield object_manager
