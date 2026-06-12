from typing import Any

from spacetimepy.core.models import StackSnapshot, StackSnapshotEdge
from spacetimepy.interface.globalapi.api.models.dto import (
    StackSnapshotDTO,
    StackSnapshotEdgeDTO,
)

from .base_repository import BaseRepository, sqlalchemy_to_dict


class StackSnapshotRepository(BaseRepository):
    def get_snapshot(self, snapshot_id: int) -> StackSnapshotDTO | None:
        """Récupère un snapshot par son ID."""
        with self._get_session() as session:
            snapshot = session.query(StackSnapshot).get(snapshot_id)
            if not snapshot:
                return None
            return StackSnapshotDTO(**sqlalchemy_to_dict(snapshot))

    def list_snapshots_by_call(self, function_call_id: int) -> list[StackSnapshotDTO]:
        """Liste tous les snapshots pour un appel de fonction."""
        with self._get_session() as session:
            snapshots = (
                session.query(StackSnapshot)
                .filter(StackSnapshot.function_call_id == function_call_id)
                .order_by(StackSnapshot.timestamp)
                .all()
            )
            return [StackSnapshotDTO(**sqlalchemy_to_dict(s)) for s in snapshots]

    def get_previous_snapshot(self, snapshot_id: int) -> StackSnapshotDTO | None:
        """Récupère le snapshot précédent dans la trace."""
        with self._get_session() as session:
            snapshot = session.query(StackSnapshot).get(snapshot_id)
            if not snapshot:
                return None
            previous = snapshot.get_previous_snapshot(session)
            if not previous:
                return None
            return StackSnapshotDTO(**sqlalchemy_to_dict(previous))

    def get_successors(
        self, snapshot_id: int, edge_type: str | None = None
    ) -> list[StackSnapshotDTO]:
        """Récupère les snapshots successeurs."""
        with self._get_session() as session:
            snapshot = session.query(StackSnapshot).get(snapshot_id)
            if not snapshot:
                return []
            successors = snapshot.get_successors(session, edge_type)
            return [StackSnapshotDTO(**sqlalchemy_to_dict(s)) for s in successors]


class StackSnapshotEdgeRepository(BaseRepository):
    def get_edge(self, edge_id: int) -> StackSnapshotEdgeDTO | None:
        """Récupère une arête par son ID."""
        with self._get_session() as session:
            edge = session.query(StackSnapshotEdge).get(edge_id)
            if not edge:
                return None
            return StackSnapshotEdgeDTO(**sqlalchemy_to_dict(edge))

    def list_edges_by_type(self, edge_type: str) -> list[StackSnapshotEdgeDTO]:
        """Liste toutes les arêtes d'un type donné."""
        with self._get_session() as session:
            edges = (
                session.query(StackSnapshotEdge)
                .filter(StackSnapshotEdge.edge_type == edge_type)
                .all()
            )
            return [StackSnapshotEdgeDTO(**sqlalchemy_to_dict(e)) for e in edges]

    def create_edge(self, edge_data: dict[str, Any]) -> StackSnapshotEdgeDTO:
        """Crée une nouvelle arête."""
        with self._get_session() as session:
            edge = StackSnapshotEdge(**edge_data)
            session.add(edge)
            session.commit()
            return StackSnapshotEdgeDTO(**sqlalchemy_to_dict(edge))
