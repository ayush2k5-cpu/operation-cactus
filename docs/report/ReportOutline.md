# GKMKB Report Outline (draft)

Status: draft, written 2026-10-21 from `main` at `b0bf65f`. Ticket #27. Owner: Sharukh.

Rules for this document:
- The report claims only what the honesty ledger (`docs/specs/GkmkbSpec.md` section 8) marks Working. Terms are exactly Designed, Partial, Working (`GLOSSARY.md`).
- Every claim row carries a Link. Until a PR or eval output exists the Link is `TBD`. A row with `TBD` may be written up only as Designed or future work.
- The ledger in the spec still reads "2026-10-18" and has not been updated for the Cycle 1 merges. The State column below is the proposed new state; the ledger must be updated by the same PRs (CONTRIBUTING step 6). Where the two disagree, the ledger wins until updated.
- `[stub]` code is never reported as a capability.

## 1. Problem

| Claim | Capability needed | State | Link |
|---|---|---|---|
| Covert exfiltration of secrets over DNS (Key Breach) evades signature tools and encrypted-traffic inspection | None (framing, cites Paper 1 and ADR 0008) | n/a | Paper 1 |
| A two-signal gate cuts false positives versus one detector | Real FlowSight, real CoverTrace, gate, eval | Designed | TBD (eval) |

## 2. Related work (from Paper 1)

| Claim | Capability needed | State | Link |
|---|---|---|---|
| Prior work on flow-statistics detection and covert-channel detection, as surveyed in Paper 1 | Citations only | n/a | Paper 1 reference list |
| Paper 1 baseline: 1,000 synthetic records, 8 features, LR 96.0% accuracy / 0.970 AUC, SVM 95.0%, XGBoost 91.5% | Paper 1 synthetic generator | Partial (synthetic only, stated as such in Paper 1) | Paper 1; `research.md` |

Report must say the Paper 1 numbers are synthetic and are not evidence for the engine.

## 3. Architecture

| Claim | Capability needed | State | Link |
|---|---|---|---|
| Middleware form: engine plus CLI is the product, console is a viewer | Engine, CLI | Partial (CLI replay merged; dashboard not built) | ADR 0008; PR #36 |
| Shared contracts (FlowRecord, Detection, Alert, HoneypotSession, Rule) with schemas and fixtures | `contracts/` | Working | PR #34 |
| Modules import only from `contracts/`; backend wires them | Import discipline | Working (by convention, reviewed per PR) | `docs/Architecture.md` |
| Independent detectors in-process, fused classifier kept only as eval baseline | Detector libraries, `eval/` baseline | Designed | ADR 0002; eval TBD |
| Capture is Python replay; C + libpcap live capture is a stretch and not claimed | Live capture agent | Designed (stretch) | ADR 0001 |
| Storage and transport: MongoDB, WebSocket, REST | Backend | Designed | ADR 0004, 0005; TBD |

## 4. Modules

### 4.1 Capture (ReplaySource)
| Claim | Capability needed | State | Link |
|---|---|---|---|
| A pcap is turned into FlowRecords with metadata-only statistics, DNS queries, ICMP timestamps and HTTP header names | `ReplaySource` | Working | PR #37 |
| Lab DNS-tunnel and benign pcaps exist | Lab capture (T07, T12) | Designed | TBD |

### 4.2 CLI and pipeline
| Claim | Capability needed | State | Link |
|---|---|---|---|
| `gkmkb replay <pcap>` runs capture, detectors and gate and prints Detections and Alerts | CLI, pipeline | Working with stub detectors; the output is tagged `[stub]` | PR #36 |

### 4.3 CoverTrace (M1)
| Claim | Capability needed | State | Link |
|---|---|---|---|
| DNS subdomain entropy detector flags tunnel flows | Real entropy detector | Designed (only `[stub]` entropy in `backend/gkmkb/stubs.py`) | TBD (Shivansh PR) |
| Chi-square ICMP timing, HTTP/protocol validation | Detectors | Designed | TBD |
| Adaptive thresholds from a Baseline | Baseline store, threshold logic | Designed | TBD |

### 4.4 FlowSight (M2)
| Claim | Capability needed | State | Link |
|---|---|---|---|
| Per-Entity windows with four metadata-only features, a rule scorer and later a classifier | Real FlowSight (ADR 0009) | Designed (Paper 1 synthetic benchmark only; code is a `[stub]`) | TBD |

### 4.5 Correlation gate
| Claim | Capability needed | State | Link |
|---|---|---|---|
| An Alert is raised only when both sources score at or above threshold for the same Entity inside the window; a single signal never raises one | Gate logic and tests | Partial (logic and tests merged, only exercised with stub detectors) | PR #36; `backend/test_gate.py` |

### 4.6 MimicNet (M3)
| Claim | Capability needed | State | Link |
|---|---|---|---|
| Alert starts one Docker honeypot, session recorded, MITRE techniques mapped | Honeypot, MITRE table | Designed | TBD |
| Banner and fingerprint variation | Fingerprint evasion | Designed (first on the cut line) | TBD |
| Rules generated from a session, analyst-approved, fed back | Rule extraction, approval flow | Designed | ADR 0006; TBD |

### 4.7 Backend and dashboard (M4)
| Claim | Capability needed | State | Link |
|---|---|---|---|
| REST and WebSocket API, persistence | Backend | Designed | TBD |
| Analyst dashboard (alerts, sessions, rules, baselines) | React + Recharts | Designed | TBD |

## 5. Evaluation

Every number must come from an `eval/` script with a fixed seed and be linked here. No number without a link.

