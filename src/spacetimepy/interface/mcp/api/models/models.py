"""Models used by the Service and the Controller"""

import datetime
from dataclasses import dataclass, field, fields

from .dto import MonitoringSessionDTO

# --- Launch Debug ---


@dataclass
class Position:
    """Represents a position in a file with line and character numbers (0-based)."""

    line: int
    character: int


@dataclass
class Range:
    """Represents a range in a file with start and end positions."""

    start: Position
    end: Position


@dataclass
class Param:
    """Represents a parameter with its name and value. (e.g. with a list, name: 'param1', value: '[1, 2, 3]')"""

    name: str
    value: str | None


@dataclass
class LaunchDebugRequest:
    """Request to start a debug session with spacetimepy's debugger tools."""

    file_path: str = field(
        metadata={
            "description": "The path to the file containing the function to debug."
        }
    )
    function_name: str = field(
        metadata={"description": "The name of the function to debug."}
    )
    range: Range = field(metadata={"description": "The range of lines to debug."})
    paramValues: list[Param] = field(
        metadata={"description": "The values of the parameters for the function call."}
    )
    use_reanimation: bool = field(
        metadata={"description": "Whether to use reanimation."}
    )
    selected_function_call_id: int | None = field(
        metadata={
            "description": "The ID of the selected function call for reanimation (reanimate from this call)."
        }
    )


# --- Summary ---


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
    nb_snapshots: int | None = None


@dataclass
class FunctionCallTree(FunctionCallDTOSummary):
    children: list["FunctionCallTree"] = field(default_factory=list)
