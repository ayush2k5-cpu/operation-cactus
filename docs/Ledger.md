# Honesty ledger

Status on 2026-10-21, taken from `main` at `ed8f510`. Expands `docs/specs/GkmkbSpec.md` section 8. Everything marked Working or Partial was built in Cycle 1 by the lead (Ayush) with the Ojas dispatcher; teammates join in Cycle 2. The report and the slides claim only what this table marks Working.

## States

- **Working**: a merged PR and a passing test prove it.
- **Partial**: some of it is built and tested, the rest is not.
- **Stub**: placeholder code that lets the pipeline run. Its output carries a visible `[stub]` tag. Not a capability.
- **Designed**: written down in the spec, an ADR or a ticket. No code.

## Capabilities

| Capability | State | Evidence | Date | Owner |
|---|---|---|---|---|
| Shared contracts (FlowRecord, Detection, Alert, HoneypotSession, Rule) | Working | PR #34; `contracts/models.py`, `contracts/test_contracts.py` | 2026-10-20 | Ayush |
| Replay capture (pcap to FlowRecords) | Working | PR #37; `capture/replay.py`, `capture/test_replay.py` | 2026-10-20 | Ayush |
| C + libpcap live capture | Designed (stretch, ADR 0001) | `docs/adr/0001-CaptureReplayFirst.md`; no code | 2026-10-18 | Open |
| `gkmkb replay <pcap>` CLI | Working (FlowSight input is a stub) | PR #36, PR #42; `backend/gkmkb/cli.py`, `backend/test_pipeline.py`. A test asserts 1 alert on `10.0.2.20` for `data/demo/dns_tunnel_plus_benign.pcap` and 0 alerts for `data/demo/single_signal_control.pcap`. Prints no rule proposals yet | 2026-10-21 | Ayush |
| Correlation gate (ADR 0003) | Working | PR #36; `backend/gkmkb/gate.py`, `backend/test_gate.py`, `backend/test_pipeline.py` (one alert for both signals, none for entropy alone or cadence alone). Works on the stub FlowSight input only, so the gate has not been tried against a real FlowSight | 2026-10-20 | Ayush |
| FlowSight | Stub | PR #36; `backend/gkmkb/stubs.py` `FlowSightStub` ([stub], aggregates small even-cadence flows per entity). No flow features, no classifier. The paper has a synthetic benchmark only | 2026-10-20 | Open |
| CoverTrace DNS subdomain entropy detector | Working | PR #41; `covertrace/entropy.py`, `covertrace/dns.py`, `covertrace/test_entropy.py`, `covertrace/test_dns.py` (flags 10.0.2.20 only on the demo pcap) | 2026-10-21 | Ayush (dispatcher) |
| CoverTrace other indicators (ICMP chi-square, HTTP/protocol checks) | Designed | Spec section 9, Cycle 2; no code | 2026-10-18 | Shivansh |
| CoverTrace overall | Partial | Only the DNS entropy detector exists. Nothing else in CoverTrace is built. The paper has synthetic features only | 2026-10-21 | Ayush (dispatcher) |
| Lab DNS-tunnel and benign pcaps | Working | PR #39; `data/demo/*.pcap`, `data/tools/MakeDnsPcaps.py`, `data/MANIFEST.md` (crafted with scapy, seed 42, synthetic, not captured traffic; not yet opened by hand in Wireshark, see the manifest). Test use: `covertrace/test_dns.py` | 2026-10-21 | Ayush (dispatcher) |
| Tool-generated tunnel pcap (iodine or dnscat2) | Designed | `data/MANIFEST.md` lists it as not made | 2026-10-21 | Bhargav |
| Report outline with ethics and dataset sections | Partial | PR #40; `docs/report/ReportOutline.md`. An outline, no results in it | 2026-10-21 | Ayush (dispatcher) |
| Evaluation harness and metrics | Designed | Spec section 7; `eval/` is empty | 2026-10-18 | Sharukh |
| Adaptive thresholds | Designed | Spec section 9, Cycle 4; no code | 2026-10-18 | Shivansh |
| MimicNet honeypot, MITRE mapping | Designed | Spec sections 3 and 9, Cycle 3; `mimicnet/` is empty | 2026-10-18 | Open |
| Fingerprint evasion | Designed | Spec section 9, Cycle 4; first on the cut line | 2026-10-18 | Open |
| Closed-loop rules | Designed | ADR 0006; second on the cut line | 2026-10-18 | Open |
| Backend REST, WebSocket, MongoDB | Designed | Spec section 5; `backend/` holds the CLI pipeline and gate only | 2026-10-18 | Ayush |
| Dashboard | Designed | UI mock prompts exist; `dashboard/` is empty | 2026-10-18 | Bhargav |

## Plain statements

- FlowSight is a `[stub]`. Any alert in the current demo rests on a stub signal plus the real CoverTrace entropy signal. It is not two independent real detectors yet.
- CoverTrace has one detector today: DNS subdomain entropy.
- Pcaps are crafted lab data. No result here says anything about real traffic.
- The 41 tests in the repo pass on `main` (`pytest -q`, run 2026-10-21).
- No evaluation numbers exist yet. Nothing in the slides or report may quote precision, recall or detection rates.

## Update rule

Update this file in every PR that changes a capability's state. Keep the spec section 8 table in step with it.
