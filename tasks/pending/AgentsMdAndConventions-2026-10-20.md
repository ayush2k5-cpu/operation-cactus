# [GKMKB] Agents Md And Conventions

## What
Write AGENTS.md and CLAUDE.md pointer for the team repo: glossary use, ADR list, ticket format, module boundaries, test and PR rules, honesty labels.

## Why
Claude and Antigravity must behave the same for every teammate without Ojas.

## Acceptance Criteria
- [ ] AGENTS.md under 150 lines, plain markdown
- [ ] Tells agents to read GLOSSARY.md, docs/Architecture.md and the ticket before coding
- [ ] States: modules import only from contracts/, tests ship with code, no claims beyond Working
- [ ] Antigravity and Claude Code both load it (tested once)

## Blockers
RepoSkeletonAndCi

## Agent
Claude Code

## Owner
Ayush

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-20

## Steps
1. Read `AGENTS.md` and `docs/WorkflowSetup.md`.
2. In Claude Code, open the repo and ask the glossary question from `docs/WorkflowSetup.md` section 2. Record the answer.
3. Repeat in Antigravity. Record whether it loaded `AGENTS.md` and whether the installed skills appear.
4. Fix `AGENTS.md` or `WorkflowSetup.md` for whatever failed. Keep `AGENTS.md` under 150 lines.
5. Confirm the exact `npx skills add` command and the skill picker prompts; correct section 3 of the guide.
6. Open the PR.

Expected output: both tools follow `AGENTS.md`; the guide matches reality.
