# from datetime import datetime

# from spacetimepy.core.models import (
#     CodeDefinition,
#     FunctionCall,
#     MonitoringSession,
#     StackSnapshot,
# )

# # Données pour MonitoringSession
# TEST_SESSIONS = [
#     {
#         "id": 1,
#         "name": "Test Session 1",
#         "description": "First test session",
#         "start_time": datetime(2023, 1, 1, 10, 0, 0),
#         "end_time": datetime(2023, 1, 1, 11, 0, 0),
#         "session_metadata": {"key": "value"},
#     },
#     {
#         "id": 2,
#         "name": "Test Session 2",
#         "description": "Second test session",
#         "start_time": datetime(2023, 1, 2, 10, 0, 0),
#         "end_time": datetime(2023, 1, 2, 11, 0, 0),
#         "session_metadata": {"key": "value2"},
#     },
# ]

# # Données pour FunctionCall
# TEST_FUNCTION_CALLS = [
#     {
#         "id": 1,
#         "function": "test_function_1",
#         "file": "test_file_1.py",
#         "line": 10,
#         "start_time": datetime(2023, 1, 1, 10, 0, 0),
#         "end_time": datetime(2023, 1, 1, 10, 0, 1),
#         "call_metadata": {"metadata": "value"},
#         "locals_refs": {"var1": "ref1"},
#         "globals_refs": {"var2": "ref2"},
#         "return_ref": "return_ref_1",
#         "code_definition_id": "code_def_1",
#         "session_id": 1,
#         "parent_call_id": None,
#         "order_in_parent": 0,
#         "order_in_session": 0,
#         "first_snapshot_id": 1,
#     },
#     {
#         "id": 2,
#         "function": "test_function_2",
#         "file": "test_file_2.py",
#         "line": 20,
#         "start_time": datetime(2023, 1, 1, 10, 0, 1),
#         "end_time": datetime(2023, 1, 1, 10, 0, 2),
#         "call_metadata": {"metadata": "value2"},
#         "locals_refs": {"var3": "ref3"},
#         "globals_refs": {"var4": "ref4"},
#         "return_ref": "return_ref_2",
#         "code_definition_id": "code_def_2",
#         "session_id": 1,
#         "parent_call_id": 1,
#         "order_in_parent": 0,
#         "order_in_session": 1,
#         "first_snapshot_id": 2,
#     },
#     {
#         "id": 3,
#         "function": "test_function_1",
#         "file": "test_file_1.py",
#         "line": 10,
#         "start_time": datetime(2023, 1, 2, 10, 0, 0),
#         "end_time": datetime(2023, 1, 2, 10, 0, 1),
#         "call_metadata": {"metadata": "value3"},
#         "locals_refs": {"var5": "ref5"},
#         "globals_refs": {"var6": "ref6"},
#         "return_ref": "return_ref_3",
#         "code_definition_id": "code_def_1",
#         "session_id": 2,
#         "parent_call_id": None,
#         "order_in_parent": 0,
#         "order_in_session": 0,
#         "first_snapshot_id": 3,
#     },
# ]

# # Données pour CodeDefinition
# TEST_CODE_DEFINITIONS = [
#     {
#         "id": "code_def_1",
#         "name": "test_function_1",
#         "type": "function",
#         "module_path": "test_module_1",
#         "code_content": "def test_function_1(): pass",
#         "first_line_no": 1,
#         "creation_time": datetime(2023, 1, 1),
#     },
#     {
#         "id": "code_def_2",
#         "name": "test_function_2",
#         "type": "function",
#         "module_path": "test_module_2",
#         "code_content": "def test_function_2(): pass",
#         "first_line_no": 1,
#         "creation_time": datetime(2023, 1, 1),
#     },
# ]

# # Données pour StackSnapshot
# TEST_STACK_SNAPSHOTS = [
#     {
#         "id": 1,
#         "function_call_id": 1,
#         "code_definition_id": "code_def_1",
#         "line_number": 10,
#         "timestamp": datetime(2023, 1, 1, 10, 0, 0),
#         "locals_refs": {"var1": "ref1"},
#         "globals_refs": {"var2": "ref2"},
#         "order_in_call": 0,
#         "next_snapshot_id": 2,
#     },
#     {
#         "id": 2,
#         "function_call_id": 1,
#         "code_definition_id": "code_def_1",
#         "line_number": 11,
#         "timestamp": datetime(2023, 1, 1, 10, 0, 0),
#         "locals_refs": {"var1": "ref1_updated"},
#         "globals_refs": {"var2": "ref2_updated"},
#         "order_in_call": 1,
#         "next_snapshot_id": None,
#     },
#     {
#         "id": 3,
#         "function_call_id": 2,
#         "code_definition_id": "code_def_2",
#         "line_number": 20,
#         "timestamp": datetime(2023, 1, 1, 10, 0, 1),
#         "locals_refs": {"var3": "ref3"},
#         "globals_refs": {"var4": "ref4"},
#         "order_in_call": 0,
#         "next_snapshot_id": None,
#     },
#     {
#         "id": 4,
#         "function_call_id": 3,
#         "code_definition_id": "code_def_1",
#         "line_number": 10,
#         "timestamp": datetime(2023, 1, 2, 10, 0, 0),
#         "locals_refs": {"var5": "ref5"},
#         "globals_refs": {"var6": "ref6"},
#         "order_in_call": 0,
#         "next_snapshot_id": None,
#     },
# ]


# def populate_test_database(session):
#     """Peuple la base de données avec des données de test."""
#     # Ajoute les sessions
#     for session_data in TEST_SESSIONS:
#         session_obj = MonitoringSession(**session_data)
#         session.add(session_obj)

#     # Ajoute les définitions de code
#     for code_def_data in TEST_CODE_DEFINITIONS:
#         code_def_obj = CodeDefinition(**code_def_data)
#         session.add(code_def_obj)

#     # Ajoute les appels de fonction
#     for call_data in TEST_FUNCTION_CALLS:
#         call_obj = FunctionCall(**call_data)
#         session.add(call_obj)

#     # Ajoute les snapshots
#     for snapshot_data in TEST_STACK_SNAPSHOTS:
#         snapshot_obj = StackSnapshot(**snapshot_data)
#         session.add(snapshot_obj)

#     session.commit()
