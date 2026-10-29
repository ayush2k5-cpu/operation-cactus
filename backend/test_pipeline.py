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
        tmp_path / "irregular.pcap", [("10.0.0.7", tunnel_labels(40), [0.5, 2.5, 0.2, 3.0])]
    )
    result = run(path)
    assert [d.source for d in result.detections] == ["covertrace"]
    assert result.alerts == []


def test_cadence_without_entropy_is_single_signal(tmp_path):
    path = build(tmp_path / "regular.pcap", [("10.0.0.8", benign_labels(30), [0.1])])
    result = run(path)
    assert [d.source for d in result.detections] == ["flowsight"]
    assert result.alerts == []


def test_cli_prints_alert_and_no_stub_note(tunnel_and_benign, capsys):
    assert main(["replay", str(tunnel_and_benign)]) == 0
    out = capsys.readouterr().out
    assert "alerts: 1" in out
    assert "ALERT" in out
    assert "[stub]" not in out


def test_cli_reports_a_file_that_is_not_a_pcap(tmp_path, capsys):
    junk = tmp_path / "junk.pcap"
    junk.write_bytes(b"not a pcap")
    assert main(["replay", str(junk)]) == 2
    captured = capsys.readouterr()
    assert "junk.pcap" in captured.err
    assert "alerts:" not in captured.out


def test_cli_reports_a_missing_file(tmp_path, capsys):
    assert main(["replay", str(tmp_path / "nope.pcap")]) == 2
    assert "nope.pcap" in capsys.readouterr().err


def test_cli_prints_zero_alerts_for_empty_pcap(tmp_path, capsys):
    empty = tmp_path / "empty.pcap"
    empty.write_bytes(b"")
    assert main(["replay", str(empty)]) == 0
    out = capsys.readouterr().out
    assert "alerts: 0" in out


def test_ids_carry_replay_id_and_alerts_reference_detections(tunnel_and_benign):
    result = run(tunnel_and_benign, replay_id="r1")
    ids = {d.detection_id for d in result.detections}
    assert ids and all(i.startswith("r1-") for i in ids)
    alert = result.alerts[0]
    assert alert.alert_id.startswith("r1-")
    assert set(alert.detection_ids) <= ids


def test_two_replays_share_no_ids(tunnel_and_benign):
    a, b = run(tunnel_and_benign), run(tunnel_and_benign)
    ids_a = {d.detection_id for d in a.detections} | {x.alert_id for x in a.alerts}
    ids_b = {d.detection_id for d in b.detections} | {x.alert_id for x in b.alerts}
    assert ids_a and not ids_a & ids_b
    assert len(a.alerts) == len(b.alerts) == 1


def test_threshold_from_env_and_cli_override(tunnel_and_benign, monkeypatch, capsys):
    monkeypatch.setenv("GATE_THRESHOLD", "0.99")
    assert run(tunnel_and_benign).alerts == []
    assert main(["replay", str(tunnel_and_benign), "--threshold", "0.7"]) == 0
    assert "alerts: 1" in capsys.readouterr().out


def test_missing_settings_give_defaults(tunnel_and_benign, monkeypatch):
    monkeypatch.delenv("GATE_WINDOW_SECONDS", raising=False)
    monkeypatch.delenv("GATE_THRESHOLD", raising=False)
    assert len(run(tunnel_and_benign).alerts) == 1


DEMO = "data/demo/dns_tunnel_plus_benign.pcap"
CONTROL = "data/demo/single_signal_control.pcap"


@pytest.mark.skipif(not __import__("os").path.exists(DEMO), reason="demo pcaps not generated")
def test_demo_pcap_raises_one_alert_on_the_tunnel_entity():
    result = run(DEMO)
    assert [a.entity.src_ip for a in result.alerts] == ["10.0.2.20"]
    assert run(CONTROL).alerts == []
