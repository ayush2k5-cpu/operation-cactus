# GKMKB — Build Spec

Status: **Grilled with Ayush 2026-10-20. Decisions in section 11 are locked unless marked open.** Created 2026-10-18.

## 1. Goal
GKMKB is **detection middleware with a thin web console** (ADR 0008). A headless engine replays network traffic, detects covert exfiltration of secrets or data (DNS tunneling first) with two independent detectors, escalates only when both agree, traps the attacker in a Docker honeypot, turns what the honeypot saw into detection rules, and shows all of it in an analyst dashboard. The engine and its CLI (`gkmkb replay <pcap>`) are the product; the dashboard is a viewer.

Targets:
- **Review 2, 2026-10-24** (progress discussion): engine slice + planned tickets + honest status ledger (section 9).
- **Final**: the headline demo in section 6 runs from one command on a clean machine. Date not fixed; build properly, cut by the order in section 9.
- The report only claims what section 8 marks *Working*.

## 2. Non-goals
- Gamification (removed).
- Live capture on real networks (stated long-term goal only).
- Distributed sensors, multi-host deploy, auth/multi-user, production hardening.
- FlowSight explainability (future work).

## 3. Modules and ownership
Each module is a folder with one public entry point, so four people can work without touching each other's files. Owners (decided 2026-10-20):

| Person | Role | Owns |
|---|---|---|
| Ayush | Lead + M4 | `contracts/`, repo and CI, `ReplaySource`, CLI, gate, backend, later dashboard; reviews every PR |
| Shivansh | M1 CoverTrace | All CoverTrace detectors, adaptive baseline |
| Bhargav | Data + slides | Lab pcaps, fixtures, review slides, later dashboard shell and views |
| Sharukh | Research + eval | Honesty ledger, datasets, evaluation harness, report, ethics, MITRE table |
| M3 MimicNet | After Review 2 | Owner open: Ayush/Shivansh once the gate works, or Bhargav with tight tickets |
| M2 FlowSight | After Review 2 (stub first) | Owner open |

All four use AI coding tools (Claude, Antigravity). AI-written code is allowed. Rules: owner can explain every line, tests ship with the PR, the report discloses AI assistance.

| Module | Folder | Public entry point | Notes |
|---|---|---|---|
| M1 CoverTrace | `covertrace/` | `analyze(flow: FlowRecord) -> Detection \| None` | Flagship. Entropy, chi-square timing, protocol validation, adaptive baseline. Deepest evaluation. |
| M2 Capture + FlowSight | `capture/`, `flowsight/` | `ReplaySource.flows() -> Iterator[FlowRecord]`; `analyze(flow) -> Detection \| None` | pcap to flows, 4 flow features, classifier. |
| M3 MimicNet | `mimicnet/` | `engage(alert) -> HoneypotSession`; `rules_from(session) -> list[Rule]` | Docker honeypot, MITRE map, banner variation, rule generation. |
| M4 Backend + Dashboard + Integration | `backend/`, `dashboard/`, `contracts/`, `eval/` | REST + WebSocket (section 5) | Gate, persistence, UI, demo script, CI. Heaviest; dashboard can split off as M5 if a fifth hand appears or work is shared. |

Cross-cutting, shared by owners of M1 and M2: lab DNS-tunnel pcaps and datasets (tickets T07, T12).

## 4. Contracts (source of truth lives in `contracts/`; shapes here)
All timestamps are UTC ISO-8601. All scores are floats in 0 to 1.

**FlowRecord**: `flow_id`, `src_ip`, `dst_ip`, `src_port`, `dst_port`, `proto` (tcp|udp|icmp), `start_ts`, `end_ts`, `pkt_count`, `byte_count`, `pkt_sizes[]`, `iat_ms[]`, optional `dns_queries[{ts,qname,qtype}]`, `icmp_ts[]`, `http_header_names[]`.

**Detection**: `detection_id`, `source` (flowsight|covertrace), `flow_id`, `entity{src_ip,dst_ip}`, `ts`, `score`, `label`, `features{name:value}`, `threshold_used`.

**Alert**: `alert_id`, `entity`, `detection_ids[]`, `severity`, `ts`, `status` (open|engaged|closed), `session_id?`.

**HoneypotSession**: `session_id`, `alert_id`, `service`, `container_id`, `started`, `ended`, `events[{ts,type,data}]`, `mitre[{technique_id,name,evidence}]`.

**Rule**: `rule_id`, `target` (flowsight|covertrace), `type` (ioc|threshold), `match{}`, `session_id`, `status` (proposed|approved|active|rejected).

Rule `match` examples: `{"qname_suffix": "t.evil.example"}`, `{"src_ip": "10.0.0.5"}`, `{"entropy_threshold": 3.8}`.

## 5. Interfaces
- Detectors are plain Python libraries called in-process by the backend (ADR 0002). No inter-service network between detectors on one host.
- REST (FastAPI): `POST /api/replay {pcap}`, `GET /api/detections`, `GET /api/alerts`, `GET /api/sessions/{id}`, `GET /api/rules`, `POST /api/rules/{id}/approve`, `POST /api/rules/{id}/reject`.
- WebSocket: `/ws/events` pushes `detection`, `alert`, `session_event`, `rule` messages (ADR 0004).
- Storage: MongoDB collections `detections`, `alerts`, `sessions`, `rules`, `baselines`.

