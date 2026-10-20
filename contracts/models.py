"""Shared data contracts. Source of truth: docs/specs/GkmkbSpec.md section 4.

Every module imports its types from here and from nowhere else. Changing a field
needs a PR approved by every module owner (see contracts/README.md).
"""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

Score = Field(ge=0.0, le=1.0)


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Entity(Contract):
    """The unit the gate correlates on."""

    src_ip: str
    dst_ip: str


class DnsQuery(Contract):
    ts: AwareDatetime
    qname: str
    qtype: str


class FlowRecord(Contract):
    flow_id: str
    src_ip: str
    dst_ip: str
    src_port: int | None = Field(default=None, ge=0, le=65535)
    dst_port: int | None = Field(default=None, ge=0, le=65535)
    proto: Literal["tcp", "udp", "icmp"]
    start_ts: AwareDatetime
    end_ts: AwareDatetime
    pkt_count: int = Field(ge=0)
    byte_count: int = Field(ge=0)
    pkt_sizes: list[int] = []
    iat_ms: list[float] = []
    dns_queries: list[DnsQuery] = []
    icmp_ts: list[AwareDatetime] = []
    http_header_names: list[str] = []


class Detection(Contract):
    detection_id: str
    source: Literal["flowsight", "covertrace"]
    flow_id: str
    entity: Entity
    ts: AwareDatetime
    score: float = Score
    label: str
    features: dict[str, float] = {}
    threshold_used: float


class Alert(Contract):
    alert_id: str
    entity: Entity
    detection_ids: list[str] = Field(min_length=2)
    severity: Literal["low", "medium", "high"]
    ts: AwareDatetime
    status: Literal["open", "engaged", "closed"]
    session_id: str | None = None


class SessionEvent(Contract):
    ts: AwareDatetime
    type: str
    data: dict[str, str] = {}


class MitreTag(Contract):
    technique_id: str
    name: str
    evidence: str


class HoneypotSession(Contract):
    session_id: str
    alert_id: str
    service: str
    container_id: str
    started: AwareDatetime
    ended: AwareDatetime | None = None
    events: list[SessionEvent] = []
    mitre: list[MitreTag] = []


class Rule(Contract):
    rule_id: str
    target: Literal["flowsight", "covertrace"]
    type: Literal["ioc", "threshold"]
    match: dict[str, str | float]
    session_id: str
    status: Literal["proposed", "approved", "active", "rejected"]


ALL_MODELS: dict[str, type[Contract]] = {
    "FlowRecord": FlowRecord,
    "Detection": Detection,
    "Alert": Alert,
    "HoneypotSession": HoneypotSession,
    "Rule": Rule,
}
