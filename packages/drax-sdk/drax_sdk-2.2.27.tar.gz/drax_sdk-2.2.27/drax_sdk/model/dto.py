from typing import Optional, List, TypeVar, Generic, Dict, Set, Any
from enum import Enum

from pydantic import Field, BaseModel

from drax_sdk.model.dynamic import Value
from drax_sdk.model.node import State
from drax_sdk.model.utils import BytesBase64Model
from drax_sdk.utils.timestamp import unix_timestamp

T = TypeVar("T")


class PagedResult(BaseModel, Generic[T]):
    results: List[T] = []
    total_rows: int = Field(alias="totalRows")

    class Config:
        populate_by_name = True


class HandshakeRequest(BaseModel):
    node_id: int | None = Field(alias="nodeId", default=None)
    name: str | None = None
    association_code: str | None = Field(alias="associationCode", default=None)
    urn: str | None = None
    project_id: str | None = Field(alias="projectId", default=None)
    supported_types: List[str] | None = Field(alias="supportedTypes", default=None)
    configuration_publish_topic: str | None = Field(
        alias="configurationPublishTopic", default=None
    )
    state_publish_topic: str | None = Field(alias="statePublishTopic", default=None)
    initial_state: State | None = Field(alias="initialState", default=None)
    extras: List[Value] | None = None

    class Config:
        populate_by_name = True


class HandshakeResponse(BaseModel):
    node_id: int = Field(alias="nodeId")
    urn: str
    public_key: bytes | None = Field(alias="publicKey")
    private_key: bytes | None = Field(alias="privateKey")

    class Config:
        populate_by_name = True


class AssociationRequest(BaseModel):
    apiKey: str
    apiSecret: str
    associationCode: str
    urn: str


class ConfigurationRequest(BaseModel):
    api_key: str | None = Field(alias="apiKey", default=None)
    api_secret: str | None = Field(alias="apiSecret", default=None)
    node_id: Optional[int] = Field(alias="nodeId", default=None)
    urn: str | None = None
    codec: str | None = None
    cryptography_disabled: bool = Field(alias="cryptographyDisabled", default=False)
    timestamp: int = Field(alias="timestamp", default_factory=unix_timestamp)
    configuration: Dict[str, str]

    @classmethod
    def from_configuration(cls, configuration):
        return cls(
            node_id=configuration.node_id,
            timestamp=configuration.timestamp,
            configuration=configuration.to_map(),
        )

    class Config:
        populate_by_name = True


class ConfigurationResponse(BytesBase64Model):
    node_id: str = Field(alias="nodeId")
    timestamp: int = Field(alias="timestamp")
    urn: str | None = Field(alias="urn", default=None)
    configuration: bytes = Field(alias="configuration")
    cryptography_disabled: bool = Field(alias="cryptographyDisabled", default=False)

    class Config:
        populate_by_name = True


class PrepareRequest(BaseModel):
    association_code: Optional[str] = Field(alias="associationCode", default=None)
    project_id: Optional[str] = Field(None, alias="projectId")
    name: str
    urn: Optional[str] = None
    tag: Optional[str] = None
    supported_types: List[str] = Field(default_factory=set, alias="supportedTypes")
    state_publish_topic: Optional[str] = Field(None, alias="statePublishTopic")
    configuration_publish_topic: Optional[str] = Field(
        None, alias="configurationPublishTopic"
    )
    script: Optional[str] = None
    max_idle_time: int = Field(0, alias="maxIdleTime")
    last_check: int = Field(default=unix_timestamp(), alias="lastCheck")
    state: State = State()

    class Config:
        populate_by_name = True


class InstallRequest(BaseModel):
    association_code: Optional[str] = Field(alias="associationCode", default=None)
    project_id: Optional[str] = Field(None, alias="projectId")
    name: str
    urn: Optional[str] = None
    tag: Optional[str] = None
    supported_types: List[str] = Field(default_factory=set, alias="supportedTypes")
    state_publish_topic: Optional[str] = Field(None, alias="statePublishTopic")
    configuration_publish_topic: Optional[str] = Field(
        None, alias="configurationPublishTopic"
    )
    script: Optional[str] = None
    max_idle_time: int = Field(0, alias="maxIdleTime")
    last_check: int = Field(default=unix_timestamp(), alias="lastCheck")
    state: State = State()

    class Config:
        populate_by_name = True