## 6. Headline demo (acceptance of the whole system)
0. Headless first: `gkmkb replay data/demo/dns_tunnel_plus_benign.pcap` prints detections, the alert and the rule proposals. The steps below add the dashboard on top.
1. `scripts/demo.ps1` (or `.sh`) starts the stack and replays `data/demo/dns_tunnel_plus_benign.pcap`.
2. Dashboard shows benign flows scoring low.
3. The tunnel flow produces a CoverTrace Detection (entropy over threshold) and a FlowSight Detection for the same entity.
4. Gate raises one Alert. A single-signal control pcap raises zero Alerts.
5. MimicNet starts a honeypot container; a scripted attacker session is recorded; MITRE techniques appear.
6. A proposed Rule appears; analyst approves; replaying the tunnel again is caught earlier or with higher score.
7. Adaptive threshold shown: same traffic, two baselines, two cutoffs.

## 7. Evaluation (what the report may claim)
- CoverTrace: precision, recall, F1, ROC/AUC, false-positive rate on benign DNS, static vs adaptive threshold. Datasets per ADR 0007.
- FlowSight: same metrics on flow data.
- Gate: false positives with gate vs either detector alone.
- Closed loop: detection delta before and after an approved rule.
- Every number reproducible by `eval/` scripts with a fixed seed.

## 8. Honesty ledger (update with every merged PR)
| Capability | State on 2026-10-18 |
|---|---|
| Replay capture | Designed |
| C + libpcap capture | Designed (stretch, ADR 0001) |
| FlowSight features and classifier | Partial: paper has a synthetic benchmark only |
| CoverTrace indicators | Partial: paper has synthetic features only |
| Adaptive thresholds | Designed |
| Correlation gate | Designed |
| MimicNet honeypot, MITRE mapping | Designed |
| Fingerprint evasion | Designed |
| Closed-loop rules | Designed |
| Dashboard | Designed (UI mock prompts exist) |

## 9. Cycles
Final date not fixed; each cycle ends with something demonstrable.

- **Cycle 1 (to 2026-10-24, Review 2)**: repo, CI, contracts, setup script, `AGENTS.md`; `ReplaySource`; CLI replay of a lab DNS-tunnel pcap; real CoverTrace DNS entropy detector; stub FlowSight and stub gate; honesty ledger, slides, planned tickets.
- **Cycle 2: core path**: real FlowSight (features + classifier), real gate with tests, backend + Mongo + WebSocket, dashboard shell, ICMP chi-square and HTTP/protocol checks, evaluation v1.
- **Cycle 3: response layer**: one Docker honeypot with session recording, MITRE mapping, dashboard session view.
- **Cycle 4: novelty**: adaptive thresholds, closed-loop rules, fingerprint variation, rule and baseline views.
- **Cycle 5: harden and prove**: final evaluation (gate vs single detector, adaptive vs static, before/after rule), one-command demo on a clean laptop, report numbers, AI disclosure, viva prep.

**Cut line (if late, drop first to last):** fingerprint evasion, closed-loop rules, adaptive thresholds, FlowSight classifier (keep rule-based stub), MimicNet depth. **Never dropped:** replay, CoverTrace, gate, CLI and dashboard alert.

## 10. Risks
- Four people, nothing built, deadline near: walking skeleton first so everyone integrates continuously.
- Dataset and ethics: lab pcaps from own machines only; cite public datasets with licence.
- Paper/code mismatch (C + libpcap, fused classifier): ADRs 0001 and 0002 handle it.
- Docker Desktop on student laptops (RAM, WSL2): setup script checks; MimicNet runs one container only.

## 11. Decisions
| ID | Question | Status |
|---|---|---|
| D0 | Product form | **Locked**: middleware + thin web console, CLI first (ADR 0008) |
| D1 | Capture language | **Locked**: Python replay now; live agent (Rust or C) is a stretch, not claimed until built (ADR 0001) |
| D2 | Paper 1 fused classifier vs independent detectors | **Locked**: independent detectors + gate; fused model kept in `eval/` as baseline (ADR 0002) |
| D3 | Dashboard charts | Proposed: React + Recharts (ADR 0004) |
| D4 | Dashboard transport | Proposed: WebSocket (ADR 0004) |
| D5 | Database | Proposed: MongoDB (ADR 0005) |
| D6 | Rule generation | Proposed: automated extraction + analyst approval (ADR 0006) |
| D7 | "Key Breach" | **Locked**: exfiltration of secrets or data over a covert channel |
| D8 | Datasets | Proposed: lab pcaps + one public flow dataset; spike ticket decides (ADR 0007) |
| D9 | Owners | **Locked** for Cycle 1 (section 3); M2/M3 owners open |
| D10 | Paper 1 venue and date | **Open**, needed for review packet |
| D11 | Repo | **Locked**: private, `ayush2k5-cpu`; teammates' usernames pending |
| D12 | Cut line | **Locked** (section 9) |
