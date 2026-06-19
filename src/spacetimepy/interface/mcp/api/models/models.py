"""Models used by the Service and the Controller"""

import datetime
from dataclasses import dataclass, field, fields

from .dto import MonitoringSessionDTO


@dataclass
class BaseSummary:
    @classmethod
    def from_dict(cls, data: dict):
        """Create an instance of SessionSummaryRelations from a dictionary, ignoring extra fields."""
        valid_keys = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)


# --- Session ---


@dataclass
class Relation:
    """Represents the related infomation"""

    parent_session_id: int | None = None
    branch_point_call_id: int | None = None
    branch_point_index: int | None = None
    child_sessions: list[int] = field(default_factory=list)


@dataclass
class SessionSummaryRelations(BaseSummary):
    """Session with the details of their relations"""

    id: int
    name: str | None
    start_time: datetime
    relations: Relation = field(default_factory=Relation)


@dataclass
class SessionDetailsCalls(MonitoringSessionDTO):
    """Session with the details of their calls"""

    call_count: dict[str, int]


# --- FunctionCall ---


@dataclass
class FunctionCallDTOSummary(BaseSummary):
    id: int
    function: str
    start_time: datetime
    return_ref: str | None
    session_id: int | None
    order_in_session: int | None


@dataclass
class FunctionCallTree(FunctionCallDTOSummary):
    children: list["FunctionCallTree"] = field(default_factory=list)
