# [GKMKB] CoverTrace evaluation harness

## What
Script computing precision, recall, F1, ROC/AUC, false-positive rate on lab pcaps, static vs adaptive, and the Paper 1 synthetic baseline.

## Why
Every number in the report must come from here.

## Acceptance Criteria
- [ ] python -m eval.covertrace prints a metrics table
- [ ] Seeded and reproducible
- [ ] Results saved as CSV and ROC plot
- [ ] Limitations section drafted

## Blockers
DnsEntropyDetector, DnsTunnelLabPcaps

## Agent
Claude Code

## Owner
Sharukh

## Cycle
2

## Created
2026-10-18 (revised 2026-10-20)
