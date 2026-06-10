import base64
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# --- Modèles pour remplacer ceux de SQLAlchemy (découplage) ---


@dataclass
class ObjectIdentityModel:
    id: int
    identity_hash: str
    creation_time: datetime
    name: str | None = None


@dataclass
class StoredObjectModel:
    id: str
    identity_id: int
    version_number: int
    type_name: str
    is_primitive: bool
    primitive_value: str | None = None
    pickle_data: str | None = None

    def __post_init__(self):
        """Convertit pickle_data (bytes) en base64 pour la sérialisation JSON."""
        if isinstance(self.pickle_data, bytes):
            self.pickle_data = base64.b64encode(self.pickle_data).decode("utf-8")


@dataclass
class StackSnapshotModel:
    id: int
    function_call_id: int
    line_number: int
    timestamp: datetime
    order_in_call: int
    locals_refs: dict[str, str]
    globals_refs: dict[str, str]
    next_snapshot_id: int | None = None
    is_first_in_call: bool = False
    is_last_in_call: bool = False
    code_definition_id: str | None = None


@dataclass
class FunctionCallModel:
    id: int
    function: str
    start_time: datetime | None
    end_time: datetime | None
    call_metadata: dict[str, Any]
    locals_refs: dict[str, str]
    globals_refs: dict[str, str]
    session_id: int
    file: str | None = None
    line: int | None = None
    return_ref: str | None = None
    code_definition_id: str | None = None
    parent_call_id: int | None = None
    order_in_parent: int = 0
    order_in_session: int = 0
    first_snapshot_id: int | None = None


@dataclass
class CodeDefinitionModel:
    id: str
    name: str
    type: str
    module_path: str
    code_content: str
    creation_time: datetime
    first_line_no: int | None = None


@dataclass
class MonitoringSessionModel:
    id: int
    start_time: datetime
    name: str | None = None
    description: str | None = None
    end_time: datetime | None = None
    session_metadata: dict[str, Any] = field(default_factory=dict)
    duration: float | None = None


# --- Modèles pour les retours de GameExplorer ---


@dataclass
class SessionData:
    """Données d'une session et de ses appels suivis."""

    session: MonitoringSessionModel
    calls: list[FunctionCallModel]


@dataclass
class VariablesData:
    """Variables locales et globales d'un appel."""

    locals: dict[str, Any] = field(default_factory=dict)
    globals: dict[str, Any] = field(default_factory=dict)


@dataclass
class CallData:
    """Données d'un appel de fonction."""

    call_id: int
    timestamp: str
    session_id: int
    call_index: int
    file: str
    line: int
    function: str
    code_definition_id: str
    image_data: Any | None = None
    variables: VariablesData = field(default_factory=VariablesData)

@dataclass
class StroboscopicFrame:
    """Cadre pour l'effet stroboscopique."""

    call_index: int
    call_id: int
    image_data: Any


@dataclass
class SessionDetails:
    """Détails complets d'une session."""

    id: int
    name: str
    start_time: str
    call_count: int
    end_time: str | None = None
    calls: list[CallData] = field(default_factory=list)


@dataclass
class SessionRelationship:
    """Relations entre sessions (parent/enfant)."""

    parent_session_id: int | None = None
    branch_point_call_id: int | None = None
    branch_point_index: int | None = None
    child_sessions: list[int] = field(default_factory=list)


@dataclass
class ReplayResult:
    """Résultat d'une opération de replay."""

    new_branch_id: int | None = None
    error: str | None = None


@dataclass
class SessionListItem:
    """Élément de la liste des sessions."""

    session_id: int
    name: str
    start_time: str
    call_count: int
    is_branch: bool
    parent_session_id: int | None = None
    branch_point_index: int | None = None
    child_sessions: list[int] = field(default_factory=list)
