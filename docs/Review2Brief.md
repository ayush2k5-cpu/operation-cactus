# GKMKB: Review 2 brief

Use this page to build the slides. Every claim matches `docs/Ledger.md`. If a claim is not on this page, do not put it on a slide. Where this page says "not built", the slide must say so too.

Project name: **GKMKB** (repository: operation-cactus). Team of four, final-year capstone, BCY705, DSATM.
Team: Ayush Rathod (lead), Sharukh Khan, Shivansh Tripathi, Bhargav Moray.

## 1. One-line pitch

GKMKB is detection middleware that finds data hidden inside normal-looking network traffic (DNS tunneling first). It raises an Alert only when two independent detectors agree, so the analyst sees fewer false alarms, and it then traps the attacker in a fake system to record what they do.

## 2. The problem

- Attackers hide stolen data and remote-control traffic inside traffic that looks normal, such as DNS lookups.
- One detector alone either misses it or raises many false alarms.
- After an alert, the analyst learns nothing about what the attacker does next.

## 3. The idea in four steps

1. **Replay.** A recorded network capture (pcap) is read and turned into flows.
2. **Two detectors, independent.** FlowSight looks only at packet sizes and timing. CoverTrace looks at what is inside DNS queries (how random the names look). Neither sees the other's result.
3. **Gate.** An Alert is raised only when both detectors flag the same machine within a time window.
4. **Response.** The Alert starts a honeypot: a fake SSH-like shell in one locked-down container. It records every command the attacker types. The Console shows the session.

## 4. Architecture (for the diagram slide)

Flow of data, left to right:

`pcap file -> ReplaySource -> flows -> FlowSight + CoverTrace -> Detections -> Gate -> Alert -> honeypot (Docker) -> session -> Console`

Rules of the design:
- Modules talk only through shared data types in `contracts/` (Flow, Detection, Alert, Session).
- Detectors run in-process and are independent (ADR 0002). The gate rule is ADR 0003.
- The engine and the command-line tool are the product; the web Console is a viewer (ADR 0008).
- Backend: FastAPI with live WebSocket events, MongoDB or in-memory storage, Docker compose for the database and API.

Colour the boxes by state in section 5.

## 5. What is built, honestly

Use these states on every slide. Evidence is in `docs/Ledger.md`.

| Part | State | What exists |
|---|---|---|
| Shared data types | Working | `contracts/`, tested |
| Replay capture | Working | pcap to flows; a file that is not a pcap now fails clearly |
| Correlation gate | Working | one Alert only when both detectors agree; tested |
| CoverTrace | Partial | entry point and settings file; one checker: DNS name randomness (entropy). No ICMP, HTTP or ping checks yet |
| FlowSight | Partial | per-machine sliding window, four flow features, a rule-based scorer. **Not a trained model.** No classifier yet |
| Honeypot | Partial | fake SSH-like shell; runs in one container (no network, 128 MB, half a CPU, 120 s limit, read-only, no extra privileges); container removed after; real-Docker test passes in CI. Scripted attacker only |
| Backend | Partial | replay API, live events, REST lists, close Alert, session endpoint, storage. MongoDB code has no automated test against a real database |
| Compose stack | Partial | database and backend start healthy; run by hand on one laptop, not on a clean machine |
| Console (web) | Partial | start a replay, live Detections and Alerts, past replays, threshold compare, session view for an engaged Alert, styled |
| Evaluation | Partial | labels, metric functions and a runner on crafted pcaps; synthetic data only |

Test status: about 180 automated tests pass on the main branch; CI runs them on every change.

## 6. Live demo (about 4 minutes)

Before the review: Docker Desktop running, laptop on power, run the setup once (`scripts/setup.ps1`). Run step 1 and 2 once beforehand: the first honeypot run downloads the `python:3.12-slim` image and takes longer.

**Automatic run.** `python scripts/demo.py` runs every step below by itself (command line, backend API, honeypot, evaluation) and prints PASS or FAIL for each. Use it the evening before and an hour before the review. `python scripts/demo.py --console` also starts the Console, opens it in the browser and keeps running until Ctrl+C. Add `--no-honeypot` if Docker is not running. Run it with the project Python: `.\.venv\Scripts\python.exe scripts/demo.py`.

To run the steps by hand, start two terminals from the repo root (PowerShell):

```powershell
$env:HONEYPOT_ENGAGE="1"; $env:DATA_DIR="data/demo"; $env:REPLAY_EVENT_DELAY_MS="400"
.\.venv\Scripts\python.exe -m backend.gkmkb.cli serve
```

```powershell
npm --prefix dashboard run dev
```

Open http://localhost:5173. Steps and what the audience should see:

1. **Tunnel pcap.** Pick `dns_tunnel_plus_benign.pcap`, press Start replay. Detections appear one at a time: a FlowSight one and a CoverTrace one on the same machine (10.0.2.20). Then one Alert.
2. **Honeypot.** Within seconds the Alert changes to "engaged". Press Open session: attacker address 192.0.2.50, the commands the attacker typed (`whoami`, `uname -a`, `cat /etc/passwd`, an `iodine` tunnel command, `exit`). The container is already gone.
3. **Control pcap.** Pick `single_signal_control.pcap`. Result: 0 Alerts. One signal alone is not enough.
4. **Hard benign pcap.** Pick `hard_benign_dns.pcap`. FlowSight alone flags it (a false alarm), but the gate raises 0 Alerts because CoverTrace disagrees. This is the point of the gate.
5. **Past Replays and Compare.** Show the replay list and the threshold compare view (labelled "from Detections").
6. **Command-line tool** (optional): `.\.venv\Scripts\python.exe -m backend.gkmkb.cli replay data\demo\dns_tunnel_plus_benign.pcap` prints the same result as text.
7. **Failure case** (optional): replay a file that is not a pcap; the Console shows "Replay failed" with the reason.

