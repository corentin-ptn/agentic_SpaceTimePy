from dataclasses import asdict

import requests

from spacetimepy.interface.mcp.api.models.dto import (
    StackSnapshotDTO,
    StackSnapshotEdgeDTO,
)
from spacetimepy.interface.mcp.api.models.models import StackSnapshotDetails
from spacetimepy.interface.mcp.api.repositories.object_identity_repository import (
    StoredObjectRepository,
)
from spacetimepy.interface.mcp.api.repositories.stack_snapshot_repository import (
    StackSnapshotEdgeRepository,
    StackSnapshotRepository,
)


class SnapshotService:
    """Service to manage snapshots and their logic."""

    def __init__(
        self,
        snapshot_repo: StackSnapshotRepository,
        object_repo: StoredObjectRepository,
    ):
        self.snapshot_repo = snapshot_repo
        self.object_repo = object_repo

    # --- Direct calls to repository ---

    def get_snapshot(self, snapshot_id: int) -> StackSnapshotDetails | None:
        """Retrieve a snapshot by its ID."""
        return (
            StackSnapshotDetails.from_dict(
                {
                    **asdict(self.snapshot_repo.get_snapshot(snapshot_id)),
                    "locals_var": {
                        k: self.object_repo.get_object(v).pickle_data
                        for k, v in self.snapshot_repo.get_snapshot(
                            snapshot_id
                        ).locals_refs.items()
                    },
                }
            )
            if self.snapshot_repo.get_snapshot(snapshot_id)
            else None
        )

    def list_snapshots_by_call(self, function_call_id: int) -> list[StackSnapshotDTO]:
        """List all snapshots depending of a function call."""
        return self.snapshot_repo.list_snapshots_by_call(function_call_id)

    def snapshot_detailed_list_by_call(
        self, function_call_id: int
    ) -> list[StackSnapshotDetails]:
        """List all snapshots depending of a function call."""
        f = [
            StackSnapshotDetails.from_dict(
                {
                    **asdict(snapshot),
                    "locals_var": {
                        k: self.object_repo.get_object(v).pickle_data
                        for k, v in snapshot.locals_refs.items()
                    },
                }
            )
            for snapshot in self.snapshot_repo.list_snapshots_by_call(function_call_id)
        ]
        print(f)
        return f

    def get_previous_snapshot(self, snapshot_id: int) -> StackSnapshotDTO | None:
        """Retrieve the predecessor snapshot."""
        return self.snapshot_repo.get_previous_snapshot(snapshot_id)

    def get_successors(
        self, snapshot_id: int, edge_type: str | None = None
    ) -> list[StackSnapshotDTO]:
        """Retreive the list of nexts snapshots."""
        if edge_type == "":
            edge_type = None
        return self.snapshot_repo.get_successors(snapshot_id, edge_type)

    def get_snapshot_count_by_call(self, function_call_id: int) -> int:
        """Retrieve the number of snapshots for a function call."""
        return self.snapshot_repo.get_snapshot_count_by_call(function_call_id)

    # --- Domain logic ---

    def load_snapshot(
        self, snapshot_id: int, ip: str = "localhost", port: int = 3000
    ) -> bool:
        """
        Modify the current debug session to load the state of the snapshot Id
        and place the debugger to the snapshot line corresponding.

        Args:
            snapshot_id (int): The ID of the snapshot to load.
            ip (str): The IP address of the target machine.
            port (int): The port of the target machine.

        Returns:
            bool: True if the request succeed, an error otherwise
        """
        target_snapshot = self.snapshot_repo.get_snapshot(snapshot_id)
        if not target_snapshot:
            raise ValueError("snapshot not found")

        # Utilisation de http par défaut pour le debug local
        url = f"http://{ip}:{port}/execute/goToSnapshotState"

        params = {
            "snapshotId": snapshot_id,
            "dbPath": self.snapshot_repo.db_path,
            "targetLine": target_snapshot.line_number,
        }

        try:
            response = requests.post(url, json=params, timeout=5)
            response.raise_for_status()
            print(f"Snapshot loaded successfully: {response.text}")
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

            print(f"HTTP Error loading snapshot: {error_msg}")
            raise Exception(f"Server returned error: {error_msg}") from e
        except requests.exceptions.RequestException as e:
            print(f"Error loading snapshot: {e}")
            raise


class SnapshotEdgeService:
    """Service to manage snapshots edges and their logic."""

    def __init__(
        self,
        snapshot_edge_repo: StackSnapshotEdgeRepository,
    ):
        self.snapshot_edge_repo = snapshot_edge_repo

    def get_edge(self, edge_id: int) -> StackSnapshotEdgeDTO | None:
        """Retrieve an edge by its ID."""
        return self.snapshot_edge_repo.get_edge(edge_id)

    def list_edges_by_type(self, edge_type: str) -> list[StackSnapshotEdgeDTO]:
        """Retrieve all edges of a specific type."""
        return self.snapshot_edge_repo.list_edges_by_type(edge_type)
