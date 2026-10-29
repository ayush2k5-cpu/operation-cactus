import random

from scapy.layers.dns import DNS, DNSQR
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
from scapy.utils import wrpcap

from capture.replay import ReplaySource
from covertrace.detector import CoverTrace, CoverTraceConfig, load_config

T0 = 1_760_000_000.0
ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"


def make_pcap(path, src, qnames, gap=0.5):
    pkts = []
    for i, qname in enumerate(qnames):
        pkt = (
            Ether()
            / IP(src=src, dst="10.0.0.53")
            / UDP(sport=40000 + i, dport=53)
            / DNS(rd=1, qd=DNSQR(qname=qname))
        )
        pkt.time = T0 + i * gap
        pkts.append(pkt)
    wrpcap(str(path), pkts)
    return path


def tunnel_names(n, seed=1):
    rng = random.Random(seed)
    return ["".join(rng.choice(ALPHABET) for _ in range(32)) + ".t.example.test." for _ in range(n)]


def run(pcap, config=None):
    cover = CoverTrace(config)
    return [d for f in ReplaySource(pcap).flows() if (d := cover.analyze(f))]


def test_tunnel_gives_one_combined_detection(tmp_path):
    pcap = make_pcap(tmp_path / "t.pcap", "10.0.0.5", tunnel_names(30))
    found = run(pcap)
    assert len(found) == 1
    det = found[0]
    assert det.source == "covertrace"
    assert det.entity.src_ip == "10.0.0.5"
    assert det.label == "dns-high-entropy"
    assert 0.5 <= det.score <= 1.0
    assert det.threshold_used == 3.5
    assert det.features["entropy"] > 3.5
    assert all(isinstance(v, float) for v in det.features.values())


def test_benign_names_not_flagged(tmp_path):
    names = ["www.wikipedia.org.", "mail.google.com.", "api.github.com.", "cdn.example.com."]
    pcap = make_pcap(tmp_path / "b.pcap", "10.0.0.6", [names[i % 4] for i in range(60)])
    assert run(pcap) == []


def test_fewer_than_twenty_queries_not_flagged(tmp_path):
    pcap = make_pcap(tmp_path / "s.pcap", "10.0.0.5", tunnel_names(19))
    assert run(pcap) == []


def test_missing_settings_file_gives_defaults(tmp_path):
    assert load_config(tmp_path / "nope.toml") == CoverTraceConfig()
    pcap = make_pcap(tmp_path / "t.pcap", "10.0.0.5", tunnel_names(30))
    assert len(run(pcap, load_config(tmp_path / "nope.toml"))) == 1


def test_settings_file_changes_behaviour(tmp_path):
    settings = tmp_path / "settings.toml"
    settings.write_text("entropy_threshold = 4.9\n", encoding="utf-8")
    pcap = make_pcap(tmp_path / "t.pcap", "10.0.0.5", tunnel_names(30))
    assert run(pcap, load_config(settings)) == []
    settings.write_text("min_queries = 25\n", encoding="utf-8")
    assert run(pcap, load_config(settings))[0].features["query_count"] == 25.0