| Claim | Capability needed | State | Link |
|---|---|---|---|
| CoverTrace precision, recall, F1, ROC/AUC, FPR on benign DNS; static vs adaptive threshold | Real CoverTrace, datasets, `eval/` | Designed | TBD (eval output) |
| FlowSight same metrics on windows from real tool-generated tunnel captures (not CIC-IDS2017) | Real FlowSight, verified dataset or laptop capture | Designed | TBD |
| Gate false positives against either detector alone | Real detectors, gate, control pcap | Designed | TBD |
| Closed loop: detection delta before and after an approved rule | Rules, replay | Designed | TBD |
| Headline demo (spec section 6) runs from one command on a clean machine | Demo script | Designed | TBD |

Rules for this chapter (`docs/specs/EvalSpec.md`): crafted and real results sit in separate tables; every percent shows its raw count; tune on one set of captures and score on another, split by capture; the gate threshold is chosen on the tuning set; the crafted control favours the gate by design, so only real and hard-benign results count as evidence; Paper 1's own numbers appear in one sentence marked synthetic, and the Paper 1 model is retrained on our data for the table.

Blockers for this chapter: evaluation tickets #81 to #91 and the real-capture ticket #49. Do not fill any row until the matching output file exists.

## 6. Ethics and legal

Draft text, to be refined once datasets are fetched.

**Scope.** All traffic used by GKMKB is lab-generated or from a public dataset. No real users' traffic is captured, replayed or stored. The engine only replays stored pcaps; it does no live capture on any network (spec non-goals, ADR 0001).

**Lab-generated traffic.** DNS tunnel pcaps are produced by the team in an isolated lab on machines the team owns, using tunnelling tools such as iodine or dnscat2 against infrastructure the team controls. Benign DNS is captured from the team's own machines only after each person has given consent. Each capture is logged with who produced it, the date, the tools and the consent. Team members: Ayush Rathod, Sharukh Khan, Shivansh Tripathi, Bhargav Moray. [Consent record per person: TBD, held by Sharukh.]

**Datasets (ADR 0007).**

| Dataset | Use | Licence and citation | Fetched | Status |
|---|---|---|---|---|
| Team lab DNS-tunnel pcaps | CoverTrace evaluation, demo | Team-owned, not redistributed if they contain personal browsing | TBD | Designed |
| Team benign DNS pcaps (consented) | CoverTrace false-positive rate, demo | Team-owned, consented | TBD | Designed |
| CIC-Bell-DNS-EXF-2021 (candidate, page not yet verified by a person) and the team's own laptop capture | FlowSight training and evaluation (CIC-IDS2017 dropped, ADR 0007 addendum) | TBD: licence and citation to be copied from the source into `data/README.md` | TBD | Candidate |
| Paper 1 synthetic generator | Baseline only | Team-owned | n/a | Partial |

Large files are gitignored and fetched by script. One line per dataset (name, licence, citation, URL, date fetched) lives in `data/README.md`; that file must be filled before any evaluation number is reported.

**Honeypot and offensive tooling.** The MimicNet honeypot runs only in the isolated lab. Attacker sessions are scripted by the team. No traffic from real attackers is claimed. Status: Designed.

**Secrets and personal data.** No secrets in git. Captures are checked for personal data (hostnames, queried domains, IPs) before any pcap is committed or put on a slide; anything personal is removed or the pcap stays out of the repo.

**Legal.** Dual-use tunnelling tools are run only on infrastructure the team owns, inside the lab, for defensive evaluation. [Institution ethics clearance, if the university requires it: to be confirmed with the guides, Gerard Deepak and Shalini Ranjan.]

## 7. Limitations

State plainly, each with the matching ledger row:
- Paper 1 numbers are synthetic and do not validate the engine.
- Replay only; no live capture. C + libpcap in Paper 1 is not built (ADR 0001).
- Lab datasets are small; results may not generalise to real networks.
- Detectors and gate verified only against replayed pcaps.
- Anything still Designed or Partial at submission is listed here as future work, in cut-line order (spec section 9): fingerprint evasion, closed-loop rules, adaptive thresholds, FlowSight classifier, MimicNet depth.
- FlowSight explainability is out of scope.

## 8. AI-assistance disclosure

Draft paragraph:

> Team members used AI coding assistants (Claude Code and Antigravity) during development. They were used to draft code, tests, tickets and documentation, including drafts of this report's outline. AI output was not accepted unreviewed: every pull request was reviewed by another teammate, tests ship with the code, and each author was required to be able to explain every line they submitted. AI tools can produce plausible but wrong code and overstated claims, so the report states a capability as Working only when merged, tested and demonstrable, and the honesty ledger tracks each capability's state. The design decisions (product form, independent detectors with a correlation gate, scope cuts) were made by the team and are recorded in the ADRs. AI tools did not generate or alter any evaluation number; those come from the `eval/` scripts. Attribution is disclosed here rather than in commit history, per team policy.

Check before submitting: the last sentence of the paragraph is true only if every number really comes from `eval/`.

## 9. Honesty ledger reference

The final report includes the ledger from `docs/specs/GkmkbSpec.md` section 8 as an appendix, as it stands at submission, and every Working claim above points to a merged PR or an eval output.

## Open items
- Fill every `TBD` link as PRs and eval outputs land.
- Update the spec ledger for the Cycle 1 merges (#34, #36, #37).
- Dataset licences and citations into `data/README.md` (spike T07).
- Consent record for each team member and for each team-captured pcap.
- Confirm whether institutional ethics approval is required.
