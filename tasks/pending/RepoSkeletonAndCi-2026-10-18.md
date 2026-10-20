# [GKMKB] Repo skeleton, CI and PR flow

## What
Create the GitHub repo layout from docs/Architecture.md, CI running lint and pytest on every PR, PR template, CODEOWNERS and branch protection notes.

## Why
Teammates need a protected main and a working PR loop before anyone writes code.

## Acceptance Criteria
- [ ] Repo has folders from Architecture.md with .gitkeep
- [ ] GitHub Actions runs ruff + pytest + dashboard lint on PRs
- [ ] PR template and CODEOWNERS present
- [ ] main requires 1 review + green CI (settings documented in CONTRIBUTING.md)

## Blockers
None

## Agent
Claude Code

## Owner
Ayush

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-18 (revised 2026-10-20)

## Steps
1. In `projects/active/GKMKB` run `git init -b main` and make the first commit (docs, tickets, scripts, config). Use `docs/rules/GitRules.md`.
2. Create the private repo and push: `gh repo create ayush2k5-cpu/gkmkb --private --source . --push`.
3. Add `pyproject.toml` with `ruff` settings (line length 100) and `pytest` settings (`testpaths = ["contracts", "capture", "flowsight", "covertrace", "mimicnet", "backend", "eval"]`).
4. Add `.github/workflows/ci.yml`: Python 3.12, `pip install -r requirements.txt -r requirements-dev.txt`, `ruff check .`, `pytest -q`. Add a dashboard job that runs only if `dashboard/package.json` exists.
5. Add `.github/CODEOWNERS` from the owner table in `CONTRIBUTING.md`.
6. Add the three teammates as collaborators: `gh api -X PUT repos/ayush2k5-cpu/gkmkb/collaborators/<user> -f permission=push`.
7. Protect `main` (PR required, 1 approval, CI required, no force push). Record the exact settings in `CONTRIBUTING.md`.
8. Open a first PR from `dev/ayush-repo-skeleton` and confirm CI turns green.

Expected output: private repo, three collaborators, green CI on a PR, `main` protected.
