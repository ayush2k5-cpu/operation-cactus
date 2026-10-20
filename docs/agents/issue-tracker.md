# Issue tracker: GitHub Issues + Projects

Tickets for this repo are GitHub Issues in `ayush2k5-cpu/fyp-untitled`. Use the `gh` CLI. Skills that say "publish to the issue tracker" run `gh issue create`.

## Conventions
- One ticket per issue. Title is a short imperative phrase.
- Body sections in this order: `**Owner:**` line, `## What`, `## Why`, `## Acceptance Criteria` (checkboxes), `## Blockers` (issue numbers like `#29`, or `None`), optional `## Steps` (numbered, with an "Expected output" line).
- Labels: exactly one `module:*` (covertrace, flowsight-capture, mimicnet, backend-console, data-eval, workflow), one `cycle-N`, and one or more `owner:*` (ayush, shivansh, bhargav, sharukh, open).
- Milestone = cycle (`Cycle 1 - Review 2` is due 2026-10-24). Cycles are defined in `docs/specs/GkmkbSpec.md` section 9.
- State: open or closed. A PR with `Closes #N` in its body closes the ticket on merge.
- Blocking: list blocker issue numbers under `## Blockers`. A ticket is unblocked when each listed issue is closed.
- Comments and conversation go in the issue thread.

## When a skill says "publish to the issue tracker"
```bash
gh issue create --repo ayush2k5-cpu/fyp-untitled --title "<title>" --body-file <file> \
  --label "module:<m>" --label "cycle-<n>" --label "owner:<name>" --milestone "Cycle <n> - ..."
```
Create blockers first so later tickets can reference their numbers.

## When a skill says "fetch the relevant ticket"
`gh issue view <number>`. Find tickets with `gh issue list --label "owner:<name>" --state open`.

## Claiming and finishing
- Claim: comment "taking this" on the issue and branch `dev/<name>-<ticket>`. Assign yourself when your GitHub username is known.
- Finish: the merging PR says `Closes #N`. Update the honesty ledger if a capability changed state.
