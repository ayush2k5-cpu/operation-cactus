"""CoverTrace entry point: one flow in, one combined Detection per Entity or nothing out.

Checkers are small detectors with `analyze(flow)`. Today there is one, DNS subdomain
entropy. The combined Detection takes the highest checker score and the label of the
checker that produced it, and merges the features of the checkers that fired.
"""

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

from contracts.models import Detection, FlowRecord
from covertrace.dns import DnsEntropyConfig, DnsEntropyDetector

SETTINGS_PATH = Path(__file__).with_name("settings.toml")


@dataclass
class CoverTraceConfig:
    window_seconds: float = 60.0
    entropy_threshold: float = 3.5
    min_queries: int = 20
    score_span: float = 1.5
    # [stub] read from settings but not applied yet
    skip_suffixes: list[str] = field(default_factory=list)


def load_config(path: str | Path = SETTINGS_PATH) -> CoverTraceConfig:
    """Defaults from code, overridden by any known key in the settings file."""
    path = Path(path)
    if not path.exists():
        return CoverTraceConfig()
    known = {f.name for f in fields(CoverTraceConfig)}
    values = tomllib.loads(path.read_text(encoding="utf-8"))
    return CoverTraceConfig(**{k: v for k, v in values.items() if k in known})


class CoverTrace:
    def __init__(self, config: CoverTraceConfig | None = None):
        self.config = config or load_config()
        c = self.config
        self._checkers = [
            DnsEntropyDetector(
                DnsEntropyConfig(
                    window_seconds=c.window_seconds,
                    entropy_threshold=c.entropy_threshold,
                    min_queries=c.min_queries,
                    score_span=c.score_span,
                )
            )
        ]
        self._flagged: set[tuple[str, str]] = set()
        self._count = 0

    def analyze(self, flow: FlowRecord) -> Detection | None:
        found = [d for checker in self._checkers if (d := checker.analyze(flow)) is not None]
        key = (flow.src_ip, flow.dst_ip)
        if not found or key in self._flagged:
            return None
        self._flagged.add(key)
        self._count += 1
        best = max(found, key=lambda d: d.score)
        features: dict[str, float] = {}
        for d in found:
            features.update(d.features)
        return best.model_copy(
            update={"detection_id": f"covertrace-{self._count:04d}", "features": features}
        )
