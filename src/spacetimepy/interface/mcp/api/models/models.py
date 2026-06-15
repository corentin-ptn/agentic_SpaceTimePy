"""Models used by the Service and the Controller"""

from dataclasses import dataclass, field

from .dto import FunctionCallDTO, MonitoringSessionDTO

# --- Session ---


@dataclass
class Relation:
    """Represents the related infomation"""

    parent_session_id: int | None = None
    branch_point_call_id: int | None = None
    branch_point_index: int | None = None
    child_sessions: list[int] = field(default_factory=list)


@dataclass
class SessionDetailsRelations(MonitoringSessionDTO):
    """Session with the details of their relations"""

    relations: Relation = field(default_factory=Relation)


@dataclass
class SessionDetailsCalls(MonitoringSessionDTO):
    """Session with the details of their calls"""

    call_count: int = 0


# --- FunctionCall ---


@dataclass
class FunctionCallTree(FunctionCallDTO):
    children: list["FunctionCallTree"] = field(default_factory=list)
