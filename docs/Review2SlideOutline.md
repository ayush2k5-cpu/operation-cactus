# Review 2 slide outline

Review 2 is 2026-10-24, a progress discussion. Ayush builds the deck from this outline. Every claim below matches a row in `docs/Ledger.md`. If a ledger row changes, change the slide.

## Slide 1: Problem

- Attackers hide stolen secrets and data inside normal-looking traffic (DNS tunneling first).
- A single detector either misses it or floods the analyst with false alarms.
- Goal: escalate only when two independent detectors agree.
- Ledger: Correlation gate (Working), CoverTrace DNS entropy (Working).

## Slide 2: Product form

- Detection middleware. The engine and the CLI (`gkmkb replay <pcap>`) are the product. The web console is a viewer (ADR 0008).
- Today only the CLI exists. The console is Designed.
- Ledger: `gkmkb replay` CLI (Partial), Dashboard (Designed).

## Slide 3: Architecture

- Diagram from `docs/Architecture.md`: ReplaySource, FlowSight, CoverTrace, gate, MimicNet, rules, dashboard.
- Modules import only from `contracts/`. Detectors run in-process (ADR 0002). Gate rule in ADR 0003.
- Colour the boxes by ledger state: Working (contracts, replay, gate, CoverTrace DNS entropy), Stub (FlowSight), Designed (MimicNet, rules, dashboard, backend services).

## Slide 4: What is done

- Contracts, replay capture, correlation gate, CoverTrace DNS entropy detector, lab pcaps. Each is Working in the ledger, with its PR number (#34, #37, #36, #41, #39).
- 41 tests pass on `main`.
- CLI demo screenshot (blocked on #5, take it once that lands): `gkmkb replay data/demo/dns_tunnel_plus_benign.pcap` gives 1 alert on 10.0.2.20; `data/demo/single_signal_control.pcap` gives 0 alerts.
- Say on the slide: this result was checked by hand. The CLI is Partial in the ledger because no test asserts it on those two files and rule proposals are not printed yet.
- Say on the slide: the alert pairs the real entropy signal with the FlowSight stub.
- Pcaps are crafted with scapy, seed 42, synthetic.

## Slide 5: What is partial or stub

- FlowSight: `[stub]`. No flow features and no classifier. The paper has a synthetic benchmark only.
- CoverTrace: one detector (DNS entropy). ICMP chi-square, HTTP/protocol checks and the adaptive baseline are Designed.
- `gkmkb replay` CLI: Partial.
- Report outline: Partial. No results.
- No evaluation numbers yet. Do not quote any.

## Slide 6: Cycles and cut line

- Cycle 1 (to 2026-10-24): foundation as listed in slide 4, plus ledger, slides, planned tickets.
- Cycle 2: real FlowSight, gate tested against it, backend + Mongo + WebSocket, dashboard shell, other CoverTrace indicators, evaluation v1.
- Cycle 3: one Docker honeypot, MITRE mapping, session view.
- Cycle 4: adaptive thresholds, closed-loop rules, fingerprint variation.
- Cycle 5: final evaluation, one-command demo, report, AI disclosure.
- Cut line, dropped first to last: fingerprint evasion, closed-loop rules, adaptive thresholds, FlowSight classifier (keep the rule-based stub), MimicNet depth. Never dropped: replay, CoverTrace, gate, CLI, dashboard alert.
- Final date is not fixed.

## Slide 7: Team split

- Ayush (lead): built the Cycle 1 foundation: contracts, repo and CI, replay, CLI, gate. Reviews every PR.
- Teammates join in Cycle 2 on their areas:
  - Shivansh: CoverTrace detectors and baseline.
  - Bhargav: lab data, slides, dashboard shell and views.
  - Sharukh: ledger, datasets, evaluation, report, ethics, MITRE table.
- FlowSight and MimicNet owners are open.
- All four use AI coding tools. Rule: the owner explains every line, tests ship with the PR, the report discloses AI assistance.

## Slide 8: Ethics

- Lab pcaps only, from our own machines or crafted. No real users' traffic (ADR 0007, `data/MANIFEST.md`).
- Public datasets are cited with licence when used. None used yet.
- The honeypot (Cycle 3) is Designed. It will run one container on our own network.
- AI assistance is disclosed in the report.

## Notes for the builder

- One idea per slide. Put the ledger state next to each claim.
- Do not add a claim that is not in `docs/Ledger.md`. Do not call FlowSight real.
- Ayush reviews the ledger and the deck before 2026-10-24.
