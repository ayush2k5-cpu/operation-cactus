"""Write crafted DNS pcaps (benign, tunnel-like, merged, single-signal control).

Synthetic lab data made with scapy; not captured, no real users' traffic.
Run from the repo root: python data/tools/MakeDnsPcaps.py
"""

import base64
import random
from pathlib import Path

from scapy.layers.dns import DNS, DNSQR
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
from scapy.utils import wrpcap

SEED = 42
START = 1_760_000_000.0  # fixed epoch so reruns are byte-identical
RESOLVER = "10.0.0.53"
BENIGN_SRC = "10.0.1.10"
TUNNEL_SRC = "10.0.2.20"
CONTROL_SRC = "10.0.3.30"
TUNNEL_DELAY = 60.0

BENIGN_DOMAINS = [
    "www.google.com",
    "en.wikipedia.org",
    "www.wikipedia.org",
    "mail.google.com",
    "www.youtube.com",
    "moodle.campus.example.edu",
    "library.campus.example.edu",
    "www.bbc.co.uk",
    "github.com",
    "stackoverflow.com",
]

ROOT = Path(__file__).resolve().parents[1]


def query(src: str, sport: int, name: str, ts: float, txid: int):
    pkt = (
        Ether(src="02:00:00:00:00:01", dst="02:00:00:00:00:02")
        / IP(src=src, dst=RESOLVER)
        / UDP(sport=sport, dport=53)
        / DNS(id=txid, rd=1, qd=DNSQR(qname=name))
    )
    pkt.time = ts
    return pkt


def base32_chars(rng: random.Random, n: int) -> str:
    raw = bytes(rng.randrange(256) for _ in range(n))
    return base64.b32encode(raw).decode().rstrip("=").lower()[:n]


def tunnel_name(rng: random.Random) -> str:
    return base32_chars(rng, rng.randint(32, 50)) + ".t.example.test"


def benign(rng: random.Random, count: int = 220) -> list:
    pkts, ts = [], START
    for _ in range(count):
        ts += rng.uniform(0.5, 20.0)
        name = rng.choice(BENIGN_DOMAINS)
        pkts.append(query(BENIGN_SRC, 40001, name, ts, rng.randrange(65536)))
    return pkts


def tunnel(rng: random.Random, count: int = 320) -> list:
    pkts, ts = [], START + TUNNEL_DELAY
    for _ in range(count):
        ts += rng.uniform(0.09, 0.11)
        pkts.append(query(TUNNEL_SRC, 40002, tunnel_name(rng), ts, rng.randrange(65536)))
    return pkts


def control(rng: random.Random, count: int = 8) -> list:
    pkts, ts = [], START
    for _ in range(count):
        ts += rng.uniform(5.0, 20.0)
        pkts.append(query(CONTROL_SRC, 40003, tunnel_name(rng), ts, rng.randrange(65536)))
    return pkts


def main() -> None:
    rng = random.Random(SEED)
    b, t, c = benign(rng), tunnel(rng), control(rng)
    demo, ev = ROOT / "demo", ROOT / "eval"
    demo.mkdir(exist_ok=True)
    ev.mkdir(exist_ok=True)
    out = {
        ev / "benign_dns.pcap": b,
        ev / "tunnel_dns.pcap": t,
        demo / "dns_tunnel_plus_benign.pcap": sorted(b + t, key=lambda p: float(p.time)),
        demo / "single_signal_control.pcap": c,
    }
    for path, pkts in out.items():
        wrpcap(str(path), pkts)
        print(f"{path.relative_to(ROOT)}: {len(pkts)} packets")


if __name__ == "__main__":
    main()
