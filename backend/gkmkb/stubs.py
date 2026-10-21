"""[stub] Placeholder detectors so the pipeline runs end to end before the real modules land.

Everything here is Designed, not Working. Output carries a `[stub]` tag. Replace with the
real FlowSight (M2) and CoverTrace (M1) when merged.
"""

from collections import defaultdict
from collections.abc import Iterable
from datetime import timedelta
from math import log2
from statistics import pstdev

from contracts.models import Detection, FlowRecord

STUB = "[stub]"


class FlowSightStub:
    """Flags an entity sending many small packets at an even cadence.

    Works on packet events, not on flows: a tunnel can be one long flow (fixed source port)
    or many one-packet flows (new port per query), and the stub must see both. The real
    FlowSight must handle both too.
    """

    def __init__(
        self,
        window_seconds: float = 60.0,
        min_packets: int = 10,
        max_mean_size: float = 150.0,
        max_cadence_cv: float = 0.5,
    ):
        self.window = timedelta(seconds=window_seconds)
        self.min_packets = min_packets
        self.max_mean_size = max_mean_size
        self.max_cadence_cv = max_cadence_cv
        self._events: dict[tuple[str, str], list[tuple]] = defaultdict(list)
        self._flagged: set[tuple[str, str]] = set()
        self._count = 0

    def analyze(self, flow: FlowRecord) -> Detection | None:
        key = (flow.src_ip, flow.dst_ip)
        events = self._events[key]
        ts = flow.start_ts
        for i, size in enumerate(flow.pkt_sizes):
            if i > 0 and i - 1 < len(flow.iat_ms):
                ts = ts + timedelta(milliseconds=flow.iat_ms[i - 1])
            events.append((ts, size))
        events.sort(key=lambda e: e[0])
        newest = events[-1][0]
        events[:] = [(t, size) for t, size in events if newest - t <= self.window]
        if key in self._flagged or len(events) < self.min_packets:
            return None
        gaps = [(b[0] - a[0]).total_seconds() for a, b in zip(events, events[1:], strict=False)]
        mean_gap = sum(gaps) / len(gaps)
        cadence_cv = pstdev(gaps) / mean_gap if mean_gap > 0 else 0.0
        mean_size = sum(size for _, size in events) / len(events)
        if mean_size > self.max_mean_size or cadence_cv > self.max_cadence_cv:
            return None
        self._flagged.add(key)
        self._count += 1
        return Detection(
            detection_id=f"flowsight-{self._count:04d}",
            source="flowsight",
            flow_id=flow.flow_id,
            entity={"src_ip": flow.src_ip, "dst_ip": flow.dst_ip},
            ts=newest,
            score=0.8,
            label=f"regular-small-packets {STUB}",
            features={
                "mean_pkt_size": mean_size,
                "cadence_cv": cadence_cv,
                "packet_count": float(len(events)),
            },
            threshold_used=self.max_cadence_cv,
        )


class CoverTraceStub:
    """Flags an entity whose DNS subdomain labels look random.

    Keeps a per-entity window of labels, as the real detector must (each tunnel query is
    a separate flow). The real detector is issue "CoverTrace DNS subdomain entropy".
    """

    def __init__(
        self, window_seconds: float = 60.0, min_queries: int = 5, min_entropy: float = 3.5
    ):
        self.window = timedelta(seconds=window_seconds)
        self.min_queries = min_queries
        self.min_entropy = min_entropy
        self._labels: dict[tuple[str, str], list[tuple]] = defaultdict(list)
        self._flagged: set[tuple[str, str]] = set()
        self._count = 0

    def analyze(self, flow: FlowRecord) -> Detection | None:
        if not flow.dns_queries:
            return None
        key = (flow.src_ip, flow.dst_ip)
        window = self._labels[key]
        for query in flow.dns_queries:
            window.append((query.ts, query.qname.split(".")[0]))
        newest = flow.dns_queries[-1].ts
        window[:] = [(ts, label) for ts, label in window if newest - ts <= self.window]
        if key in self._flagged or len(window) < self.min_queries:
            return None
        entropy = _mean_entropy(label for _, label in window)
        if entropy < self.min_entropy:
            return None
        self._flagged.add(key)
        self._count += 1
        return Detection(
            detection_id=f"covertrace-{self._count:04d}",
            source="covertrace",
            flow_id=flow.flow_id,
            entity={"src_ip": flow.src_ip, "dst_ip": flow.dst_ip},
            ts=newest,
            score=min(1.0, 0.7 + (entropy - self.min_entropy) / 5),
            label=f"dns-high-entropy {STUB}",
            features={"entropy": entropy, "query_count": float(len(window))},
            threshold_used=self.min_entropy,
        )


def _mean_entropy(labels: Iterable[str]) -> float:
    values = []
    for label in labels:
        if not label:
            continue
        total = len(label)
        counts = {c: label.count(c) for c in set(label)}
        values.append(-sum(n / total * log2(n / total) for n in counts.values()))
    return sum(values) / len(values) if values else 0.0
