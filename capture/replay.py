"""ReplaySource: read a pcap and yield FlowRecords.

Packets are read as a stream. Flows are grouped by 5-tuple (direction normalized) and
closed after `idle_timeout` seconds without traffic. FlowRecords are emitted sorted by
start time once the file is read, so consumers see time order.

http_header_names stays empty for now (see issue "CoverTrace HTTP header anomaly and
protocol validation").
"""

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from scapy.layers.dns import DNS
from scapy.layers.inet import ICMP, IP, TCP, UDP
from scapy.layers.inet6 import IPv6
from scapy.utils import PcapReader

from contracts.models import DnsQuery, FlowRecord

log = logging.getLogger(__name__)

QTYPES = {1: "A", 2: "NS", 5: "CNAME", 10: "NULL", 15: "MX", 16: "TXT", 28: "AAAA"}


@dataclass
class _Flow:
    flow_id: str
    src_ip: str
    dst_ip: str
    src_port: int | None
    dst_port: int | None
    proto: str
    first_ts: float
    last_ts: float
    pkt_sizes: list[int] = field(default_factory=list)
    iat_ms: list[float] = field(default_factory=list)
    dns_queries: list[DnsQuery] = field(default_factory=list)
    icmp_ts: list[datetime] = field(default_factory=list)

    def to_record(self) -> FlowRecord:
        return FlowRecord(
            flow_id=self.flow_id,
            src_ip=self.src_ip,
            dst_ip=self.dst_ip,
            src_port=self.src_port,
            dst_port=self.dst_port,
            proto=self.proto,
            start_ts=_dt(self.first_ts),
            end_ts=_dt(self.last_ts),
            pkt_count=len(self.pkt_sizes),
            byte_count=sum(self.pkt_sizes),
            pkt_sizes=self.pkt_sizes,
            iat_ms=self.iat_ms,
            dns_queries=self.dns_queries,
            icmp_ts=self.icmp_ts,
        )


def _dt(ts: float) -> datetime:
    return datetime.fromtimestamp(ts, tz=UTC)


class ReplaySource:
    def __init__(self, path: str | Path, idle_timeout: float = 60.0):
        self.path = Path(path)
        self.idle_timeout = idle_timeout

    def flows(self) -> Iterator[FlowRecord]:
        done: list[_Flow] = []
        active: dict[tuple, _Flow] = {}
        counter = 0

        for pkt in self._packets():
            try:
                parsed = self._parse(pkt)
                if parsed is None:
                    continue
                key, src, dst, sport, dport, proto = parsed
                ts = float(pkt.time)
                query = self._dns_query(
                    pkt, ts
                )  # parse first: a bad packet must not leave a half-built flow
                flow = active.get(key)
                if flow is not None and ts - flow.last_ts > self.idle_timeout:
                    done.append(active.pop(key))
                    flow = None
                if flow is None:
                    counter += 1
                    flow = _Flow(f"flow-{counter:06d}", src, dst, sport, dport, proto, ts, ts)
                    active[key] = flow
                else:
                    flow.iat_ms.append((ts - flow.last_ts) * 1000.0)
                    flow.last_ts = ts
                flow.pkt_sizes.append(len(pkt))
                if pkt.haslayer(ICMP):
                    flow.icmp_ts.append(_dt(ts))
                if query is not None:
                    flow.dns_queries.append(query)
            except Exception as exc:  # one bad packet must not stop the replay
                log.warning("skipping bad packet: %s", exc)

        done.extend(active.values())
        for flow in sorted(done, key=lambda f: f.first_ts):
            yield flow.to_record()

    def _packets(self) -> Iterator:
        try:
            reader = PcapReader(str(self.path))
        except Exception as exc:
            log.warning("cannot open %s: %s", self.path, exc)
            return
        try:
            yield from reader
        except Exception as exc:  # truncated file: keep what was read
            log.warning("stopped reading %s: %s", self.path, exc)
        finally:
            reader.close()

    @staticmethod
    def _parse(pkt):
        ip = pkt.getlayer(IP) or pkt.getlayer(IPv6)
        if ip is None:
            return None
        if pkt.haslayer(TCP):
            l4, proto = pkt[TCP], "tcp"
        elif pkt.haslayer(UDP):
            l4, proto = pkt[UDP], "udp"
        elif pkt.haslayer(ICMP):
            l4, proto = None, "icmp"
        else:
            return None
        sport = l4.sport if l4 is not None else None
        dport = l4.dport if l4 is not None else None
        a, b = (ip.src, sport), (ip.dst, dport)
        # direction-normalized key: both directions of a conversation share a flow
        key = (proto, *sorted((a, b), key=lambda e: (e[0], e[1] or 0)))
        return key, ip.src, ip.dst, sport, dport, proto

    @staticmethod
    def _dns_query(pkt, ts: float) -> DnsQuery | None:
        if not pkt.haslayer(DNS):
            return None
        dns = pkt[DNS]
        # queries only (qr == 0); responses repeat the question and would double count
        if dns.qr != 0 or not dns.qd:
            return None
        question = dns.qd[0] if isinstance(dns.qd, list) else dns.qd
        qname = question.qname
        qname = qname.decode(errors="replace") if isinstance(qname, bytes) else str(qname)
        return DnsQuery(
            ts=_dt(ts),
            qname=qname.rstrip("."),
            qtype=QTYPES.get(question.qtype, str(question.qtype)),
        )
