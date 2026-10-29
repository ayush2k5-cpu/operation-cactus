"""Wire a capture source, the detectors and the gate. Only the backend does this wiring."""

from dataclasses import dataclass, field
from pathlib import Path

from backend.gkmkb.gate import Gate
from capture.replay import ReplaySource
from contracts.models import Alert, Detection
from covertrace.dns import DnsEntropyConfig, DnsEntropyDetector
from flowsight.detector import FlowSight, FlowSightConfig


@dataclass
class Result:
    flows: int = 0
    detections: list[Detection] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)


def run(pcap: str | Path, window_seconds: float = 60.0, threshold: float = 0.7) -> Result:
    flowsight = FlowSight(FlowSightConfig(window_seconds=window_seconds))
    covertrace = DnsEntropyDetector(DnsEntropyConfig(window_seconds=window_seconds))
    gate = Gate(window_seconds=window_seconds, threshold=threshold)
    result = Result()
    for flow in ReplaySource(pcap).flows():
        result.flows += 1
        for detector in (flowsight, covertrace):
            detection = detector.analyze(flow)
            if detection is None:
                continue
            result.detections.append(detection)
            alert = gate.feed(detection)
            if alert is not None:
                result.alerts.append(alert)
    return result
