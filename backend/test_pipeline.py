import random

import pytest
from scapy.layers.dns import DNS, DNSQR
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
from scapy.utils import wrpcap

from backend.gkmkb.cli import main
from backend.gkmkb.pipeline import run

T0 = 1_760_000_000.0
ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"


def query(ts, src, label, sport):
    pkt = (
        Ether()
        / IP(src=src, dst="10.0.0.53")
        / UDP(sport=sport, dport=53)
        / DNS(rd=1, qd=DNSQR(qname=f"{label}.t.example.test."))
    )
    pkt.time = ts
    return pkt


def tunnel_labels(n, seed=42):
    rng = random.Random(seed)
    return ["".join(rng.choice(ALPHABET) for _ in range(32)) for _ in range(n)]


def benign_labels(n):
    return [["www", "mail", "docs", "api"][i % 4] for i in range(n)]


def build(path, specs):
    """specs: list of (src_ip, labels, gaps) -> pcap with one query per label."""
    pkts = []
    for src, labels, gaps in specs:
        t = T0
        for i, label in enumerate(labels):
            pkts.append(query(t, src, label, 40000 + i))
            t += gaps[i % len(gaps)]
    wrpcap(str(path), sorted(pkts, key=lambda p: p.time))
    return path


@pytest.fixture
def tunnel_and_benign(tmp_path):
    return build(
        tmp_path / "mix.pcap",
        [
            ("10.0.0.5", tunnel_labels(30), [0.1]),  # tunnel: random labels, fast regular cadence
            ("10.0.0.6", benign_labels(30), [2.0, 9.0, 4.5, 15.0, 1.0]),  # benign, human pace
        ],
    )


def test_tunnel_raises_one_alert_and_benign_none(tunnel_and_benign):
    result = run(tunnel_and_benign)
    assert len(result.alerts) == 1
    assert result.alerts[0].entity.src_ip == "10.0.0.5"
    assert {d.source for d in result.detections if d.entity.src_ip == "10.0.0.5"} == {
        "flowsight",
        "covertrace",
    }
    assert not [d for d in result.detections if d.entity.src_ip == "10.0.0.6"]


def test_entropy_without_cadence_is_single_signal(tmp_path):
    path = build(
        tmp_path / "irregular.pcap", [("10.0.0.7", tunnel_labels(20), [1.0, 9.0, 3.0, 14.0])]
    )
    result = run(path)
    assert [d.source for d in result.detections] == ["covertrace"]
    assert result.alerts == []


def test_cadence_without_entropy_is_single_signal(tmp_path):
    path = build(tmp_path / "regular.pcap", [("10.0.0.8", benign_labels(30), [0.1])])
    result = run(path)
    assert [d.source for d in result.detections] == ["flowsight"]
    assert result.alerts == []


def test_cli_prints_alert_and_stub_note(tunnel_and_benign, capsys):
    assert main(["replay", str(tunnel_and_benign)]) == 0
    out = capsys.readouterr().out
    assert "alerts: 1" in out
    assert "ALERT" in out
    assert "[stub]" in out


def test_cli_prints_zero_alerts_for_empty_pcap(tmp_path, capsys):
    empty = tmp_path / "empty.pcap"
    empty.write_bytes(b"")
    assert main(["replay", str(empty)]) == 0
    out = capsys.readouterr().out
    assert "alerts: 0" in out