All demo pcaps are crafted in the lab (scapy, seed 42). They are synthetic.

## 7. Numbers we can show

From `python -m eval` on the crafted lab pcaps (`eval/results/crafted_results.csv`). **Synthetic data, four machines, one of them a tunnel. Not a claim about real traffic.**

| Target | Hits | Misses | False alarms | True negatives | Precision | Recall |
|---|---|---|---|---|---|---|
| CoverTrace | 1 | 0 | 0 | 3 | 1/1 | 1/1 |
| FlowSight | 1 | 0 | 1 | 2 | 1/2 | 1/1 |
| Gate (both agree) | 1 | 0 | 0 | 3 | 1/1 | 1/1 |

What it shows: on one hard benign machine FlowSight alone raises a false alarm; the gate removes it. What it does not show: anything about real networks. The sample is tiny. Say so on the slide.

Do not quote any other number. No detection rate on real traffic exists yet.

## 8. Not built yet (say it plainly)

- A trained FlowSight classifier and any result on real tunnel traffic. The real dataset (CIC-Bell-DNS-EXF-2021) is checked but not downloaded; its download needs a request form.
- More CoverTrace checks: ICMP, HTTP/protocol, ping timing, episode and skip-list rules, adaptive thresholds.
- MITRE ATT&CK tags on sessions. The session view says "MITRE tags: none yet".
- Rules learned from honeypot sessions, an approve/reject Rules view, and the closed loop (a learned Rule making the next detection earlier). These are the novelty claim and they are **not built**.
- The compose stack cannot start honeypots (it has no Docker access by design); the honeypot runs when the backend runs on the laptop.
- Evaluation comparisons on real data, retraining the Paper 1 baseline, the report evaluation chapter.
- Live capture with libpcap (stretch goal; replay-first by design, ADR 0001).

## 9. Plan after Review 2

- Cycle 2 (core path): about 86 percent of its tickets are merged. Left: CoverTrace episodes and skip-list, the real-dataset decision, the team consent record, setup check on clean laptops.
- Cycle 3 (response layer): MITRE mapping and the session timeline with tags.
- Cycle 4 (novelty): rules from sessions, Rules view, closed loop, adaptive thresholds.
- Cycle 5 (prove): final evaluation (gate vs single detector, fixed vs learned limit, before/after a Rule), one-command demo, report, AI disclosure.
- Cut line, dropped first to last: banner variation, closed loop, adaptive thresholds, FlowSight classifier (keep the rules), MimicNet depth. Never dropped: replay, CoverTrace, gate, command-line tool, Console Alert view.
- Final date is not fixed.

## 10. Team and who did what

- **Ayush (lead):** architecture, repository and CI, replay, command-line tool, gate, backend, Console, honeypot wiring, release management. Reviews every change.
- **Bhargav:** FlowSight window features with hand-computed tests; verified the real dataset page, licence and size.
- **Sharukh:** evaluation: pcap labels and a hard benign set, metric functions, the evaluation runner.
- **Shivansh:** owner of the CoverTrace and MimicNet tickets. His remaining tickets (episodes and skip-list, ping timing, banner variation) are open; the lead built the CoverTrace entry point and the honeypot in the meantime.

Process worth one slide: tickets are GitHub Issues; each teammate works on a ticket branch, opens a pull request into a module branch, CI runs, the lead releases to main. A dispatcher builds some tickets with AI coding agents and every result is reviewed by a person.

## 11. Ethics and AI disclosure

- Lab pcaps only, crafted or from our own machines. No real users' traffic (ADR 0007, `data/MANIFEST.md`).
- Capturing real tunnel traffic from team laptops needs a written consent record first (ticket #83). Nobody has consented yet.
- Public datasets are cited with licence. None is used yet.
- The honeypot runs one container on our own machine, with no network.
- The team uses AI coding assistants. The rule is: the owner explains every line, tests ship with the code, and the report discloses AI assistance.

## 12. Suggested slides (10)

1. Title and team.
2. Problem: hidden data in normal traffic; one detector is not enough.
3. Idea: two independent detectors, one gate, then a trap.
4. Architecture diagram (section 4), boxes coloured by state.
5. What is built (table in section 5).
6. Live demo (section 6). Keep this slide empty or one screenshot.
7. Numbers (section 7) with the synthetic warning.
8. What is not built yet (section 8). Do not skip this slide.
9. Plan, cycles and cut line (section 9).
10. Ethics, AI disclosure and team process (sections 10 and 11).

## 13. Likely questions

- **"Is FlowSight machine learning?"** Not yet. It is a rule-based scorer on four flow features. A trained classifier is planned (Cycle 4, first thing we cut if late).
- **"Does it work on real traffic?"** We have no result on real traffic. All numbers are on crafted lab pcaps.
- **"Why two detectors?"** One signal alone raised a false alarm in our test (the hard benign pcap). Requiring both removed it.
- **"Is the attacker real?"** No. The attacker in the honeypot is a fixed list of commands the team plays. It shows the recording works, not that we defeat attackers.
- **"What is new compared with the papers?"** The correlation of two independent detectors, the automatic response, and (planned, not built) rules learned from sessions.
- **"Can it run live on a network?"** Not yet. It replays captures. Live capture is a stretch goal.
