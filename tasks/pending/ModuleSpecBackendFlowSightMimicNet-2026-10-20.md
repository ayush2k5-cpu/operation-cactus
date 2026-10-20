# [GKMKB] Module Spec Backend Flow Sight Mimic Net

## What
Spec and plan the backend, FlowSight and MimicNet using the team skills, so M2 and M3 owners can be assigned.

## Why
M2 and M3 have no owner yet; their specs and tickets let anyone pick them up.

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
Ayush

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-20

## Steps
1. Read `docs/specs/GkmkbSpec.md`, ADRs 0001 to 0008 and the existing tickets for these modules.
2. Run `/grill-with-docs` on the backend (gate, persistence, WebSocket, compose). Run `/to-spec` and save as `docs/specs/BackendSpec.md`.
3. Repeat for FlowSight (`docs/specs/FlowSightSpec.md`) and MimicNet (`docs/specs/MimicNetSpec.md`).
4. Run `/to-tickets` for each. Replace the existing tickets instead of duplicating.
5. Decide M2 and M3 owners and update `CONTRIBUTING.md`.
6. Open the PR.

Expected output: three specs, tickets with Steps, owners assigned.
