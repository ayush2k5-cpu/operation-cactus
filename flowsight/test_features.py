"""Tests for the four pure FlowSight feature functions.

Values are hand-computed.  Population variance (÷ N) is used throughout,
matching the implementation choice documented in flow_pkt_size_variance.

Edge cases — empty and single-packet windows — must return defined floats
and never raise (ticket #53 acceptance criterion).
"""

import inspect
import math

import pytest

from flowsight.features import (
    flow_avg_pkt_size_log,
    flow_burst_ratio,
    flow_iat_mean_ms,
    flow_pkt_size_variance,
)

# ── flow_avg_pkt_size_log ────────────────────────────────────────────


class TestFlowAvgPktSizeLog:
    def test_empty(self):
        """Empty window → 0.0, no error."""
        assert flow_avg_pkt_size_log([]) == 0.0

    def test_single_packet(self):
        """Single packet → log of that size."""
        assert flow_avg_pkt_size_log([64]) == pytest.approx(math.log(64))

    def test_multi(self):
        """[100, 200, 300] → mean 200 → log(200) ≈ 5.2983."""
        assert flow_avg_pkt_size_log([100, 200, 300]) == pytest.approx(math.log(200))

    def test_zero_sizes(self):
        """All-zero sizes → mean 0 → returns 0.0 rather than raising."""
        assert flow_avg_pkt_size_log([0, 0, 0]) == 0.0


# ── flow_pkt_size_variance ───────────────────────────────────────────


class TestFlowPktSizeVariance:
    def test_empty(self):
        """Empty window → 0.0, no error."""
        assert flow_pkt_size_variance([]) == 0.0

    def test_single_packet(self):
        """Single packet → 0.0 (variance undefined for N=1, returned as 0)."""
        assert flow_pkt_size_variance([64]) == 0.0

    def test_multi(self):
        """[100, 200, 300] → mean 200.

        Deviations: −100, 0, +100.  Squared: 10 000, 0, 10 000.
        Population variance = 20 000 / 3 ≈ 6666.667.
        """
        expected = 20_000 / 3
        assert flow_pkt_size_variance([100, 200, 300]) == pytest.approx(expected)

    def test_identical_sizes(self):
        """All packets the same size → variance 0."""
        assert flow_pkt_size_variance([128, 128, 128, 128]) == 0.0

    def test_population_not_sample(self):
        """Verify ÷ N (population), not ÷ (N−1) (sample).

        [10, 20]: mean 15, deviations ±5, sum of squares 50.
        Population variance = 50 / 2 = 25.0
        Sample variance     = 50 / 1 = 50.0  ← must NOT match.
        """
        result = flow_pkt_size_variance([10, 20])
        assert result == pytest.approx(25.0)
        assert result != pytest.approx(50.0)


# ── flow_iat_mean_ms ─────────────────────────────────────────────────


class TestFlowIatMeanMs:
    def test_empty(self):
        """No gaps → 0.0, no error."""
        assert flow_iat_mean_ms([]) == 0.0

    def test_multi(self):
        """[10.0, 20.0, 30.0] → mean 20.0 ms."""
        assert flow_iat_mean_ms([10.0, 20.0, 30.0]) == pytest.approx(20.0)

    def test_single_gap(self):
        """One gap → returns that gap."""
        assert flow_iat_mean_ms([42.5]) == pytest.approx(42.5)


# ── flow_burst_ratio ─────────────────────────────────────────────────


class TestFlowBurstRatio:
    def test_empty(self):
        """No gaps → 0.0, no error."""
        assert flow_burst_ratio([], burst_limit_ms=100.0) == 0.0

    def test_all_slow(self):
        """All gaps ≥ limit → ratio 0.0."""
        assert flow_burst_ratio([150.0, 200.0, 300.0], burst_limit_ms=100.0) == 0.0

    def test_all_fast(self):
        """All gaps < limit → ratio 1.0."""
        assert flow_burst_ratio([10.0, 20.0, 30.0], burst_limit_ms=100.0) == 1.0

    def test_mixed(self):
        """[50, 150, 80, 200] with limit 100 → 2 below / 4 = 0.5."""
        result = flow_burst_ratio([50.0, 150.0, 80.0, 200.0], burst_limit_ms=100.0)
        assert result == pytest.approx(0.5)

    def test_gap_equal_to_limit_not_counted(self):
        """Gap exactly at the limit is NOT below it → not a burst."""
        assert flow_burst_ratio([100.0], burst_limit_ms=100.0) == 0.0


# ── independence from DNS / ICMP / HTTP ──────────────────────────────


_FORBIDDEN_PARAMS = {"dns_queries", "icmp_ts", "http_header_names", "payload"}


class TestNoDnsFields:
    """None of the four feature functions accept DNS, ICMP, HTTP, or payload
    parameters — proving FlowSight ignores those fields (US 12, US 28)."""

    @pytest.mark.parametrize(
        "fn",
        [
            flow_avg_pkt_size_log,
            flow_pkt_size_variance,
            flow_iat_mean_ms,
            flow_burst_ratio,
        ],
    )
    def test_no_forbidden_params(self, fn):
        params = set(inspect.signature(fn).parameters)
        overlap = params & _FORBIDDEN_PARAMS
        assert not overlap, f"{fn.__name__} has forbidden params: {overlap}"
