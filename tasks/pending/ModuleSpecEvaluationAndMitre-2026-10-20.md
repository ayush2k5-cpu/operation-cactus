# [GKMKB] Module Spec Evaluation And Mitre

## What
Spec and plan the evaluation harness and MITRE mapping using the team skills.

## Why
The report numbers must come from a planned, reproducible harness.

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
Sharukh

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-20

## Steps
1. Read `docs/specs/GkmkbSpec.md` section 7, Paper 1 (evaluation sections) and the existing tickets `CoverTraceEvaluation`, `MitreMapping`, `DatasetSpike`.
2. Run `/grill-with-docs` on "How do we evaluate GKMKB honestly?". Cover metrics, datasets, baselines (Paper 1 fused model) and limitations.
3. Run `/to-spec` and save as `docs/specs/EvalSpec.md`.
4. Review with Ayush.
5. Run `/to-tickets`. Replace the existing evaluation and MITRE tickets instead of duplicating.
6. Open the PR.

Expected output: `docs/specs/EvalSpec.md` and tickets with Steps, owner Sharukh.
