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
HARD_BENIGN_SRC = "10.0.1.11"
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

CDN_DOMAINS = [
    "cloudfront.net",
    "akamaized.net",
    "fastly.net",
    "edgecastcdn.net",
    "azureedge.net",
]

LOCAL_DOMAINS = [
    "printer.office.local",
    "laptop-dev.local",
    "workstation.local",
    "gateway.home.local",
    "nas-storage.local",
]

ARPA_DOMAINS = [
    "11.1.0.10.in-addr.arpa",
    "10.1.0.10.in-addr.arpa",
    "53.0.0.10.in-addr.arpa",
    "1.1.168.192.in-addr.arpa",
    "1.0.0.127.in-addr.arpa",
]

BURSTY_WEB_DOMAINS = [
    "fonts.googleapis.com",
    "cdnjs.cloudflare.com",
    "static.xx.fbcdn.net",
    "assets.github.com",
    "code.jquery.com",
    "cdn.jsdelivr.net",
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


def hex_hash(rng: random.Random, length: int = 16) -> str:
    chars = "0123456789abcdef"
    return "".join(rng.choice(chars) for _ in range(length))


def hard_benign_name(rng: random.Random) -> str:
    choice = rng.random()
    if choice < 0.40:
        cdn = rng.choice(CDN_DOMAINS)
        return f"{hex_hash(rng, rng.choice([12, 16, 20]))}.{cdn}"
    elif choice < 0.65:
        return rng.choice(LOCAL_DOMAINS)
    elif choice < 0.85:
        return rng.choice(ARPA_DOMAINS)
    else:
        return rng.choice(BURSTY_WEB_DOMAINS)


def hard_benign(rng: random.Random, burst_count: int = 25) -> list:
    """Bursty human browsing: clusters of rapid queries with human pauses between."""
    pkts, ts = [], START
    for _ in range(burst_count):
        ts += rng.uniform(5.0, 20.0)
        burst_size = rng.randint(4, 10)
        for _ in range(burst_size):
            ts += rng.uniform(0.02, 0.15)
            name = hard_benign_name(rng)
            pkts.append(query(HARD_BENIGN_SRC, 40004, name, ts, rng.randrange(65536)))
    return pkts


LABELS = {
    "dns_tunnel_plus_benign": [
        f"{BENIGN_SRC},{RESOLVER},benign",
        f"{TUNNEL_SRC},{RESOLVER},tunnel",
    ],
    "single_signal_control": [
        f"{CONTROL_SRC},{RESOLVER},benign",
    ],
    "benign_dns": [
        f"{BENIGN_SRC},{RESOLVER},benign",
    ],
    "tunnel_dns": [
        f"{TUNNEL_SRC},{RESOLVER},tunnel",
    ],
    "hard_benign_dns": [
        f"{HARD_BENIGN_SRC},{RESOLVER},benign",
    ],
}


def write_labels(pcap_path: Path, rows: list[str]) -> None:
    labels_path = pcap_path.with_suffix(".labels")
    content = (
        f"# Labels for {pcap_path.name} (crafted lab data, seed {SEED})\nsrc_ip,dst_ip,label\n"
    )
    content += "\n".join(rows) + "\n"
    labels_path.write_text(content, encoding="utf-8")


def main() -> None:
    rng = random.Random(SEED)
    b, t, c, hb = benign(rng), tunnel(rng), control(rng), hard_benign(rng)
    demo, ev = ROOT / "demo", ROOT / "eval"
    demo.mkdir(exist_ok=True)
    ev.mkdir(exist_ok=True)
    out = {
        ev / "benign_dns.pcap": (b, LABELS["benign_dns"]),
        ev / "tunnel_dns.pcap": (t, LABELS["tunnel_dns"]),
        ev / "hard_benign_dns.pcap": (hb, LABELS["hard_benign_dns"]),
        demo / "dns_tunnel_plus_benign.pcap": (
            sorted(b + t, key=lambda p: float(p.time)),
            LABELS["dns_tunnel_plus_benign"],
        ),
        demo / "single_signal_control.pcap": (c, LABELS["single_signal_control"]),
        demo / "hard_benign_dns.pcap": (hb, LABELS["hard_benign_dns"]),
    }
    for path, (pkts, label_rows) in out.items():
        wrpcap(str(path), pkts)
        write_labels(path, label_rows)
        print(f"{path.relative_to(ROOT)}: {len(pkts)} packets")


if __name__ == "__main__":
    main()