class FlatConfigurationResponse(BaseModel):
    node_id: Optional[str] = Field(alias="nodeId")
    urn: Optional[str] = None
    timestamp: int
    configuration: Dict[str, str]

    @classmethod
    def from_node_and_entry(cls, node, state):
        return cls(
            nodeId=node.id,
            urn=node.urn,
            timestamp=state.timestamp,
            state=state.to_map(),
        )

    @classmethod
    def from_state(cls, state):
        return cls(nodeId=state.nodeId, timestamp=state.timestamp, state=state.to_map())


class StateRequest(BytesBase64Model):
    api_key: str = Field(alias="apiKey", default=None)
    api_secret: str = Field(alias="apiSecret", default=None)
    node_id: Optional[str] = Field(alias="nodeId", default=None)
    urn: Optional[str] = None
    timestamp: Optional[int] = None
    state: bytes
    codec: Optional[str] = None
    cryptography_disabled: bool = Field(alias="cryptographyDisabled", default=False)

    class Config:
        populate_by_name = True


class StateResponse(BaseModel):
    node_id: Optional[str] = Field(alias="nodeId")
    urn: Optional[str] = None
    timestamp: int
    state: Dict[str, str]

    @classmethod
    def from_node_and_entry(cls, node, state):
        return cls(
            nodeId=node.id,
            urn=node.urn,
            timestamp=state.timestamp,
            state=state.to_map(),
        )

    @classmethod
    def from_state(cls, state):
        return cls(nodeId=state.nodeId, timestamp=state.timestamp, state=state.to_map())


class AuthenticationRequest(BaseModel):
    api_key: str = Field(alias="apiKey")
    api_secret: str = Field(alias="apiSecret")

    class Config:
        populate_by_name = True


class FindNodeByIdsRequest(BaseModel):
    node_ids: List[int] = Field(alias="nodeIds")

    class Config:
        populate_by_name = True


from pydantic import Field
from typing import Optional


class InstalledNode(BytesBase64Model):
    id: str
    urn: str
    public_key: Optional[bytes] = Field(None, alias="publicKey")
    private_key: Optional[bytes] = Field(None, alias="privateKey")

    @property
    def public_key_hex(self) -> str:
        if self.public_key is None:
            return ""
        return self.public_key.hex()

    @property
    def private_key_hex(self) -> str:
        if self.private_key is None:
            return ""
        return self.private_key.hex()

    class Config:
        populate_by_name = True


# =============================================================================
# ALARM MODELS AND REQUESTS
# =============================================================================

