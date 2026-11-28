"""Unit tests for the feature extractor on controlled DNS, ICMP, and HTTP traffic.

Answers Reviewer Comment 4:
Verifies the extractor on controlled traffic and edge cases (sample size, length bounds,
missing headers, encrypted flows).
"""

from datetime import UTC, datetime

from contracts.models import DnsQuery, FlowRecord
from eval.extractor import (
    dns_subdomain_entropy,
    extract_flow_features,
    flow_avg_pkt_size_log,
    flow_burst_ratio,
    flow_iat_mean_ms,
    flow_pkt_size_variance,
    http_header_anomaly_score,
    icmp_timing_chi2,
    protocol_struct_deviation,
)


def _dt(seconds: float) -> datetime:
    return datetime.fromtimestamp(1_760_000_000.0 + seconds, tz=UTC)


def test_flowsight_features_pure_math():
    sizes = [100, 200, 300]
    # mean is 200, ln(200) ~= 5.2983
    assert round(flow_avg_pkt_size_log(sizes), 4) == 5.2983
    # variance of [100, 200, 300] is 10000.0
    assert flow_pkt_size_variance(sizes) == 10000.0

    gaps = [5.0, 10.0, 50.0, 100.0]  # ms
    assert flow_iat_mean_ms(gaps) == 41.25
    # burst threshold 20ms: 5.0 and 10.0 are bursts (2 / 4 = 0.50)
    assert flow_burst_ratio(gaps, threshold_ms=20.0) == 0.50


def test_flowsight_edge_cases():
    assert flow_avg_pkt_size_log([]) == 0.0
    assert flow_pkt_size_variance([500]) == 0.0
    assert flow_iat_mean_ms([]) == 0.0
    assert flow_burst_ratio([]) == 0.0


def test_dns_subdomain_entropy_controlled():
    # 1. Normal benign short subdomain: should be skipped (< 12 chars)
    benign_queries = ["www.google.com.", "api.github.com.", "mail.example.org."]
    assert dns_subdomain_entropy(benign_queries, min_length=12) == 0.0

    # 2. Benign long subdomain with repeated characters (low entropy)
    repeated_long = ["aaaaaaaaaaaaaaaa.example.com."]
    # only one unique character -> entropy is 0.0
    assert dns_subdomain_entropy(repeated_long, min_length=12) == 0.0

    # 3. High-entropy DNS tunneling subdomain (random base32 payload)
    tunnel_sub = "7f9a2b4c6e8d0f1a3b5c7e9d1f2a4b6c"
    tunnel_query = [f"{tunnel_sub}.t.example.test."]
    h = dns_subdomain_entropy(tunnel_query, min_length=12)
    assert h > 3.5  # High entropy (expected ~3.8-4.5 bits)


def test_icmp_timing_chi2_controlled():
    # 1. Fewer than 20 pings: must return 0.0 (sample size condition)
    few_pings = [float(i) for i in range(15)]
    assert icmp_timing_chi2(few_pings, min_samples=20, is_timestamps=True) == 0.0

    # 2. Regular 1.0s pings (25 pings spaced at 1000ms): should have low chi2
    regular_pings = [float(i) for i in range(25)]
    chi2_reg = icmp_timing_chi2(
        regular_pings, expected_interval_ms=1000.0, min_samples=20, is_timestamps=True
    )
    assert chi2_reg < 5.0

    # 3. Modulated covert timing channel (alternating 100ms and 2500ms gaps)
    modulated_gaps = [100.0 if i % 2 == 0 else 2500.0 for i in range(25)]
    chi2_mod = icmp_timing_chi2(
        modulated_gaps, expected_interval_ms=1000.0, min_samples=20, is_timestamps=False
    )
    assert chi2_mod > 15.0  # Strongly rejects expected 1000ms normal distribution


def test_http_header_anomaly_score_controlled():
    # 1. Standard browser request: Host and User-Agent present
    standard_headers = ["Host", "User-Agent", "Accept", "Accept-Language"]
    assert http_header_anomaly_score(standard_headers) == 0.0

    # 2. Missing Host or User-Agent
    missing_ua = ["Host", "Accept"]
    assert http_header_anomaly_score(missing_ua) == 0.15

    # 3. Missing both Host and User-Agent
    missing_both = ["Accept", "Connection"]
    assert http_header_anomaly_score(missing_both) == 0.30

    # 4. Known covert exfiltration header present
    covert_headers = ["Host", "User-Agent", "X-Exfil-Payload"]
    assert http_header_anomaly_score(covert_headers) == 0.60

    # 5. Non-HTTP traffic
    assert http_header_anomaly_score([], has_http_traffic=False) == 0.0


def test_protocol_struct_deviation_controlled():
    # Normal traffic: 10 packets, 5000 bytes (avg 500 bytes/pkt)
    assert protocol_struct_deviation(byte_count=5000, pkt_count=10) == 0.0

    # Tunnel traffic: 50 packets, 1500 bytes (avg 30 bytes/pkt < 64 bytes)
    assert protocol_struct_deviation(byte_count=1500, pkt_count=50) == 0.40

    # With anomalies
    assert (
        protocol_struct_deviation(byte_count=1500, pkt_count=50, anomalies=["malformed_flags"])
        == 0.60
    )


def test_extract_flow_features_end_to_end():
    flow = FlowRecord(
        flow_id="f-test-01",
        src_ip="10.0.0.5",
        dst_ip="10.0.0.53",
        src_port=45000,
        dst_port=53,
        proto="udp",
        start_ts=_dt(0.0),
        end_ts=_dt(10.0),
        pkt_count=20,
        byte_count=1600,
        pkt_sizes=[80] * 20,
        iat_ms=[10.0] * 19,
        dns_queries=[
            DnsQuery(
                ts=_dt(i * 0.5),
                qname="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.t.example.test.",
                qtype="TXT",
            )
            for i in range(20)
        ],
    )

    vec, obs = extract_flow_features(flow, is_encrypted=False)
    assert len(vec) == 8
    assert all(isinstance(v, float) for v in vec)
    assert obs["dns_subdomain_entropy"] is True
    assert vec[4] > 3.5
    assert vec[3] == 1.0


def test_observability_under_encryption():
    flow = FlowRecord(
        flow_id="f-enc-01",
        src_ip="10.0.0.8",
        dst_ip="10.0.0.1",
        src_port=52000,
        dst_port=443,
        proto="tcp",
        start_ts=_dt(0.0),
        end_ts=_dt(5.0),
        pkt_count=30,
        byte_count=12000,
        pkt_sizes=[400] * 30,
        iat_ms=[15.0] * 29,
    )

    vec, obs = extract_flow_features(flow, is_encrypted=True)
    assert len(vec) == 8
    assert obs["flow_avg_pkt_size_log"] is True
    assert obs["flow_pkt_size_variance"] is True
    assert obs["flow_iat_mean_ms"] is True
    assert obs["flow_burst_ratio"] is True

    assert obs["dns_subdomain_entropy"] is False
    assert vec[4] == 0.0
    assert obs["icmp_timing_chi2"] is False
    assert vec[5] == 0.0
    assert obs["http_header_anomaly_score"] is False
    assert vec[6] == 0.0
