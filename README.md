# GKMKB — Guarded Kill-chain Monitoring & Key Breach

> Operation Cactus is the final-year project. GKMKB (Guarded Kill-chain Monitoring & Key Breach) is its Phase-II name and the name used in the code and docs.

Detection middleware: a headless engine with a CLI (`gkmkb replay <pcap>`) and a thin web console. Replayed traffic goes through two independent detectors (FlowSight, CoverTrace). A gate escalates only when both agree. MimicNet traps the attacker in a Docker honeypot and feeds new detection rules back. An analyst dashboard shows it live.

BCY705 Capstone Phase-II, DSATM, B.E. CSE (Cyber Security).
Team: Ayush Rathod, Sharukh Khan, Shivansh Tripathi, Bhargav Moray.

Status (2026-10-22): the engine foundation is built (contracts, replay, gate, CLI, DNS entropy detector, demo pcaps). Module specs and tickets are written; module work starts in Cycle 2. The honesty ledger is `docs/Ledger.md`.

**New teammate? Start with `docs/Onboarding.md`.**

## Read first
0. `docs/Onboarding.md` — what to do and what not to do
1. `docs/specs/GkmkbSpec.md` — what we build, contracts, demo, milestones
2. `docs/Architecture.md` — diagram, folders, boundary rules
3. `docs/adr/` — why each big choice
4. `GLOSSARY.md` — shared words
5. `CONTRIBUTING.md` — branch and PR flow
6. GitHub Issues — your tickets (filter by label `owner:<name>`)

## Quick start (new teammate)
You need only a Windows, macOS or Linux machine and a GitHub account. You do **not** need Claude, Ojas or any AI tool.

### 1. Accept the repo invite
Ayush adds you as a collaborator. Accept the email invite, or at https://github.com/notifications.

### 2. Clone and run setup
Windows (PowerShell):
```powershell
git clone https://github.com/ayush2k5-cpu/operation-cactus.git
cd operation-cactus
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup.ps1
```
macOS / Linux:
```bash
git clone https://github.com/ayush2k5-cpu/operation-cactus.git
cd operation-cactus
bash scripts/setup.sh
```
The script installs Git, Python 3.12, Node.js LTS, GitHub CLI and Docker Desktop when missing (Windows uses winget). It then creates `.venv`, installs Python and dashboard dependencies, copies `.env.example` to `.env`, pulls Docker images and runs tests. Safe to re-run. Add `-Yes` (Windows) or `--yes` (bash) to skip prompts.

Docker Desktop needs WSL2 and a reboot after first install. Start Docker Desktop before running the stack.

### 3. Log in to GitHub
```bash
gh auth login
```

### 4. Set up the shared AI workflow (recommended)
Follow `docs/WorkflowSetup.md` once. It installs the shared skills and shows the daily loop.

### 5. Pick a ticket and start
Open the Issues tab, take an issue with your `owner:<name>` label, then run `python scripts/ticket.py start <issue number>`. When you are done run `python scripts/ticket.py submit <issue number>`; it opens a PR into your module branch. Details in `CONTRIBUTING.md`.

## Run the stack (database and backend)
Needs Docker running. From the repo root:
```bash
docker compose up --build        # start; wait until both services show "healthy"
curl http://127.0.0.1:8000/api/health
curl -X POST http://127.0.0.1:8000/api/replay -H "Content-Type: application/json" -d '{"pcap": "demo/dns_tunnel_plus_benign.pcap"}'
curl http://127.0.0.1:8000/api/alerts
docker compose down              # teardown, keeps the database volume
docker compose down -v           # teardown and delete the database volume
```
The backend listens on `127.0.0.1:8000` only. `data/` is mounted read-only at `/app/data`. Settings come from `.env.example`; the compose file overrides the Mongo address, the bind host and the data path for the container.

Known failure points:
- Docker Desktop not running: `docker compose` cannot connect to the daemon. Start it and retry.
- Port 8000 already in use (for example a local `gkmkb serve`): stop that process or the stack fails to start.
- First `--build` is slow and large (scikit-learn, xgboost, scipy); later builds use the cache.
- Backend stays `starting` until Mongo is healthy; on a slow laptop that can take about a minute.
- A replay of a pcap that is not under `data/` is rejected; there is no upload.
- Changing `.env.example` needs `docker compose up -d` again to take effect.

Risk for the MimicNet spec: the honeypot needs the backend to start containers, which means giving the backend container the host Docker socket. This compose file does not do that. Mounting the socket gives the container control of the host, so the MimicNet spec must decide how to grant it.

Status: written but not yet verified by hand on a clean machine (see PR).

## Modules
| Module | Folder | What |
|---|---|---|
| M1 CoverTrace | `covertrace/` | Entropy, chi-square timing, protocol checks, adaptive baseline |
| M2 Capture + FlowSight | `capture/`, `flowsight/` | pcap to flows, flow features, classifier |
| M3 MimicNet | `mimicnet/` | Docker honeypot, MITRE map, rule generation |
| M4 Backend + Dashboard | `backend/`, `dashboard/`, `contracts/`, `eval/` | API, gate, UI, demo, CI |

Owners are listed in `CONTRIBUTING.md`. Tickets and cycles: GitHub Issues and milestones. Next milestone: Review 2 on 2026-10-24 (engine slice).

## License
All rights reserved for now: the code is public to be viewed and reviewed, not reused (see `LICENSE`). The authors will choose an open license at final submission.

## Ethics
All demo and evaluation traffic is replayed from datasets or generated in an isolated lab on team-owned machines with consent. Never capture or test against anyone's real traffic or systems.

## Troubleshooting
- `winget` not found: update "App Installer" from the Microsoft Store, or install tools by hand.
- `python` opens the Store: turn off the App execution alias for python.exe, or use `py -3.12`.
- Docker will not start: enable virtualization in BIOS, run `wsl --install`, reboot.
- Script blocked: `Set-ExecutionPolicy -Scope Process Bypass` in the same window.
