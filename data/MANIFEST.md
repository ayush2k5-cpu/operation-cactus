# Data manifest

All files below are **crafted with scapy** by `data/tools/MakeDnsPcaps.py`. They are not captured traffic and not real malware traffic.

No real users' traffic. Synthetic lab data.

Seed: 42. Date: 2026-10-21. Re-running the script gives byte-identical files. Each file is under 5 MB.

| File | How made | Seed | Date | Packets | Notes |
|---|---|---|---|---|---|
| `demo/dns_tunnel_plus_benign.pcap` | crafted with scapy, benign + tunnel merged and sorted by time | 42 | 2026-10-21 | 540 | Headline demo input |
| `demo/single_signal_control.pcap` | crafted with scapy | 42 | 2026-10-21 | 8 | High-entropy names at a human rate, one signal only |
| `eval/benign_dns.pcap` | crafted with scapy | 42 | 2026-10-21 | 220 | 10.0.1.10, common domains, gaps 0.5 to 20 s. Gitignored, regenerate with the script |
| `eval/tunnel_dns.pcap` | crafted with scapy | 42 | 2026-10-21 | 320 | 10.0.2.20, `<32-50 base32 chars>.t.example.test`, about 100 ms apart. Gitignored, regenerate with the script |

## Checks

- Wireshark: not yet opened by hand. Do this before the demo and note it here.
- `tunnel_dns_tool.pcap` (iodine or dnscat2, "tool-generated"): not made. Stretch goal, needs Ayush's OK.
