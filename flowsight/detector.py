"""FlowSight entry point: one flow in, a Detection or nothing out.

Keeps a sliding window of packets per Entity and pools the packets of all its flows, so a
tunnel made of one long flow and a tunnel made of many one-packet flows look the same.
Reads only packet sizes and gaps, never DNS, ICMP or HTTP fields.

[stub] The scorer is a placeholder rule (small packets at an even cadence). The real rules
and the classifier plug in behind `_score`.
"""

import tomllib
from collections import defaultdict
from dataclasses import dataclass, fields
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import mean, pstdev

from contracts.models import Detection, Entity, FlowRecord

SETTINGS_PATH = Path(__file__).with_name("settings.toml")


@dataclass
class FlowSightConfig:
    window_seconds: float = 60.0
    min_packets: int = 20
    score_cut: float = 0.5
    max_mean_size: float = 150.0
    max_cadence_cv: float = 0.5


def load_config(path: str | Path = SETTINGS_PATH) -> FlowSightConfig:
    """Defaults from code, overridden by any known key in the settings file."""
    path = Path(path)
    if not path.exists():
        return FlowSightConfig()
    known = {f.name for f in fields(FlowSightConfig)}
    values = tomllib.loads(path.read_text(encoding="utf-8"))
    return FlowSightConfig(**{k: v for k, v in values.items() if k in known})


class FlowSight:
    def __init__(self, config: FlowSightConfig | None = None):
        self.config = config or load_config()
        self._window = timedelta(seconds=self.config.window_seconds)
        self._events: dict[tuple[str, str], list[tuple[datetime, int]]] = defaultdict(list)
        self._flagged: set[tuple[str, str]] = set()
        self._count = 0

    def analyze(self, flow: FlowRecord) -> Detection | None:
        key = (flow.src_ip, flow.dst_ip)
        new = self._packet_times(flow)
        if not new:
            return None
        events = self._events[key]
        # a full quiet window ends the episode
        if events and new[0][0] - max(t for t, _ in events) >= self._window:
            events.clear()
            self._flagged.discard(key)
        events.extend(new)
        events.sort(key=lambda e: e[0])
        newest = events[-1][0]
        events[:] = [(t, size) for t, size in events if newest - t <= self._window]
        if key in self._flagged or len(events) < max(self.config.min_packets, 2):
            return None
        mean_size, cadence_cv = self._features(events)
        score = self._score(mean_size, cadence_cv)
        if score < self.config.score_cut:
            return None
        self._flagged.add(key)
        self._count += 1
        return Detection(
            detection_id=f"flowsight-{self._count:04d}",
            source="flowsight",
            flow_id=flow.flow_id,
            entity=Entity(src_ip=flow.src_ip, dst_ip=flow.dst_ip),
            ts=newest,
            score=score,
            label="regular-small-packets [stub]",
            features={
                "mean_pkt_size": mean_size,
                "cadence_cv": cadence_cv,
                "packet_count": float(len(events)),
            },
            threshold_used=self.config.score_cut,
        )

    @staticmethod
    def _packet_times(flow: FlowRecord) -> list[tuple[datetime, int]]:
        """Rebuild per-packet times from the flow start and its gaps."""
        ts = flow.start_ts.astimezone(UTC)
        out = []
        for i, size in enumerate(flow.pkt_sizes):
            if i > 0 and i - 1 < len(flow.iat_ms):
                ts = ts + timedelta(milliseconds=flow.iat_ms[i - 1])
            out.append((ts, size))
        return out

    @staticmethod
    def _features(events: list[tuple[datetime, int]]) -> tuple[float, float]:
        gaps = [(b[0] - a[0]).total_seconds() for a, b in zip(events, events[1:], strict=False)]
        mean_gap = mean(gaps)
        cadence_cv = pstdev(gaps) / mean_gap if mean_gap > 0 else 0.0
        return mean(size for _, size in events), cadence_cv

    def _score(self, mean_size: float, cadence_cv: float) -> float:
        """[stub] placeholder rule: 0.8 when small and even, else 0.2."""
        small = mean_size <= self.config.max_mean_size
        even = cadence_cv <= self.config.max_cadence_cv
        return 0.8 if small and even else 0.2
