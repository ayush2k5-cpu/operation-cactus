"""CoverTrace DNS subdomain entropy detector.

Each tunnel query is its own flow (new source port), so labels are aggregated per entity
over a sliding window. Static threshold for now; the adaptive Baseline threshold is a
later issue.
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta

from contracts.models import Detection, FlowRecord
from covertrace.entropy import shannon_entropy


@dataclass
class DnsEntropyConfig:
    window_seconds: float = 60.0
    entropy_threshold: float = 3.5
    min_queries: int = 20
    score_span: float = 1.5


class DnsEntropyDetector:
    """Flags an entity whose recent subdomain labels have high mean entropy.

    Emits one Detection per entity, the first time it crosses the threshold.
    """

    def __init__(self, config: DnsEntropyConfig | None = None):
        self.config = config or DnsEntropyConfig()
        self._window = timedelta(seconds=self.config.window_seconds)
        self._labels: dict[tuple[str, str], deque[tuple[datetime, str]]] = defaultdict(deque)
        self._flagged: set[tuple[str, str]] = set()
        self._count = 0

    def analyze(self, flow: FlowRecord) -> Detection | None:
        if not flow.dns_queries:
            return None
        key = (flow.src_ip, flow.dst_ip)
        labels = self._labels[key]
        for query in flow.dns_queries:
            labels.append((query.ts, query.qname.split(".")[0]))
        newest = flow.dns_queries[-1].ts
        while newest - labels[0][0] > self._window:
            labels.popleft()
        if key in self._flagged or len(labels) < self.config.min_queries:
            return None
        texts = [label for _, label in labels if label]
        if not texts:
            return None
        entropy = sum(shannon_entropy(t) for t in texts) / len(texts)
        if entropy <= self.config.entropy_threshold:
            return None
        self._flagged.add(key)
        self._count += 1
        excess = (entropy - self.config.entropy_threshold) / self.config.score_span
        return Detection(
            detection_id=f"covertrace-{self._count:04d}",
            source="covertrace",
            flow_id=flow.flow_id,
            entity={"src_ip": flow.src_ip, "dst_ip": flow.dst_ip},
            ts=newest,
            score=min(1.0, 0.5 + 0.5 * excess),
            label="dns-high-entropy",
            features={
                "entropy": entropy,
                "query_count": float(len(labels)),
                "mean_label_len": sum(len(t) for t in texts) / len(texts),
            },
            threshold_used=self.config.entropy_threshold,
        )
