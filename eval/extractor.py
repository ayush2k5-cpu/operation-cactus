"""Feature extraction specification and implementation for FlowSight and CoverTrace.

Answers Reviewer Comment 4:
- Formally defines the 5-tuple flow key, windowing, burst thresholds, entropy calculation,
  chi-square binning and sample-size criteria, HTTP/protocol anomaly scores,
  and missing/unobservable feature handling under encryption.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from contracts.models import FlowRecord

FEATURE_NAMES = [
    "flow_avg_pkt_size_log",
    "flow_pkt_size_variance",
    "flow_iat_mean_ms",
    "flow_burst_ratio",
    "dns_subdomain_entropy",
    "icmp_timing_chi2",
    "http_header_anomaly_score",
    "protocol_struct_deviation",
]

FLOWSIGHT_FEATURES = FEATURE_NAMES[:4]
COVERTRACE_FEATURES = FEATURE_NAMES[4:]

KNOWN_COVERT_PREFIXES = (
    "x-data",
    "x-tunnel",
    "x-exfil",
    "x-command",
    "x-c2",
    "x-payload",
    "x-covert",
)


@dataclass(frozen=True)
class FlowKey:
    src_ip: str
    dst_ip: str
    src_port: int | None
    dst_port: int | None
    proto: str

    @classmethod
    def from_flow(cls, flow: FlowRecord) -> FlowKey:
        return cls(
            src_ip=flow.src_ip,
            dst_ip=flow.dst_ip,
            src_port=flow.src_port,
            dst_port=flow.dst_port,
            proto=flow.proto,
        )


def flow_avg_pkt_size_log(pkt_sizes: Sequence[int]) -> float:
    """Log of mean packet size: ln(mean(sizes))."""
    if not pkt_sizes:
        return 0.0
    mean_sz = float(np.mean(pkt_sizes))
    return float(math.log(max(mean_sz, 1.0)))


def flow_pkt_size_variance(pkt_sizes: Sequence[int]) -> float:
    """Sample variance of packet sizes in bytes^2."""
    if len(pkt_sizes) <= 1:
        return 0.0
    return float(np.var(pkt_sizes, ddof=1))


def flow_iat_mean_ms(iat_ms: Sequence[float]) -> float:
    """Mean inter-arrival time in milliseconds."""
    if not iat_ms:
        return 0.0
    return float(np.mean(iat_ms))


def flow_burst_ratio(iat_ms: Sequence[float], threshold_ms: float = 20.0) -> float:
    """Proportion of inter-arrival gaps strictly less than threshold_ms."""
    if not iat_ms:
        return 0.0
    count_burst = sum(1 for gap in iat_ms if gap < threshold_ms)
    return float(count_burst / len(iat_ms))


def dns_subdomain_entropy(qnames: Sequence[str], min_length: int = 12) -> float:
    """Shannon entropy of the lowest subdomain label in bits per character.

    H = - sum p_i * log2(p_i)
    Strings shorter than min_length return 0.0 to prevent small-sample noise.
    """
    if not qnames:
        return 0.0

    entropies: list[float] = []
    for q in qnames:
        clean = q.rstrip(".").lower()
        parts = clean.split(".")
        if len(parts) >= 3:
            sub = ".".join(parts[:-2])
        elif len(parts) == 2:
            sub = parts[0]
        else:
            sub = clean

        if len(sub) < min_length:
            continue

        counts = Counter(sub)
        n = len(sub)
        h = -sum((c / n) * math.log2(c / n) for c in counts.values())
        entropies.append(h)

    return float(np.mean(entropies)) if entropies else 0.0


def icmp_timing_chi2(
    timestamps_or_gaps: Sequence[float],
    expected_interval_ms: float = 1000.0,
    min_samples: int = 20,
    is_timestamps: bool = True,
) -> float:
    """Chi-square goodness-of-fit test statistic on ICMP inter-packet timing.

    Compares observed inter-ping delays against the expected normal distribution.
    Sample-size condition: requires at least min_samples (20) observations, else 0.0.
    """
    arr = np.array(timestamps_or_gaps, dtype=float)
    if is_timestamps:
        if len(arr) < min_samples + 1:
            return 0.0
        gaps = np.diff(arr) * 1000.0  # seconds to ms
    else:
        if len(arr) < min_samples:
            return 0.0
        gaps = arr

    e = expected_interval_ms
    # 5 bins: [<0.7e, 0.7-0.95e, 0.95-1.05e, 1.05-1.3e, >1.3e]
    bin_edges = [0.0, 0.70 * e, 0.95 * e, 1.05 * e, 1.30 * e, np.inf]
    observed, _ = np.histogram(gaps, bins=bin_edges)

    total = len(gaps)
    # Expected proportions under benign ping: 90% fall into center bin [0.95e, 1.05e]
    expected_probs = [0.025, 0.025, 0.90, 0.025, 0.025]
    expected = np.array(expected_probs) * total

    chi2 = float(np.sum((observed - expected) ** 2 / np.maximum(expected, 1e-6)))
    return chi2


def http_header_anomaly_score(
    header_names: Sequence[str],
    has_http_traffic: bool = True,
) -> float:
    """Normalized HTTP header anomaly score in [0.0, 1.0]."""
    if not has_http_traffic or not header_names:
        return 0.0

    lowered = [h.strip().lower() for h in header_names]
    score = 0.0

    # Check for covert indicators / prefixes
    if any(any(h.startswith(p) for p in KNOWN_COVERT_PREFIXES) for h in lowered):
        score += 0.60

    # Check for absence of standard HTTP request headers
    has_host = any("host" in h for h in lowered)
    has_ua = any("user-agent" in h for h in lowered)

    if not has_host and not has_ua:
        score += 0.30
    elif not has_host or not has_ua:
        score += 0.15

    # Excessive custom/unusual headers
    custom_headers = [h for h in lowered if h.startswith("x-")]
    if len(custom_headers) > 3:
        score += 0.10

    return min(1.0, round(score, 4))


def protocol_struct_deviation(
    byte_count: int,
    pkt_count: int,
    anomalies: Sequence[str] | None = None,
) -> float:
    """Protocol structural deviation score in [0.0, 1.0]."""
    if pkt_count == 0:
        return 0.0

    score = 0.0
    avg_sz = byte_count / pkt_count

    if avg_sz < 64.0 and pkt_count >= 10:
        score += 0.40

    if anomalies:
        score += min(0.60, len(anomalies) * 0.20)

    return min(1.0, round(score, 4))


def extract_flow_features(
    flow: FlowRecord,
    is_encrypted: bool = False,
) -> tuple[np.ndarray, dict[str, bool]]:
    """Extract 8-dimensional fused feature vector and observability mask."""
    obs = {f: True for f in FEATURE_NAMES}

    f1 = flow_avg_pkt_size_log(flow.pkt_sizes)
    f2 = flow_pkt_size_variance(flow.pkt_sizes)
    f3 = flow_iat_mean_ms(flow.iat_ms)
    f4 = flow_burst_ratio(flow.iat_ms)

    if is_encrypted:
        f5 = 0.0
        obs["dns_subdomain_entropy"] = False
        f6 = 0.0
        obs["icmp_timing_chi2"] = False
        f7 = 0.0
        obs["http_header_anomaly_score"] = False
        f8 = protocol_struct_deviation(flow.byte_count, flow.pkt_count)
    else:
        qnames = [q.qname for q in flow.dns_queries] if flow.dns_queries else []
        f5 = dns_subdomain_entropy(qnames)
        if not qnames:
            obs["dns_subdomain_entropy"] = False

        icmp_floats = [dt.timestamp() for dt in flow.icmp_ts] if flow.icmp_ts else []
        f6 = icmp_timing_chi2(icmp_floats, is_timestamps=True)
        if len(icmp_floats) < 20:
            obs["icmp_timing_chi2"] = False

        has_http = bool(flow.http_header_names or flow.dst_port in (80, 8080))
        f7 = http_header_anomaly_score(flow.http_header_names, has_http_traffic=has_http)
        if not has_http:
            obs["http_header_anomaly_score"] = False

        f8 = protocol_struct_deviation(flow.byte_count, flow.pkt_count)

    vec = np.array([f1, f2, f3, f4, f5, f6, f7, f8], dtype=float)
    return vec, obs
