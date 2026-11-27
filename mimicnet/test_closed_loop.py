import io
import random
from contextlib import redirect_stdout
from pathlib import Path

import pytest
from scapy.layers.dns import DNS, DNSQR
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
from scapy.utils import wrpcap

from backend.gkmkb.cli import main as cli_main
from backend.gkmkb.pipeline import run as replay_pipeline
from mimicnet.honeypot import engage, play

DEMO_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"
TUNNEL_PCAP = DEMO_DIR / "dns_tunnel_plus_benign.pcap"
CONTROL_PCAP = DEMO_DIR / "single_signal_control.pcap"

T0 = 1_760_000_000.0
ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"


def _fake_engage(alert):
    return play(alert.alert_id)


def _docker_client():
    docker = pytest.importorskip("docker")
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception:
        pytest.skip("Docker is not available")


def _make_pcap(path, src, qnames, gap=0.5):
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


def _tunnel_names(n, seed=1):
    rng = random.Random(seed)
    return ["".join(rng.choice(ALPHABET) for _ in range(32)) + ".t.example.test." for _ in range(n)]


def test_tunnel_demo_pcap_starts_honeypot_session_and_engages_alert():
    result = replay_pipeline(TUNNEL_PCAP, engage_fn=_fake_engage)

    assert len(result.alerts) == 1
    alert = result.alerts[0]
    assert alert.status == "engaged"
    assert alert.session_id is not None
    assert alert.session_id.startswith("session-")

    assert result.session is not None
    assert result.session.session_id == alert.session_id
    assert result.session.service == "ssh-like"
    assert len(result.session.events) > 0

    # MITRE tags attached
    assert len(result.session.mitre) > 0
    technique_ids = [tag.technique_id for tag in result.session.mitre]
    assert "T1071.004" in technique_ids  # DNS tunnel
    assert "T1082" in technique_ids  # uname
    assert "T1083" in technique_ids  # cat /etc/passwd

    # Proposed rules extracted
    assert len(result.rules) == 2
    assert all(r.status == "proposed" for r in result.rules)
    assert all(r.target == "covertrace" for r in result.rules)

    suffix_rule = next((r for r in result.rules if "qname_suffix" in r.match), None)
    addr_rule = next((r for r in result.rules if "src_ip" in r.match), None)

    assert suffix_rule is not None
    assert suffix_rule.match["qname_suffix"] == "t.example.test"

    assert addr_rule is not None
    assert addr_rule.match["src_ip"] == "192.0.2.50"


def test_control_pcap_gives_no_alert_and_no_session():
    result = replay_pipeline(CONTROL_PCAP, engage_fn=_fake_engage)

    assert len(result.alerts) == 0
    assert result.session is None
    assert len(result.rules) == 0


def test_proposed_rules_remain_inactive_until_approved():
    result = replay_pipeline(TUNNEL_PCAP, engage_fn=_fake_engage)
    assert len(result.rules) > 0
    for r in result.rules:
        assert r.status == "proposed"
        assert r.status != "active"


def test_approved_rule_re_replay_catches_earlier_and_higher_score(tmp_path):
    # Initial run on demo pcap without any rules
    baseline_result = replay_pipeline(TUNNEL_PCAP, engage_fn=_fake_engage)
    baseline_ct_dets = [d for d in baseline_result.detections if d.source == "covertrace"]
    assert len(baseline_ct_dets) == 1
    baseline_det = baseline_ct_dets[0]
    assert baseline_det.score < 1.0

    # Extract rule and approve it
    proposed_suffix_rule = next(r for r in baseline_result.rules if "qname_suffix" in r.match)
    approved_rule = proposed_suffix_rule.model_copy(update={"status": "active"})

    # Re-replay with approved active rule
    approved_result = replay_pipeline(TUNNEL_PCAP, rules=[approved_rule], engage_fn=_fake_engage)
    approved_ct_dets = [d for d in approved_result.detections if d.source == "covertrace"]
    assert len(approved_ct_dets) == 1
    approved_det = approved_ct_dets[0]

    # Score is 1.0 and strictly higher than baseline
    assert approved_det.score == 1.0
    assert approved_det.score > baseline_det.score
    assert approved_det.label == f"rule:{approved_rule.rule_id}"

    # Re-replay with rejected rule produces no change from baseline
    rejected_rule = proposed_suffix_rule.model_copy(update={"status": "rejected"})
    rejected_result = replay_pipeline(TUNNEL_PCAP, rules=[rejected_rule], engage_fn=_fake_engage)
    rejected_ct_dets = [d for d in rejected_result.detections if d.source == "covertrace"]
    assert len(rejected_ct_dets) == 1
    rejected_det = rejected_ct_dets[0]
    assert rejected_det.score == baseline_det.score
    assert rejected_det.label == baseline_det.label

    # Demonstration of earlier detection: pcap with only 5 queries
    # Without rule: 0 detections (needs 20)
    few_pcap = _make_pcap(tmp_path / "few.pcap", "10.0.0.5", _tunnel_names(5))
    few_baseline = replay_pipeline(few_pcap, engage_fn=_fake_engage)
    few_base_dets = [d for d in few_baseline.detections if d.source == "covertrace"]
    assert len(few_base_dets) == 0

    # With approved rule: caught immediately on the very first flow!
    few_approved = replay_pipeline(few_pcap, rules=[approved_rule], engage_fn=_fake_engage)
    few_appr_dets = [d for d in few_approved.detections if d.source == "covertrace"]
    assert len(few_appr_dets) == 1
    assert few_appr_dets[0].score == 1.0
    assert few_appr_dets[0].label == f"rule:{approved_rule.rule_id}"


def test_cli_output_shows_session_tags_and_rules(monkeypatch):
    monkeypatch.setattr("mimicnet.honeypot.engage", _fake_engage)
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = cli_main(["replay", str(TUNNEL_PCAP), "--engage"])

    assert exit_code == 0
    output = buf.getvalue()

    assert "alerts: 1" in output
    assert "status=engaged" in output
    assert "session_id=" in output
    assert "session: session-" in output
    assert "mitre tags:" in output
    assert "T1071.004 Application Layer Protocol: DNS" in output
    assert "rules:" in output
    assert "target=covertrace" in output
    assert "status=proposed" in output
    assert "t.example.test" in output


def test_cli_output_control_pcap_shows_no_session_or_rules():
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = cli_main(["replay", str(CONTROL_PCAP), "--engage"])

    assert exit_code == 0
    output = buf.getvalue()

    assert "alerts: 0" in output
    assert "session:" not in output
    assert "mitre tags:" not in output
    assert "rules:" not in output


@pytest.mark.docker
def test_docker_real_container_engage_end_to_end():
    _docker_client()
    result = replay_pipeline(TUNNEL_PCAP, engage_fn=engage)
    assert len(result.alerts) == 1
    assert result.alerts[0].status == "engaged"
    assert result.session is not None
    assert result.session.container_id != "in-process"
    assert len(result.session.mitre) > 0
    assert len(result.rules) == 2
