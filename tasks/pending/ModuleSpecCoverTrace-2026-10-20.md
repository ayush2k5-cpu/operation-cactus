# [GKMKB] Module Spec Cover Trace

## What
Spec and plan the rest of CoverTrace (ICMP chi-square, HTTP/protocol checks, adaptive baseline) using the team skills.

## Why
Review 2 needs planned tickets, and the owner should shape his own module.

## Acceptance Criteria
- [ ] Spec saved under docs/specs/
- [ ] Tickets generated with /to-tickets in the repo format, each with Steps
- [ ] Existing overlapping tickets replaced, not duplicated
- [ ] Ayush reviewed

## Blockers
None

## Agent
Claude Code or Antigravity

## Owner
Shivansh

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-20

## Steps
1. Read `docs/specs/GkmkbSpec.md`, `GLOSSARY.md`, ADR 0002 and the existing tickets `IcmpTimingChiSquare`, `HttpHeaderAndProtocolValidation`, `AdaptiveBaseline`.
2. In your agent run `/grill-with-docs` on "CoverTrace beyond DNS entropy". Answer its questions. Let it update `GLOSSARY.md` and propose ADRs. Mention Paper 1's four CoverTrace features.
3. Run `/to-spec` and save the result as `docs/specs/CoverTraceSpec.md`.
4. Review the spec with Ayush.
5. Run `/to-tickets` on the spec. Tickets go to `tasks/pending/` in the repo format (`docs/agents/issue-tracker.md`). Replace the three existing tickets instead of duplicating them: copy useful text, then delete the old files in the same PR.
6. Open the PR.

Expected output: `docs/specs/CoverTraceSpec.md` and tickets with Steps, owner Shivansh, cycles 2 to 4.
