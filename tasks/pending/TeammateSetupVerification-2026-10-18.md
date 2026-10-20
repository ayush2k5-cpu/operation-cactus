# [GKMKB] Verify setup script on clean machines

## What
Run scripts/setup.ps1 on each teammate laptop, record failures, fix script and README.

## Why
Setup must work for people without Ojas or Claude.

## Acceptance Criteria
- [ ] Each of 3 teammates completes setup, tests pass
- [ ] Failures logged and fixed in script or README

## Blockers
RepoSkeletonAndCi

## Agent
Unassigned

## Owner
Shivansh, Bhargav, Sharukh (each on own laptop)

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-18 (revised 2026-10-20)

## Steps
1. Accept the GitHub invite and run `gh auth login`.
2. Clone the repo and run `scripts/setup.ps1` (Windows) or `scripts/setup.sh`. If a prompt asks to install, answer `y`.
3. Run `.\.venv\Scripts\python -m pytest -q` (or the Linux path). Note the result.
4. Follow `docs/WorkflowSetup.md` sections 2 and 3: open your AI tool, run the glossary check, install the seven skills.
5. Append one row to `docs/SetupLog.md`: name, OS, RAM, tool and version, setup result, anything that failed (paste the exact error line).
6. Fix what you can in the scripts or docs. Open a PR from `dev/<name>-setup-log` with the row and fixes.

Expected output: a row in `docs/SetupLog.md` and a working environment on every laptop.
