from scapy.layers.dns import DNS, DNSQR
from scapy.layers.inet import ICMP, IP, UDP
from scapy.layers.l2 import Ether
from scapy.utils import wrpcap

from capture.replay import ReplaySource

T0 = 1_760_000_000.0


def dns_pkt(ts, src, qname, sport=40000, dst="10.0.0.53"):
    pkt = (
        Ether()
        / IP(src=src, dst=dst)
        / UDP(sport=sport, dport=53)
        / DNS(rd=1, qd=DNSQR(qname=qname))
    )
    pkt.time = ts
    return pkt


def icmp_pkt(ts, src="10.0.0.7", dst="10.0.0.1"):
    pkt = Ether() / IP(src=src, dst=dst) / ICMP()
    pkt.time = ts
    return pkt


def write(path, pkts):
    wrpcap(str(path), pkts)
    return path


def test_dns_flow_extracts_queries(tmp_path):
    path = write(
        tmp_path / "dns.pcap",
        [
            dns_pkt(T0, "10.0.0.5", "mfrggzdfmztwq2lknnwg23tpoi.t.example.test.", sport=50001),
            dns_pkt(T0 + 0.1, "10.0.0.5", "nbswy3dpeb3w64tmmq.t.example.test.", sport=50002),
            dns_pkt(T0 + 3, "10.0.0.6", "www.wikipedia.org.", sport=50003),
        ],
    )
    flows = list(ReplaySource(path).flows())
    assert len(flows) == 3
    tunnel = [f for f in flows if f.src_ip == "10.0.0.5"]
    assert {q.qname for f in tunnel for q in f.dns_queries} == {
        "mfrggzdfmztwq2lknnwg23tpoi.t.example.test",
        "nbswy3dpeb3w64tmmq.t.example.test",
    }
    assert all(f.proto == "udp" and f.dst_port == 53 for f in flows)
    assert flows == sorted(flows, key=lambda f: f.start_ts)
    assert all(q.qtype == "A" for f in flows for q in f.dns_queries)


def test_flow_statistics(tmp_path):
    pkts = [dns_pkt(T0 + i * 0.5, "10.0.0.5", "a.example.test.", sport=50001) for i in range(4)]
    flow = next(ReplaySource(write(tmp_path / "s.pcap", pkts)).flows())
    assert flow.pkt_count == 4
    assert flow.byte_count == sum(flow.pkt_sizes)
    assert len(flow.pkt_sizes) == 4
    assert flow.iat_ms == [500.0, 500.0, 500.0]
    assert (flow.end_ts - flow.start_ts).total_seconds() == 1.5


def test_icmp_timestamps(tmp_path):
    path = write(tmp_path / "icmp.pcap", [icmp_pkt(T0 + i) for i in range(3)])
    flow = next(ReplaySource(path).flows())
    assert flow.proto == "icmp"
    assert flow.src_port is None
    assert len(flow.icmp_ts) == 3


def test_idle_timeout_splits_flow(tmp_path):
    pkts = [
        dns_pkt(T0, "10.0.0.5", "a.example.test.", sport=50001),
        dns_pkt(T0 + 120, "10.0.0.5", "b.example.test.", sport=50001),
    ]
    flows = list(ReplaySource(write(tmp_path / "idle.pcap", pkts), idle_timeout=60).flows())
    assert len(flows) == 2


def test_empty_file_yields_nothing(tmp_path):
    path = tmp_path / "empty.pcap"
    path.write_bytes(b"")
    assert list(ReplaySource(path).flows()) == []


def test_missing_file_yields_nothing(tmp_path):
    assert list(ReplaySource(tmp_path / "nope.pcap").flows()) == []


def test_truncated_file_keeps_what_was_read(tmp_path):
    pkts = [dns_pkt(T0 + i, "10.0.0.5", f"q{i}.example.test.", sport=50000 + i) for i in range(5)]
    path = write(tmp_path / "full.pcap", pkts)
    data = path.read_bytes()
    cut = tmp_path / "cut.pcap"
    cut.write_bytes(data[: len(data) - 20])
    flows = list(ReplaySource(cut).flows())
    assert 1 <= len(flows) < 5
