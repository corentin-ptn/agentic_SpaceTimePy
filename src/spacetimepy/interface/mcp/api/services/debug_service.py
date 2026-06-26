import requests

from spacetimepy.interface.mcp.api.models.models import LaunchDebugRequest


class DebugService:
    """Service to start debugging sesions with spacetimepy."""

    def start_debug_session(
        self,
        launch_debug_request: LaunchDebugRequest,
        ip: str = "localhost",
        port: int = 3000,
    ) -> bool:
        """
        Modify the current debug session to load the state of the snapshot Id
        and place the debugger to the snapshot line corresponding.

        Args:
            launch_debug_request (LaunchDebugRequest): The request containing the details for starting the debug session.
            ip (str): The IP address of the target machine.
            port (int): The port number of the target machine.

        Returns:
            bool: True if the request succeed, an error otherwise
        """

        # Utilisation de http par défaut pour le debug local
        url = f"http://{ip}:{port}/startDebugSession"

        params = {
            "filePath": launch_debug_request.file_path,
            "functionName": launch_debug_request.function_name,
            "range": {
                "start": {
                    "line": launch_debug_request.range.start.line,
                    "character": launch_debug_request.range.start.character,
                },
                "end": {
                    "line": launch_debug_request.range.end.line,
                    "character": launch_debug_request.range.end.character,
                },
            },
            "paramValues": [
                [p.name, p.value] for p in launch_debug_request.paramValues
            ],
            "useReanimation": launch_debug_request.use_reanimation,
            "selectedFunctionCallId": launch_debug_request.selected_function_call_id,
        }

        try:
            response = requests.post(url, json=params, timeout=30)
            response.raise_for_status()
            print(f"Debug session started successfully: {response.text}")
            return True
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            if e.response is not None:
                try:
                    json_data = e.response.json()
                    error_msg = (
                        json_data.get("details")
                        or json_data.get("error")
                        or e.response.text
                    )
                except Exception:
                    error_msg = e.response.text

            print(f"HTTP Error starting debug session: {error_msg}")
            raise Exception(f"Server returned error: {error_msg}") from e
        except requests.exceptions.RequestException as e:
            print(f"Error starting debug session: {e}")
            raise
