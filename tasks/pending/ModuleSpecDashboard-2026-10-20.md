# [GKMKB] Module Spec Dashboard

## What
Spec and plan the dashboard (console) using the team skills.

## Why
The console is a viewer; its scope must be small and clear before it is built.

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
Bhargav

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-20

## Steps
1. Read `docs/specs/GkmkbSpec.md` sections 5 and 6, ADR 0004 and ADR 0008, and the existing tickets `DashboardShell`, `DashboardViews`. Look at the SENTINEL mock prompts in Ayush's Downloads folder for visual ideas (ask Ayush to share them).
2. Run `/grill-with-docs` on "What does the analyst need to see in the console?". Keep it to alerts, detections, session timeline, rules approve/reject, baseline.
3. Run `/to-spec` and save as `docs/specs/DashboardSpec.md`.
4. Review with Ayush.
5. Run `/to-tickets`. Replace the existing dashboard tickets instead of duplicating.
6. Open the PR.

Expected output: `docs/specs/DashboardSpec.md` and tickets with Steps, owner Bhargav.
