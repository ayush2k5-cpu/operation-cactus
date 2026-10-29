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
| FlowSight | Partial | PRs #110, #112, #114; `flowsight/detector.py`, `flowsight/features.py`. Per-Entity window and episodes, four flow features with hand-computed tests, and a rule-based scorer, wired into the pipeline in place of the stub. No classifier, no training data, no result on real traffic (tickets #55, #56) | 2026-10-29 | Bhargav (planned) |
| CoverTrace DNS subdomain entropy detector | Working | PR #41; `covertrace/entropy.py`, `covertrace/dns.py`, `covertrace/test_entropy.py`, `covertrace/test_dns.py` (flags 10.0.2.20 only on the demo pcap) | 2026-10-21 | Ayush (dispatcher) |
| CoverTrace other indicators (ICMP chi-square, HTTP/protocol checks) | Designed | Spec section 9, Cycle 2; no code | 2026-10-18 | Shivansh |
| CoverTrace overall | Partial | PR #126; `covertrace/detector.py`, `covertrace/settings.toml`. A CoverTrace entry point returns one combined Detection per Entity from its checkers, with a settings file. Only one checker exists: DNS subdomain entropy. The skip-list setting is read but not applied. No ICMP, HTTP or ping checks, no learned normal (tickets #47, #48). The paper has synthetic features only | 2026-10-30 | Ayush (di
| Lab DNS-tunnel and benign pcaps | Working | PR #39; `data/demo/*.pcap`, `data/tools/MakeDnsPcaps.py`, `data/MANIFEST.md` (crafted with scapy, seed 42, synthetic, not captured traffic; not yet opened by hand in Wireshark, see the manifest). Test use: `covertrace/test_dns.py` | 2026-10-21 | Ayush (dispatcher) |
| Tool-generated tunnel pcap (iodine or dnscat2) | Designed | `data/MANIFEST.md` lists it as not made | 2026-10-21 | Bhargav |
| Report outline with ethics and dataset sections | Partial | PR #40; `docs/report/ReportOutline.md`. An outline, no results in it | 2026-10-21 | Ayush (dispatcher) |
| Evaluation harness and metrics | Partial | PRs #107, #108, #109; `eval/` holds labels loading, metric functions and a runner on crafted pcaps with a committed results CSV. Synthetic data only. Known gaps from review: an alerting Entity missing from the labels file is dropped, time to first Detection runs from the pcap start, no length check in the metric functions. Comparisons and baseline (tickets #87 to #90) not built | 2026-10-29 | Sharukh |
| Retrained Paper 1 baseline | Designed | EvalSpec; ticket #87 | 2026-10-22 | Sharukh |
| Consent record for captures | Designed | EvalSpec; ticket #83 | 2026-10-22 | Sharukh |
| Adaptive thresholds | Designed | Spec section 9, Cycle 4; no code | 2026-10-18 | Shivansh |
| MimicNet honeypot with session recording | Partial | PR #111; `mimicnet/shell.py`, `mimicnet/honeypot.py`. SSH-like fake shell and `engage` in one locked-down container, container removed after the session; a real-Docker test passes in CI. Scripted attacker and fixed banner only; nothing starts a honeypot from an Alert yet (ticket #60) | 2026-10-29 | Shivansh (planned) |
| MITRE tagging | Designed | MimicNet spec and EvalSpec; tickets #85 and #86 (#21 closed as superseded) | 2026-10-22 | Sharukh (planned) |
| Rule generation from sessions | Designed | MimicNet spec; ticket #58 | 2026-10-22 | Shivansh (planned) |
| Rule loading in CoverTrace | Designed | MimicNet spec; ticket #58 | 2026-10-22 | Shivansh (planned) |
| Fingerprint evasion (banner variation) | Designed | MimicNet spec; ticket #59; first on the cut line | 2026-10-22 | Shivansh (planned) |
| Closed-loop rules | Designed | ADR 0006 addendum; ticket #60; second on the cut line | 2026-10-22 | Ayush (planned) |
| Backend REST, WebSocket, MongoDB, compose stack | Partial | PRs #103 to #106, #115, #127; `backend/gkmkb/api.py`, `storage.py`, `settings.py`, `compose.yaml`, `Dockerfile`. Event stream with replay IDs, replay API with background worker, WebSocket events, REST lists, close Alert, pcap list, session endpoint, in-memory store. The compose stack (Mongo and backend) was run by hand on one Windows laptop: both healthy, a replay stored 2 Detections and 1 Alert in Mongo, data folder read-only, volume kept on teardown. Not run on a clean machine. The Mongo store has no automated test against a real database. No Rules endpoints (ticket #74); the Console is not in the stack | 2026-10-30 | Ayush |
| Dashboard | Partial | PRs #122, #123, #124, #125, #128; `dashboard/` (Vite, React, TypeScript, Vitest, recharts). Replay picker and live feed, Detections with their features, Alerts with close, past Replays list and detail, threshold compare view labelled "from Detections", styled by hand. 25 tests against a fake backend, plus a manual browser check of the live, Replays and Compare views. No Rules view, no honeypot session timeline. Not in the compose stack | 2026-10-30 | Ayush |

## Plain statements

- FlowSight is a rule-based scorer on four window features. It has no trained classifier and no result on real traffic. The demo alert rests on it plus the CoverTrace entropy signal, both on crafted pcaps.
- CoverTrace has one detector today: DNS subdomain entropy.
- Pcaps are crafted lab data. No result here says anything about real traffic.
- The tests in the repo pass on `main`: 165 passed, 24 skipped (`pytest -q`, run 2026-10-29). The skipped ones need MongoDB or are not run locally.
- The only evaluation numbers are on crafted lab pcaps (`eval/results/crafted_results.csv`). They are synthetic. Nothing in the slides or report may quote them as detection rates on real traffic.

## Update rule

Update this file in every PR that changes a capability's state. Keep the spec section 8 table in step with it.
