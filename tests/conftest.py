# import os
# import sys
# import tempfile
# from pathlib import Path
# from unittest.mock import patch

# import pytest
# from fastapi.testclient import TestClient
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker

# sys.path.append(str(Path(__file__).parent.parent))

# from test_globalapi_data import populate_test_database

# from spacetimepy.interface.mcp.api.controller import create_mcp
# from src.spacetimepy.core.models import Base
# from src.spacetimepy.core.representation import PickleConfig

# with patch.object(PickleConfig, "load_custom_picklers", lambda self, module_names: None):
#     pass

# @pytest.fixture(scope="session")
# def db_file():
#     fd, db_path = tempfile.mkstemp(suffix=".db")
#     os.close(fd)
#     yield db_path
#     if os.path.exists(db_path):
#         os.unlink(db_path)

# @pytest.fixture(scope="session")
# def engine(db_file):
#     engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
#     Base.metadata.create_all(engine)
#     yield engine
#     Base.metadata.drop_all(engine)

# @pytest.fixture(scope="function")
# def test_db(engine, db_file):
#     connection = engine.connect()
#     transaction = connection.begin()
#     Session = sessionmaker(bind=connection)
#     session = Session()
#     populate_test_database(session)
#     session.commit()
#     yield session
#     session.close()
#     transaction.rollback()
#     connection.close()

# @pytest.fixture(scope="function")
# def client(test_db, db_file):
#     with patch.object(PickleConfig, "load_custom_picklers", lambda self, module_names: None):
#         app = create_app(db_path=db_file, session=test_db)
#     with TestClient(app) as test_client:
#         yield test_client