class AlarmSeverity(str, Enum):
    """Alarm severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AlarmStatus(str, Enum):
    """Alarm status types."""
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"
    TRIGGERED = "TRIGGERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class AlarmTypeStatus(str, Enum):
    """Alarm type status."""
    ARMED = "ARMED"
    DISARMED = "DISARMED"
    AUTO = "AUTO"


class ScopeType(str, Enum):
    """Scope type for alarms."""
    LOCAL = "LOCAL"
    GLOBAL = "GLOBAL"
    TAGS = "TAGS"
    NODE_LIST = "NODE_LIST"


class Scope(BaseModel):
    """Alarm scope definition."""
    type: ScopeType = Field(default=ScopeType.GLOBAL)
    node_ids: Optional[List[str]] = Field(default=None, alias="nodeIds")
    tags: Optional[List[str]] = None

    class Config:
        populate_by_name = True


class AlarmType(BaseModel):
    """Alarm type definition."""
    id: Optional[str] = None
    name: str
    project_id: str = Field(alias="projectId")
    description: Optional[str] = None
    severity: AlarmSeverity
    scope: Scope
    status: AlarmTypeStatus
    
    class Config:
        populate_by_name = True


class Alarm(BaseModel):
    """Alarm instance."""
    id: Optional[str] = None
    alarm_type_id: str = Field(alias="alarmTypeId")
    project_id: str = Field(alias="projectId")
    status: AlarmStatus
    severity: AlarmSeverity
    triggered_at: Optional[int] = Field(default=None, alias="triggeredAt")
    acknowledged_at: Optional[int] = Field(default=None, alias="acknowledgedAt")
    resolved_at: Optional[int] = Field(default=None, alias="resolvedAt")
    duration: Optional[int] = None
    node_id: Optional[str] = Field(default=None, alias="nodeId")
    message: Optional[str] = None

    class Config:
        populate_by_name = True


class AlarmLogEntry(BaseModel):
    """Alarm log entry."""
    id: Optional[str] = None
    alarm_id: str = Field(alias="alarmId")
    project_id: str = Field(alias="projectId")
    timestamp: int
    message: str
    level: str

    class Config:
        populate_by_name = True


class AcknowledgeAlarmRequest(BaseModel):
    """Request to acknowledge an alarm."""
    alarm_id: str = Field(alias="alarmId")
    project_id: str = Field(alias="projectId")

    class Config:
        populate_by_name = True


class ResolveAlarmRequest(BaseModel):
    """Request to resolve an alarm."""
    alarm_id: str = Field(alias="alarmId")
    project_id: str = Field(alias="projectId")

    class Config:
        populate_by_name = True


class GetAlarmRequest(BaseModel):
    """Request to get an alarm by ID."""
    id: str

    class Config:
        populate_by_name = True


class GetAlarmTypeRequest(BaseModel):
    """Request to get an alarm type by ID."""
    id: str

    class Config:
        populate_by_name = True


class PageableRequest(BaseModel):
    """Base class for pageable requests."""
    page: int = Field(default=1)
    size: int = Field(default=10)

    class Config:
        populate_by_name = True


class FindAlarmLogEntriesRequest(PageableRequest):
    """Request to find alarm log entries."""
    project_id: Optional[str] = Field(default=None, alias="projectId")
    alarm_id: Optional[str] = Field(default=None, alias="alarmId")

    class Config:
        populate_by_name = True


class FindAlarmTypesRequest(PageableRequest):
    """Request to find alarm types."""
    project_id: Optional[str] = Field(default=None, alias="projectId")
    name: Optional[str] = None

    class Config:
        populate_by_name = True


class FindAlarmsRequest(PageableRequest):
    """Request to find alarms."""
    keyword: Optional[str] = None
    project_id: Optional[str] = Field(default=None, alias="projectId")
    statuses: Optional[List[AlarmStatus]] = None
    alarm_type_ids: Optional[List[str]] = Field(default=None, alias="alarmTypeIds")
    start: Optional[int] = None
    end: Optional[int] = None
    min_duration: Optional[int] = Field(default=None, alias="minDuration")
    max_duration: Optional[int] = Field(default=None, alias="maxDuration")

    class Config:
        populate_by_name = True


# =============================================================================
# AUTOMATION MODELS AND REQUESTS
# =============================================================================

class LogLevel(str, Enum):
    """Log level for automation logs."""
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class AutomationPageableRequest(BaseModel):
    """Base class for pageable requests (automation uses page=0 default)."""
    page: int = Field(default=0)
    size: int = Field(default=10)

    class Config:
        populate_by_name = True


class FindAutomationsRequest(AutomationPageableRequest):
    """Request to find automations."""
    project_id: Optional[str] = Field(default=None, alias="projectId")
    keyword: Optional[str] = None
    activator_type: Optional[str] = Field(default=None, alias="activatorType")

    class Config:
        populate_by_name = True


class FindUserActionsRequest(AutomationPageableRequest):
    """Request to find user actions."""
    project_id: Optional[str] = Field(default=None, alias="projectId")
    keyword: Optional[str] = None

    class Config:
        populate_by_name = True


class FindUserConditionsRequest(AutomationPageableRequest):
    """Request to find user conditions."""
    project_id: Optional[str] = Field(default=None, alias="projectId")
    keyword: Optional[str] = None

    class Config:
        populate_by_name = True


class FindLogRequest(BaseModel):
    """Request to find automation logs."""
    project_id: Optional[str] = Field(default=None, alias="projectId")
    automation_id: Optional[str] = Field(default=None, alias="automationId")
    level: Optional[LogLevel] = None
    keyword: Optional[str] = None
    from_time: int = Field(default=0, alias="from")
    to_time: int = Field(default=0, alias="to")
    sorts: Optional[List[Dict[str, Any]]] = None
    paging_state: Optional[Dict[str, Any]] = Field(default=None, alias="pagingState")

    class Config:
        populate_by_name = True


class AutomationRequest(BaseModel):
    """Request to trigger automation."""
    activator_type: str = Field(alias="activatorType")
    selector: str
    initial_variables: Dict[str, Any] = Field(default_factory=dict, alias="initialVariables")
    project_id: Optional[str] = Field(default=None, alias="projectId")

    class Config:
        populate_by_name = True


class ExecuteAutomationRequest(BaseModel):
    """Request to execute an automation."""
    automation_id: str = Field(alias="automationId")

    class Config:
        populate_by_name = True


class UserVariable(BaseModel):
    """User variable definition."""
    name: str
    label: str
    input_type: str = Field(alias="inputType")
    default_value: Optional[str] = Field(default=None, alias="defaultValue")

    class Config:
        populate_by_name = True


class UserAction(BaseModel):
    """User-defined action."""
    id: Optional[str] = None
    project_id: str = Field(alias="projectId")
    type: str
    description: str
    priority: int = 0
    variables: List[UserVariable] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class UserCondition(BaseModel):
    """User-defined condition."""
    id: Optional[str] = None
    project_id: str = Field(alias="projectId")
    type: str
    description: str
    priority: int = 0
    variables: List[UserVariable] = Field(default_factory=list)
    script: Optional[str] = None

    class Config:
        populate_by_name = True


class LogEntry(BaseModel):
    """Automation log entry."""
    id: Optional[str] = None
    project_id: str = Field(alias="projectId")
    automation_id: str = Field(alias="automationId")
    message: str
    level: LogLevel
    timestamp: int

    class Config:
        populate_by_name = True


# =============================================================================
# DATA MINER MODELS AND REQUESTS
# =============================================================================

class AggregationFunction:
    """Supported aggregation functions."""
    NONE = "none"
    SUM = "sum"
    MEAN = "mean"
    MIN = "min"
    MAX = "max"
    STDDEV = "stddev"
    COUNT = "count"
    INTEGRAL = "integral"
    MEDIAN = "median"
    DISTINCT = "distinct"
    MODE = "mode"

    @staticmethod
    def values() -> List[str]:
        return [
            AggregationFunction.NONE,
            AggregationFunction.SUM,
            AggregationFunction.MEAN,
            AggregationFunction.MIN,
            AggregationFunction.MAX,
            AggregationFunction.STDDEV,
            AggregationFunction.COUNT,
            AggregationFunction.INTEGRAL,
            AggregationFunction.MEDIAN,
            AggregationFunction.DISTINCT,
            AggregationFunction.MODE,
        ]


class AggregationPeriod:
    """Supported aggregation periods."""
    LAST_MINUTE = "last-minute"
    LAST_HOUR = "last-hour"
    LAST_DAY = "last-day"
    LAST_WEEK = "last-week"
    LAST_MONTH = "last-month"
    LAST_THREE_MONTHS = "last-three-months"

    @staticmethod
    def values() -> List[str]:
        return [
            AggregationPeriod.LAST_MINUTE,
            AggregationPeriod.LAST_HOUR,
            AggregationPeriod.LAST_DAY,
            AggregationPeriod.LAST_WEEK,
            AggregationPeriod.LAST_MONTH,
            AggregationPeriod.LAST_THREE_MONTHS,
        ]


class TimeWindow:
    """Supported time windows."""
    SECONDS_1 = "1s"
    SECONDS_5 = "5s"
    SECONDS_10 = "10s"
    SECONDS_30 = "30s"
    MINUTES_1 = "1m"
    MINUTES_30 = "30m"
    HOURS_1 = "1h"
    HOURS_8 = "8h"
    DAYS_1 = "1d"

    @staticmethod
    def values() -> List[str]:
        return [
            TimeWindow.SECONDS_1,
            TimeWindow.SECONDS_5,
            TimeWindow.SECONDS_10,
            TimeWindow.SECONDS_30,
            TimeWindow.MINUTES_1,
            TimeWindow.MINUTES_30,
            TimeWindow.HOURS_1,
            TimeWindow.HOURS_8,
            TimeWindow.DAYS_1,
        ]


class DataRequest(BaseModel):
    """Request for data mining."""
    project_id: str = Field(alias="projectId")
    node_ids: Optional[List[str]] = Field(default=None, alias="nodeIds")
    peripherals: Optional[List[str]] = None
    tag: Optional[str] = None
    window: Optional[int] = None
    unit: str = "millisecond"
    from_time: Optional[int] = Field(default=None, alias="from")
    to_time: Optional[int] = Field(default=None, alias="to")
    aggregation_function: Optional[str] = Field(default=None, alias="aggregationFunction")
    group_nodes: bool = Field(default=False, alias="groupNodes")

    class Config:
        populate_by_name = True


class DataResponse(BaseModel):
    """Response from data mining."""
    rows: List[List[Any]]
    response_code: int = Field(alias="responseCode")
    peripherals: List[str]
    nodes: Set[str]

    class Config:
        populate_by_name = True


# =============================================================================
# CORE/HANDSHAKE MODELS AND REQUESTS (Original dto.py models)
# =============================================================================
