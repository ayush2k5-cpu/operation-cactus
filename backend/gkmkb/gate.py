"""Correlation gate (ADR 0003).

An Alert is raised when a FlowSight and a CoverTrace Detection, both with score at or
above the threshold, exist for the same entity within the window. A single signal never
raises an Alert. One open Alert per entity.
"""

from collections import defaultdict
from datetime import timedelta

from contracts.models import Alert, Detection


class Gate:
    def __init__(self, window_seconds: float = 60.0, threshold: float = 0.7):
        self.window = timedelta(seconds=window_seconds)
        self.threshold = threshold
        self._seen: dict[tuple[str, str], dict[str, list[Detection]]] = defaultdict(
            lambda: {"flowsight": [], "covertrace": []}
        )
        self._open: set[tuple[str, str]] = set()
        self._alert_count = 0

    def feed(self, detection: Detection) -> Alert | None:
        if detection.score < self.threshold:
            return None
        key = (detection.entity.src_ip, detection.entity.dst_ip)
        bucket = self._seen[key]
        bucket[detection.source].append(detection)
        for source in bucket:
            bucket[source] = [d for d in bucket[source] if detection.ts - d.ts <= self.window]
        if key in self._open or not (bucket["flowsight"] and bucket["covertrace"]):
            return None
        self._open.add(key)
        self._alert_count += 1
        pair = [bucket["flowsight"][-1], bucket["covertrace"][-1]]
        score = max(d.score for d in pair)
        return Alert(
            alert_id=f"alert-{self._alert_count:04d}",
            entity=detection.entity,
            detection_ids=[d.detection_id for d in pair],
            severity="high" if score >= 0.9 else "medium",
            ts=detection.ts,
            status="open",
        )

    def close(self, alert: Alert) -> None:
        self._open.discard((alert.entity.src_ip, alert.entity.dst_ip))
