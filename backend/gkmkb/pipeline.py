"""Wire a capture source, the detectors and the gate. Only the backend does this wiring."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from backend.gkmkb.gate import Gate
from backend.gkmkb.settings import load_settings
from backend.gkmkb.stubs import FlowSightStub
from capture.replay import ReplaySource
from contracts.models import Alert, Detection, FlowRecord
from covertrace.dns import DnsEntropyConfig, DnsEntropyDetector


@dataclass
class Result:
    flows: int = 0
    detections: list[Detection] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)


def default_detectors(window_seconds: float) -> list:
    """Fresh detectors for one replay. FlowSight is a [stub] until the real one lands."""
    return [
        FlowSightStub(window_seconds=window_seconds),
        DnsEntropyDetector(DnsEntropyConfig(window_seconds=window_seconds)),
    ]


def stream(
    flows: Iterable[FlowRecord],
    detectors: list,
    gate: Gate,
    replay_id: str,
) -> Iterator[Detection | Alert]:
    """Yield each Detection and Alert as it happens, IDs prefixed with the replay_id."""
    for flow in flows:
        for detector in detectors:
            detection = detector.analyze(flow)
            if detection is None:
                continue
            detection = detection.model_copy(
                update={"detection_id": f"{replay_id}-{detection.detection_id}"}
            )
            yield detection
            alert = gate.feed(detection)
            if alert is not None:
                yield alert.model_copy(update={"alert_id": f"{replay_id}-{alert.alert_id}"})


def run(
    pcap: str | Path,
    window_seconds: float | None = None,
    threshold: float | None = None,
    detectors: list | None = None,
    replay_id: str | None = None,
) -> Result:
    """Replay a pcap with a fresh Gate and fresh detectors; collect the stream."""
    settings = load_settings()
    window = settings.gate_window_seconds if window_seconds is None else window_seconds
    level = settings.gate_threshold if threshold is None else threshold
    result = Result()

    def counted() -> Iterator[FlowRecord]:
        for flow in ReplaySource(pcap).flows():
            result.flows += 1
            yield flow

    events = stream(
        counted(),
        default_detectors(window) if detectors is None else detectors,
        Gate(window_seconds=window, threshold=level),
        replay_id or uuid4().hex[:8],
    )
    for event in events:
        if isinstance(event, Alert):
            result.alerts.append(event)
        else:
            result.detections.append(event)
    return result
