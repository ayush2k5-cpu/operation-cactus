# [GKMKB] Generate crafted DNS-tunnel and benign pcaps

## What
Generate small, reproducible DNS pcaps with a scapy script: benign, tunnel-like, merged demo file and a single-signal control. Label them crafted, not captured.

## Why
Honest evaluation and the demo input without touching real users.

## Acceptance Criteria
- [ ] `data/demo/dns_tunnel_plus_benign.pcap` and `data/demo/single_signal_control.pcap` exist
- [ ] Script `data/tools/MakeDnsPcaps.py` is seeded and reproducible
- [ ] `data/MANIFEST.md` states: crafted with scapy, seed, date, no real users' traffic
- [ ] Each file under 5 MB

## Blockers
None

## Agent
Unassigned

## Owner
Bhargav

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-18 (revised 2026-10-20)

## Steps
1. Read `contracts/` FlowRecord and `docs/specs/GkmkbSpec.md` section 6 so you know what the pcaps must show.
2. Install scapy (`pip install scapy`, already in `requirements.txt`).
3. Write `data/tools/MakeDnsPcaps.py` using scapy. It writes three files into `data/demo/` and `data/eval/`:
   - `benign_dns.pcap`: 200 or more DNS queries from one source IP to a resolver. Use common domains (google.com, wikipedia.org, a campus site). Normal human timing (random gaps 0.5 to 20 s).
   - `tunnel_dns.pcap`: 300 or more queries from a different source IP to the same resolver. Each query is `<32 to 50 random base32 chars>.t.example.test`. Regular timing (about 100 ms).
   - `dns_tunnel_plus_benign.pcap`: both merged and sorted by time.
   - Also write `single_signal_control.pcap`: tunnel-like high-entropy DNS but at a human rate (few queries), used later to prove the gate does not fire on one signal.
4. Use a fixed random seed (42). Re-running must give identical files.
5. Write `data/MANIFEST.md`: one row per file with how it was made (**crafted with scapy**, not captured), seed, date, packet count, and the sentence "No real users' traffic. Synthetic lab data."
6. Open each pcap in Wireshark and confirm queries show. Note in the manifest.
7. Stretch, only with Ayush's OK: record real tunnel traffic between two of your own VMs with iodine or dnscat2 and add it as `tunnel_dns_tool.pcap`. Label it "tool-generated" in the manifest.
8. Open a PR. Do not commit large files; keep each pcap under 5 MB.

Expected output: four small pcaps and a manifest in `data/`. Honest label: crafted, not real malware traffic.
