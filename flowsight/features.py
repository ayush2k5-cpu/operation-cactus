"""Pure feature functions for FlowSight windows.

Each function takes only packet sizes and/or inter-arrival times — never DNS,
ICMP, HTTP fields or payload — and returns a float.  All four are safe on
empty and single-packet inputs (return a defined value, never raise).

Paper 1 feature names are preserved (FlowSightSpec § Features, US 30).
"""

import math


def flow_avg_pkt_size_log(pkt_sizes: list[int]) -> float:
    """Natural log of the mean packet size in the window.

    Returns 0.0 when *pkt_sizes* is empty or the mean is ≤ 0.
    For a single packet the result is ``math.log(size)``.
    """
    if not pkt_sizes:
        return 0.0
    avg = sum(pkt_sizes) / len(pkt_sizes)
    if avg <= 0:
        return 0.0
    return math.log(avg)


def flow_pkt_size_variance(pkt_sizes: list[int]) -> float:
    """Population variance (divide by *N*, not *N − 1*) of packet sizes.

    Population variance is used because the window is the complete
    observation, not a sample drawn from a larger population.

    Returns 0.0 when fewer than 2 packets are present (variance is
    undefined for 0 items and trivially 0 for 1 item).
    """
    n = len(pkt_sizes)
    if n < 2:
        return 0.0
    avg = sum(pkt_sizes) / n
    return sum((s - avg) ** 2 for s in pkt_sizes) / n


def flow_iat_mean_ms(iat_ms: list[float]) -> float:
    """Mean inter-arrival time in milliseconds.

    Returns 0.0 when *iat_ms* is empty (no gaps to average).
    """
    if not iat_ms:
        return 0.0
    return sum(iat_ms) / len(iat_ms)


def flow_burst_ratio(iat_ms: list[float], burst_limit_ms: float) -> float:
    """Share of inter-arrival gaps strictly below *burst_limit_ms*.

    A higher ratio means more machine-like bursting.  The burst limit
    is a setting (``FLOWSIGHT_BURST_LIMIT_MS``), not a constant, so it
    must be passed in by the caller (FlowSightSpec § Features, US 16).

    Returns 0.0 when *iat_ms* is empty (no gaps to classify).
    """
    if not iat_ms:
        return 0.0
    return sum(1 for g in iat_ms if g < burst_limit_ms) / len(iat_ms)
