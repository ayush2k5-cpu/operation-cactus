# [GKMKB] Report skeleton, ethics and datasets section

## What
Draft report outline mapping each claim to a Working capability, plus the ethics/legal and dataset provenance sections.

## Why
Report must match the code; fourth teammate can own it.

## Acceptance Criteria
- [ ] Outline links each claim to a PR or eval output
- [ ] Ethics section names datasets and lab consent
- [ ] Honesty ledger referenced

## Blockers
DatasetSpike, DnsTunnelLabPcaps

## Agent
Unassigned

## Owner
Sharukh

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-18 (revised 2026-10-20)

## Steps
1. Read `docs/specs/GkmkbSpec.md` sections 7 and 8.
2. Create `docs/report/ReportOutline.md` with chapters: problem, related work (from Paper 1), architecture, each module, evaluation, ethics, limitations, AI-assistance disclosure.
3. Under each chapter list the claim, the capability it needs and its state (Designed, Partial, Working). Link to the PR or eval output once it exists.
4. Draft the ethics section: lab data only, no real users' traffic, dataset provenance, consent for any team-captured traffic.
5. Draft one honest paragraph on AI-assisted development.
6. Open a PR.
