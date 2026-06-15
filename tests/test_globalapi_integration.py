# from fastapi import status


# class TestIntegration:
#     """Tests d'intégration pour l'API SpaceTimePy."""

#     def test_db_info(self, client):
#         """Test l'endpoint /api/db-info."""
#         response = client.get("/api/db-info")
#         assert response.status_code == status.HTTP_200_OK
#         assert "db_path" in response.json()

#     def test_list_sessions(self, client):
#         """Test l'endpoint /api/sessions."""
#         response = client.get("/api/sessions")
#         assert response.status_code == status.HTTP_200_OK
#         sessions = response.json()
#         print(sessions)
#         assert isinstance(sessions, list)
#         assert len(sessions) == 2  # 2 sessions dans test_mcp_data.py
#         assert sessions[0]["id"] == 1
#         assert sessions[1]["id"] == 2

#     def test_get_session_details(self, client):
#         """Test l'endpoint /api/session/{session_id}."""
#         # Test avec une session existante
#         response = client.get("/api/session/1")
#         assert response.status_code == status.HTTP_200_OK
#         session = response.json()
#         assert session["id"] == 1
#         assert session["name"] == "Test Session 1"
#         assert "call_count" in session  # Vérifie que call_count est présent
#         assert session["call_count"] == 2

#         # Test avec une session non existante
#         response = client.get("/api/session/999")
#         assert response.status_code == status.HTTP_404_NOT_FOUND
#         assert "not found" in response.json()["detail"]

#     def test_get_call_data(self, client):
#         """Test l'endpoint /api/sessions/{session_id}/calls/{call_index}."""
#         # Test avec un appel existant (session 1, call_index 0)
#         response = client.get("/api/sessions/1/calls/0")
#         assert response.status_code == status.HTTP_200_OK
#         call = response.json()
#         assert call["id"] == 1
#         assert call["function"] == "test_function_1"

#         # Test avec un call_index hors limites
#         response = client.get("/api/sessions/1/calls/999")
#         assert response.status_code == status.HTTP_404_NOT_FOUND
#         assert "not found" in response.json()["detail"]

#     def test_get_execution_tree(self, client):
#         """Test l'endpoint /api/execution-tree/{call_id}."""
#         # Test avec un appel existant (call_id 1)
#         response = client.get("/api/execution-tree/1")
#         assert response.status_code == status.HTTP_200_OK
#         tree = response.json()
#         assert tree["id"] == 1
#         assert tree["function"] == "test_function_1"
#         assert "children" in tree

#         # Test avec un appel non existant
#         response = client.get("/api/execution-tree/999")
#         assert response.status_code == status.HTTP_404_NOT_FOUND
#         assert "function call 999 not found" in response.json()["detail"]

#         # Test avec max_depth
#         response = client.get("/api/execution-tree/1?max_depth=1")
#         assert response.status_code == status.HTTP_200_OK
#         tree = response.json()
#         assert tree["id"] == 1
#         assert "children" in tree

#     def test_session_relationships(self, client):
#         """Test que les relations entre sessions sont correctement calculées."""
#         response = client.get("/api/sessions")
#         assert response.status_code == status.HTTP_200_OK
#         sessions = response.json()
#         assert len(sessions) == 2

#         # Vérifie que les relations sont présentes
#         for session in sessions:
#             assert "relations" in session
#             assert "parent_session_id" in session["relations"]
#             assert "child_sessions" in session["relations"]
