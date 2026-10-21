import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from capture.replay import ReplaySource
from contracts.models import DnsQuery, FlowRecord
from covertrace.dns import DnsEntropyConfig, DnsEntropyDetector

T0 = datetime(2026, 10, 20, tzinfo=UTC)
ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"
DEMO = Path("data/demo/dns_tunnel_plus_benign.pcap")


def flow(i, src, qname, gap=0.5, dst="10.0.0.53"):
    ts = T0 + timedelta(seconds=i * gap)
    return FlowRecord(
        flow_id=f"{src}-{i}",
        src_ip=src,
        dst_ip=dst,
        proto="udp",
        start_ts=ts,
        end_ts=ts,
        pkt_count=1,
        byte_count=80,
        dns_queries=[DnsQuery(ts=ts, qname=qname, qtype="A")],
    )


def tunnel_qname(rng):
    return "".join(rng.choice(ALPHABET) for _ in range(32)) + ".t.example.test."


def run(detector, flows):
    return [d for f in flows if (d := detector.analyze(f))]


def test_tunnel_queries_trigger():
    rng = random.Random(1)
    found = run(DnsEntropyDetector(), [flow(i, "10.0.0.5", tunnel_qname(rng)) for i in range(30)])
    assert len(found) == 1
    det = found[0]
    assert det.source == "covertrace"
    assert det.entity.src_ip == "10.0.0.5"
    assert 0.5 <= det.score <= 1.0
    assert det.threshold_used == 3.5
    assert det.features["entropy"] > 3.5
    assert det.features["query_count"] == 20.0
    assert det.features["mean_label_len"] == 32.0


def test_benign_domains_stay_below_threshold():
    names = ["www.wikipedia.org.", "mail.google.com.", "api.github.com.", "cdn.example.com."]
    flows = [flow(i, "10.0.0.6", names[i % 4]) for i in range(60)]
    assert run(DnsEntropyDetector(), flows) == []


def test_fewer_than_min_queries_do_not_trigger():
    rng = random.Random(2)
    flows = [flow(i, "10.0.0.5", tunnel_qname(rng)) for i in range(19)]
    assert run(DnsEntropyDetector(), flows) == []


def test_queries_outside_window_are_dropped():
    rng = random.Random(3)
    flows = [flow(i, "10.0.0.5", tunnel_qname(rng), gap=5.0) for i in range(30)]
    assert run(DnsEntropyDetector(), flows) == []


def test_threshold_is_configurable():
    rng = random.Random(4)
    detector = DnsEntropyDetector(DnsEntropyConfig(entropy_threshold=4.9))
    assert run(detector, [flow(i, "10.0.0.5", tunnel_qname(rng)) for i in range(30)]) == []


def test_entities_are_tracked_separately():
    rng = random.Random(5)
    flows = []
    for i in range(30):
        flows.append(flow(i, "10.0.0.5", tunnel_qname(rng)))
        flows.append(flow(i, "10.0.0.6", "www.wikipedia.org."))
    found = run(DnsEntropyDetector(), flows)
    assert [d.entity.src_ip for d in found] == ["10.0.0.5"]


@pytest.mark.skipif(not DEMO.exists(), reason="demo pcap not landed yet")
def test_demo_pcap_flags_one_entity_only():
    found = run(DnsEntropyDetector(), ReplaySource(DEMO).flows())
    assert len({d.entity.src_ip for d in found}) == 1
    assert len(found) == 1
