"""[stub] Placeholder CoverTrace detector, from before the real one landed.

Designed, not Working. Output carries a `[stub]` tag. The pipeline no longer uses it.
"""

from collections import defaultdict
from collections.abc import Iterable
from datetime import timedelta
from math import log2

from contracts.models import Detection, FlowRecord

STUB = "[stub]"


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
