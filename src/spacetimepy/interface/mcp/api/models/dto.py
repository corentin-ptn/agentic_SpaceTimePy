"""Models used to replace SQLAlchemy models"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


# --- DTOs for ObjectIdentity et StoredObject ---
@dataclass
class ObjectIdentityDTO:
    id: int
    identity_hash: str
    name: str | None
    creation_time: datetime


@dataclass
class StoredObjectDTO:
    id: str
    identity_id: int
    version_number: int
    type_name: str
    is_primitive: bool
    primitive_value: str | None
    pickle_data: bytes | None


# --- DTOs for StackSnapshot et StackSnapshotEdge ---
@dataclass
class StackSnapshotDTO:
    id: int
    function_call_id: int
    code_definition_id: str | None
    line_number: int
    timestamp: datetime
    locals_refs: dict[str, str]
    globals_refs: dict[str, str]
    order_in_call: int | None
    next_snapshot_id: int | None


@dataclass
class StackSnapshotEdgeDTO:
    id: int
    from_snapshot_id: int
    to_snapshot_id: int
    edge_type: str
    created_at: datetime


# --- DTOs for FunctionCall ---
@dataclass
class FunctionCallDTO:
    id: int
    function: str
    file: str | None
    line: int | None
    start_time: datetime
    end_time: datetime | None
    call_metadata: dict[str, Any] | None
    locals_refs: dict[str, str]
    globals_refs: dict[str, str]
    return_ref: str | None
    code_definition_id: str | None
    session_id: int | None
    parent_call_id: int | None
    order_in_parent: int | None
    order_in_session: int | None
    first_snapshot_id: int | None


# --- DTOs for CodeDefinition et CodeObjectLink ---
@dataclass
class CodeDefinitionDTO:
    id: str
    name: str
    type: str
    module_path: str
    code_content: str
    first_line_no: int | None
    creation_time: datetime


@dataclass
class CodeObjectLinkDTO:
    id: int
    object_id: str
    definition_id: str
    timestamp: datetime


# --- DTOs for MonitoringSession ---
@dataclass
class MonitoringSessionDTO:
    id: int
    name: str | None
    description: str | None
    start_time: datetime
    end_time: datetime | None
    session_metadata: dict[str, Any] | None
