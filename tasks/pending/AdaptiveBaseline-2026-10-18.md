# [GKMKB] CoverTrace adaptive thresholds

## What
Maintain a rolling per-network Baseline and derive entropy/chi-square cutoffs from it; persist to baselines.

## Why
Phase-II novelty 3.

## Acceptance Criteria
- [ ] Window size and update frequency are config (default proposed in PR)
- [ ] Test: same traffic yields different cutoffs under two baselines
- [ ] Evaluation compares static vs adaptive false-positive rate

## Blockers
DnsEntropyDetector

## Agent
Claude Code

## Owner
Shivansh

## Cycle
4

## Created
2026-10-18 (revised 2026-10-20)
