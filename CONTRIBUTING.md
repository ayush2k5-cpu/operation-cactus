# Contributing to GKMKB

## Module owners
| Area | Owner | GitHub |
|---|---|---|
| Lead, contracts, CI, replay, CLI, gate, backend | Ayush | ayush2k5-cpu |
| M1 CoverTrace, M3 MimicNet | Shivansh | TBD |
| M2 FlowSight, lab pcaps and fixtures | Bhargav | TBD |
| Ledger, datasets, evaluation, report, MITRE table | Sharukh | TBD |
| Dashboard (for now) | Ayush | ayush2k5-cpu |

Same names go into `.github/CODEOWNERS` once usernames are known. Ayush reviews every PR during Cycle 1.

## Branches
```
main                        stable, only Ayush merges here
mod/covertrace              one long-lived branch per module:
mod/flowsight                 covertrace, flowsight, mimicnet, backend (the dashboard lives here too), eval
mod/mimicnet
mod/backend
mod/eval
<module>/<owner>-<ticket>   short ticket branch, cut from its module branch
```
A branch called `mimicnet` and a branch called `mimicnet/x` cannot coexist in git, which is why module branches live under `mod/`.

## Flow (teammates)
1. Pick an open issue with your `owner:<name>` label (`gh issue list --label owner:<name> --state open`, or the GitHub Issues tab).
2. Start it: `python scripts/ticket.py start <issue>`. This makes `<module>/<owner>-<ticket>` from your module branch and comments "taking this". Never work on `main` or on a `mod/` branch directly.
3. Build with small commits, Conventional Commits: `feat: add subdomain entropy function`.
4. Submit it: `python scripts/ticket.py submit <issue>`. It runs ruff and pytest, pushes, and opens a PR into **your module branch** (not `main`).
5. When CI is green, merge your own PR into the module branch with a merge commit (not squash, not rebase). Never delete branches yourself and never tick "delete branch" on a PR. Branches stay until Ayush asks for a cleanup.
6. Ayush merges the module branch into `main` at milestones and whenever another module needs your code (`python scripts/release.py <module>`). The issue closes then.

## Shared files
Only Ayush edits `GLOSSARY.md`, `docs/adr/`, `docs/specs/`, `docs/Ledger.md`, `docs/report/`, `contracts/` and `CONTRIBUTING.md`. One exception: a ticket may tell you to add a new file under `docs/report/` (for example the evaluation chapter); you may add that new file but never edit an existing report file. If your ticket says "update the ledger", write the state change (Designed, Partial or Working, with the evidence) in the PR body instead, under "Ledger". Ayush records it when he merges to `main`. If you need a shared file changed, say so in the PR.

## Flow (Ayush)
- Your own tickets follow the same path through `mod/backend`.
- `scripts/release.py <module>` opens the module-to-main PR with a `Closes #N` line per ticket. Update the shared files, check CI, merge with a merge commit.
- After each merge to main, run `python scripts/sync_modules.py`. It merges `main` back into every `mod/` branch and lists any conflict for you to merge by hand. (A GitHub Action cannot do this: user-owned repos cannot give Actions a ruleset bypass.)
- Tickets labelled `module:workflow` go to `main` directly by PR, reviewed by you.

## AI-assisted coding
AI tools are fine and encouraged. Rules: the PR author can explain every line, tests ship with the code, `AGENTS.md` is followed, and the report discloses AI assistance. No AI attribution anywhere in git (`docs/rules/GitRules.md`).

## Rules
- Never push to `main` or to a `mod/` branch. Always use a ticket branch and a PR.
- Stay inside your module folder. Touching another module or a shared file needs Ayush.
- `contracts/` changes are Ayush's. If your code needs a different contract, say so in the PR.
- Modules import only from `contracts/`, not from each other (`docs/Architecture.md`).
- Every PR ships tests for the code it adds.
- Do not claim in docs, report or slides what is not merged and working. Use the words Designed, Partial, Working.
- No secrets in git. Use `.env` (ignored).
- No real users' traffic. Lab or dataset pcaps only. Large pcaps stay out of git (`data/` is ignored except `data/README.md` and small test files).

## Local checks before a PR
```bash
.venv/bin/python -m ruff check .          # Windows: .\.venv\Scripts\python -m ruff check .
.venv/bin/python -m ruff format --check . # fix with: ruff format .
.venv/bin/python -m pytest -q
cd dashboard && npm run lint && npm run build
```

## Repo setup for Ayush (one time)
```bash
gh api -X PUT repos/ayush2k5-cpu/operation-cactus/collaborators/<username> -f permission=push   # per teammate
```
Module branches already exist (`mod/covertrace`, `mod/flowsight`, `mod/mimicnet`, `mod/backend`, `mod/eval`). The repo is public so branch rulesets are free. They live in `.github/rulesets/` and are applied with `python scripts/apply_rulesets.py`:
- `main`: no direct pushes, no deletion, no force push, a PR with your approval (as code owner) and green CI, merge commits only. You bypass through a PR.
- `mod/**`: a PR and green CI, no approval needed (teammates merge their own), merge commits only, no deletion, no force push. You bypass it to sync with `scripts/sync_modules.py`.
- every branch: no deletion and no force push (you can bypass when you clean up).
