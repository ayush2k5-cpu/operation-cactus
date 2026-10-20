# GKMKB — Guarded Kill-chain Monitoring & Key Breach

> Repo name `fyp-untitled` is a placeholder. The final-year project is untitled; GKMKB is the Phase-II working title and will be renamed when the team decides.

Detection middleware: a headless engine with a CLI (`gkmkb replay <pcap>`) and a thin web console. Replayed traffic goes through two independent detectors (FlowSight, CoverTrace). A gate escalates only when both agree. MimicNet traps the attacker in a Docker honeypot and feeds new detection rules back. An analyst dashboard shows it live.

BCY705 Capstone Phase-II, DSATM, B.E. CSE (Cyber Security).
Team: Ayush Rathod, Sharukh Khan, Shivansh Tripathi, Bhargav Moray.

Status: planning done, code not started (2026-10-20). See the honesty ledger in `docs/specs/GkmkbSpec.md` section 8.

## Read first
1. `docs/specs/GkmkbSpec.md` — what we build, contracts, demo, milestones
2. `docs/Architecture.md` — diagram, folders, boundary rules
3. `docs/adr/` — why each big choice
4. `GLOSSARY.md` — shared words
5. `CONTRIBUTING.md` — branch and PR flow
6. `tasks/pending/` — your tickets

## Quick start (new teammate)
You need only a Windows, macOS or Linux machine and a GitHub account. You do **not** need Claude, Ojas or any AI tool.

### 1. Accept the repo invite
Ayush adds you as a collaborator. Accept the email invite, or at https://github.com/notifications.

### 2. Clone and run setup
Windows (PowerShell):
```powershell
git clone https://github.com/ayush2k5-cpu/fyp-untitled.git
cd fyp-untitled
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup.ps1
```
macOS / Linux:
```bash
git clone https://github.com/ayush2k5-cpu/fyp-untitled.git
cd fyp-untitled
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
Open `tasks/pending/`, take a ticket in your module, put your name in its `Owner` line, move it to `tasks/in-progress/`, branch, code, open a PR. Details in `CONTRIBUTING.md`.

## Modules
| Module | Folder | What |
|---|---|---|
| M1 CoverTrace | `covertrace/` | Entropy, chi-square timing, protocol checks, adaptive baseline |
| M2 Capture + FlowSight | `capture/`, `flowsight/` | pcap to flows, flow features, classifier |
| M3 MimicNet | `mimicnet/` | Docker honeypot, MITRE map, rule generation |
| M4 Backend + Dashboard | `backend/`, `dashboard/`, `contracts/`, `eval/` | API, gate, UI, demo, CI |

Owners are listed in `CONTRIBUTING.md`. Ticket order and cycles: `tasks/README.md`. Next milestone: Review 2 on 2026-10-24 (engine slice).

## Ethics
All demo and evaluation traffic is replayed from datasets or generated in an isolated lab on team-owned machines with consent. Never capture or test against anyone's real traffic or systems.

## Troubleshooting
- `winget` not found: update "App Installer" from the Microsoft Store, or install tools by hand.
- `python` opens the Store: turn off the App execution alias for python.exe, or use `py -3.12`.
- Docker will not start: enable virtualization in BIOS, run `wsl --install`, reboot.
- Script blocked: `Set-ExecutionPolicy -Scope Process Bypass` in the same window.
