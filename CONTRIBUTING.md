# Contributing to GKMKB

## Module owners
| Area | Owner | GitHub |
|---|---|---|
| Lead, contracts, CI, replay, CLI, gate, backend | Ayush | ayush2k5-cpu |
| M1 CoverTrace | Shivansh | TBD |
| Lab pcaps, fixtures, slides, dashboard (later) | Bhargav | TBD |
| Ledger, datasets, evaluation, report, MITRE table | Sharukh | TBD |
| M2 FlowSight, M3 MimicNet | Open (after Review 2) | |

Same names go into `.github/CODEOWNERS` once usernames are known. Ayush reviews every PR during Cycle 1.

## Flow
1. Pick a ticket from `tasks/pending/` in your module. Set `## Owner` to your name. Move the file to `tasks/in-progress/` in the same PR as your first commit.
2. Branch from `main`: `dev/<name>-<ticket>` (e.g. `dev/shivansh-dns-entropy`). Git rules: `docs/rules/GitRules.md`.
3. Commit small, Conventional Commits: `feat: add subdomain entropy function`.
4. Push and open a PR into `main`. Fill the PR template. Link the ticket file.
5. One review from another teammate and green CI before merge. Squash merge.
6. On merge, move the ticket to `tasks/done/` and update the honesty ledger in `docs/specs/GkmkbSpec.md` if a capability changed state.

## AI-assisted coding
AI tools are fine and encouraged. Rules: the PR author can explain every line, tests ship with the code, `AGENTS.md` is followed, and the report discloses AI assistance. No AI attribution anywhere in git (`docs/rules/GitRules.md`).

## Rules
- Never push to `main`.
- Stay inside your module folder. Touching another module needs that owner's review.
- `contracts/` changes need approval from all owners. Never edit a contract to fit your code without the PR discussion.
- Modules import only from `contracts/`, not from each other (`docs/Architecture.md`).
- Every PR ships tests for the code it adds.
- Do not claim in docs, report or slides what is not merged and working. Use the words Designed, Partial, Working.
- No secrets in git. Use `.env` (ignored).
- No real users' traffic. Lab or dataset pcaps only. Large pcaps stay out of git (`data/` is ignored except `data/README.md` and small test files).

## Local checks before a PR
```bash
.venv/bin/python -m ruff check .     # Windows: .\.venv\Scripts\python -m ruff check .
.venv/bin/python -m pytest -q
cd dashboard && npm run lint && npm run build
```

## Repo setup for Ayush (one time)
```bash
gh repo create gkmkb --private --source . --remote origin --push
gh api -X PUT repos/<owner>/gkmkb/collaborators/<username> -f permission=push   # per teammate
```
Then in GitHub Settings > Branches: protect `main` (require PR, 1 approval, status checks, no force push).
