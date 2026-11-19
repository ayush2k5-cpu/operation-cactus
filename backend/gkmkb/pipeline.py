"""Wire a capture source, the detectors and the gate. Only the backend does this wiring."""

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field, replace
from pathlib import Path
from uuid import uuid4

from backend.gkmkb.gate import Gate
from backend.gkmkb.settings import load_settings
from capture.replay import ReplaySource
from contracts.models import Alert, Detection, FlowRecord, HoneypotSession, Rule
from covertrace.detector import CoverTrace, load_config
from flowsight.detector import FlowSight, FlowSightConfig


@dataclass
class Result:
    flows: int = 0
    detections: list[Detection] = field(default_factory=list)
    alerts: list[Alert] = field(default_factory=list)
    session: HoneypotSession | None = None
    rules: list[Rule] = field(default_factory=list)


def default_detectors(window_seconds: float, rules: list[Rule] | None = None) -> list:
    """Fresh detectors for one replay."""
    ct = CoverTrace(replace(load_config(), window_seconds=window_seconds))
    if rules:
        ct.load_rules(rules)
    return [
        FlowSight(FlowSightConfig(window_seconds=window_seconds)),
        ct,
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
    rules: list[Rule] | None = None,
    engage_fn: Callable[[Alert], HoneypotSession] | None = None,
) -> Result:
    """Replay a pcap with a fresh Gate and fresh detectors; collect the stream."""
    settings = load_settings()
    window = settings.gate_window_seconds if window_seconds is None else window_seconds
    level = settings.gate_threshold if threshold is None else threshold
    result = Result()

    if engage_fn is None and settings.honeypot_engage:
        from mimicnet.honeypot import engage as default_engage

        engage_fn = default_engage

    def counted() -> Iterator[FlowRecord]:
        for flow in ReplaySource(pcap).flows():
            result.flows += 1
            yield flow

    events = stream(
        counted(),
        default_detectors(window, rules=rules) if detectors is None else detectors,
        Gate(window_seconds=window, threshold=level),
        replay_id or uuid4().hex[:8],
    )
    for event in events:
        if isinstance(event, Alert):
            if engage_fn is not None and result.session is None:
                try:
                    session = engage_fn(event)
                    from eval.mitre import tag_events
                    from mimicnet.rules import rules_from

                    session = session.model_copy(update={"mitre": tag_events(session.events)})
                    proposed_rules = rules_from(session)
                    event = event.model_copy(
                        update={"status": "engaged", "session_id": session.session_id}
                    )
                    result.session = session
                    result.rules.extend(proposed_rules)
                except Exception:
                    pass
            result.alerts.append(event)
        else:
            result.detections.append(event)
    return result
