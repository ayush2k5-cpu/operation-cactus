# GKMKB — Agent Instructions

Applies to any AI coding agent (Claude Code, Antigravity, others). Plain markdown; no external tooling needed.

## What this is
GKMKB: detection middleware. Engine + CLI (`gkmkb replay <pcap>`) is the product; the web console is a viewer. Read `README.md`, `docs/specs/GkmkbSpec.md`, `docs/Architecture.md` and `GLOSSARY.md` before coding. Decisions are in `docs/adr/`.

## Before you code
1. Read your ticket in `tasks/pending/` or `tasks/in-progress/`. Work only on that ticket.
2. Use `GLOSSARY.md` terms exactly (Detection, Alert, Entity, Gate, Engine). Do not invent synonyms.
3. Stay inside your module folder. Modules import only from `contracts/`, never from each other. The backend wires modules together.
4. Do not change `contracts/` unless the ticket says so; a contracts change needs all owners to review.

## While coding
- Smallest code that meets the acceptance criteria. No extra abstractions, no unused config.
- Tests ship with the code (pytest). A change without a test is not done.
- Python 3.12, type hints, `ruff` clean. Dashboard: React + Recharts, `npm run lint` clean.
- Detectors take `FlowRecord`s and may keep in-memory state per entity (window, baseline); no network or DB calls inside them.
- Config (thresholds, windows) goes in config or `.env`, not constants.
- No secrets in git. No real users' traffic. Pcaps come from `data/` (crafted or public datasets).

## Honesty
Every capability is Designed, Partial or Working (`GkmkbSpec.md` section 8). Mark stub code with a visible `[stub]` tag in output and docstring. Never write docs, comments or reports that claim more than the code does.

## Git and PRs
- Follow `docs/rules/GitRules.md`: branch `dev/<name>-<ticket>` from `main`, never push to `main`, Conventional Commits, no AI attribution in commits, PRs or code comments.
- PR uses `.github/PULL_REQUEST_TEMPLATE.md`, links the ticket, and updates the honesty ledger if a capability changed state.
- The owner must be able to explain every line in a viva. Do not paste code you cannot explain.

## Agent skills
The team uses a shared set of skills from `mattpocock/skills` (MIT, reviewed by Ayush at commit `49dd158d`). Each teammate installs them locally; they are not committed to this repo. Setup: `docs/WorkflowSetup.md`. If a skill is not installed, follow the written rules in this file instead.

### Issue tracker
Local markdown in `tasks/`. See `docs/agents/issue-tracker.md`.

### Domain docs
Single-context: `GLOSSARY.md` + `docs/adr/`. See `docs/agents/domain.md`.

### Which skill, when
| Situation | Skill |
|---|---|
| Idea or ticket is unclear | `/grill-with-docs` (updates GLOSSARY and ADRs as terms settle) |
| Need a spec for a new feature | `/to-spec`, saved in `docs/specs/` |
| Spec ready, need tickets | `/to-tickets`, written to `tasks/pending/` in the repo ticket format |
| Designing or deepening a module | `/codebase-design` |
| Writing the PR body | `/pr` (no AI attribution lines) |
Do not run `/setup-matt-pocock-skills` here; the config is already committed. Triage labels are not used.

## When unsure
Ask the owner of the ticket. If a decision is not in the spec or an ADR, write a short note in the PR rather than guessing.
