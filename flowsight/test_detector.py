import pytest
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
from scapy.packet import Raw
from scapy.utils import wrpcap

from capture.replay import ReplaySource
from flowsight.detector import FlowSight, FlowSightConfig, load_config

T0 = 1_760_000_000.0
TUNNEL = "10.0.0.5"
BENIGN = "10.0.0.6"


def pkt(ts, src, sport, size=40):
    p = Ether() / IP(src=src, dst="10.0.0.53") / UDP(sport=sport, dport=53) / Raw(b"x" * size)
    p.time = ts
    return p


def flows_of(path, pkts):
    wrpcap(str(path), pkts)
    return list(ReplaySource(path).flows())


def run(detector, flows):
    return [d for f in flows if (d := detector.analyze(f))]


def long_flow(path, n=40, gap=0.5):
    return flows_of(path, [pkt(T0 + i * gap, TUNNEL, 40000) for i in range(n)])


def many_flows(path, n=40, gap=0.5, start=0.0):
    return flows_of(path, [pkt(T0 + start + i * gap, TUNNEL, 40000 + i) for i in range(n)])


def test_long_flow_tunnel_is_detected(tmp_path):
    found = run(FlowSight(FlowSightConfig()), long_flow(tmp_path / "a.pcap"))
    assert len(found) == 1
    det = found[0]
    assert det.source == "flowsight"
    assert det.entity.src_ip == TUNNEL
    assert 0.5 <= det.score <= 1.0
    assert det.threshold_used == 0.5
    assert "[stub]" not in det.label
    assert {
        "flow_avg_pkt_size_log",
        "flow_pkt_size_variance",
        "flow_iat_mean_ms",
        "flow_burst_ratio",
        "packet_count",
    } <= det.features.keys()


def test_clearer_tunnel_pattern_scores_higher(tmp_path):
    partial = run(FlowSight(FlowSightConfig()), long_flow(tmp_path / "a.pcap", gap=0.5))
    clear = run(FlowSight(FlowSightConfig()), long_flow(tmp_path / "b.pcap", gap=0.05))
    assert len(partial) == len(clear) == 1
    assert clear[0].score > partial[0].score


def test_many_one_packet_flows_tunnel_is_detected(tmp_path):
    flows = many_flows(tmp_path / "a.pcap")
    assert len(flows) == 40
    found = run(FlowSight(FlowSightConfig()), flows)
    assert [d.entity.src_ip for d in found] == [TUNNEL]


def test_human_paced_benign_traffic_is_quiet(tmp_path):
    gaps = [0.3, 4.1, 1.2, 7.5, 0.6, 2.2, 9.0, 1.1]
    pkts, t = [], 0.0
    for i in range(40):
        t += gaps[i % len(gaps)]
        pkts.append(pkt(T0 + t, BENIGN, 50000 + i, size=600))
    assert run(FlowSight(FlowSightConfig()), flows_of(tmp_path / "b.pcap", pkts)) == []


def test_below_minimum_packets_never_detects(tmp_path):
    flows = many_flows(tmp_path / "a.pcap", n=19)
    assert run(FlowSight(FlowSightConfig()), flows) == []


def test_one_detection_per_episode_then_again_after_quiet_window(tmp_path):
    first = many_flows(tmp_path / "a.pcap", n=100)
    second = many_flows(tmp_path / "b.pcap", n=40, start=200.0)
    detector = FlowSight(FlowSightConfig())
    assert len(run(detector, first)) == 1
    assert len(run(detector, second)) == 1


def test_long_flow_is_trimmed_by_packet_time(tmp_path):
    found = run(FlowSight(FlowSightConfig()), long_flow(tmp_path / "a.pcap", n=200, gap=1.0))
    assert len(found) == 1
    assert found[0].features["packet_count"] == 61.0


def test_dns_icmp_http_fields_are_ignored(tmp_path):
    flows = many_flows(tmp_path / "a.pcap")
    changed = [
        f.model_copy(update={"dns_queries": [], "icmp_ts": [], "http_header_names": ["Host"]})
        for f in flows
    ]

    def view(found):
        return [(d.score, d.label, d.features, d.threshold_used, d.ts) for d in found]

    baseline = view(run(FlowSight(FlowSightConfig()), flows))
    assert baseline
    assert view(run(FlowSight(FlowSightConfig()), changed)) == baseline


def test_missing_settings_file_gives_working_defaults(tmp_path):
    config = load_config(tmp_path / "none.toml")
    assert config == FlowSightConfig()
    assert len(run(FlowSight(config), long_flow(tmp_path / "a.pcap"))) == 1


@pytest.mark.parametrize(
    "line",
    [
        "min_packets = 50",
        "score_cut = 1.1",
        "max_mean_size = 10",
        "max_size_variance = -1",
        "max_iat_mean_ms = 10",
        "min_burst_ratio = 1.1",
        "burst_limit_ms = 1",
    ],
)
def test_settings_file_changes_behaviour(tmp_path, line):
    settings = tmp_path / "settings.toml"
    settings.write_text(line + "\n", encoding="utf-8")
    flows = long_flow(tmp_path / "a.pcap", gap=0.05)
    baseline = run(FlowSight(FlowSightConfig()), flows)
    assert [d.score for d in baseline] == [1.0]
    changed = run(FlowSight(load_config(settings)), flows)
    assert [d.score for d in changed] != [1.0]
