"""CoverTrace entry point: one flow in, one combined Detection per Entity or nothing out.

Checkers are small detectors with `analyze(flow)`. Today there is one, DNS subdomain
entropy. The combined Detection takes the highest checker score and the label of the
checker that produced it, and merges the features of the checkers that fired.
"""

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

from contracts.models import Detection, Entity, FlowRecord, Rule
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


def _matches_rule(rule: Rule, flow: FlowRecord) -> bool:
    if not rule.match:
        return False
    if "qname_suffix" in rule.match:
        suffix = str(rule.match["qname_suffix"]).strip(".").lower()
        matched = False
        for q in flow.dns_queries:
            qn = q.qname.strip(".").lower()
            if qn == suffix or qn.endswith("." + suffix):
                matched = True
                break
        if not matched:
            return False

    if "src_ip" in rule.match:
        if flow.src_ip != str(rule.match["src_ip"]):
            return False

    return True


class CoverTrace:
    def __init__(
        self,
        config: CoverTraceConfig | None = None,
        rules: list[Rule] | None = None,
    ):
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
        self._rules: list[Rule] = []
        if rules:
            self.load_rules(rules)

    def load_rules(self, rules: list[Rule]) -> None:
        self._rules = [r for r in rules if r.target == "covertrace" and r.status == "active"]

    def analyze(self, flow: FlowRecord) -> Detection | None:
        key = (flow.src_ip, flow.dst_ip)
        if key in self._flagged:
            return None

        for rule in self._rules:
            if _matches_rule(rule, flow):
                self._flagged.add(key)
                self._count += 1
                return Detection(
                    detection_id=f"covertrace-{self._count:04d}",
                    source="covertrace",
                    flow_id=flow.flow_id,
                    entity=Entity(src_ip=flow.src_ip, dst_ip=flow.dst_ip),
                    ts=flow.end_ts,
                    score=1.0,
                    label=f"rule:{rule.rule_id}",
                    features={"rule_hit": 1.0},
                    threshold_used=self.config.entropy_threshold,
                )

        found = [d for checker in self._checkers if (d := checker.analyze(flow)) is not None]
        if not found:
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
