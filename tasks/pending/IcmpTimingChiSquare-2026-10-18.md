# [GKMKB] CoverTrace ICMP timing chi-square

## What
Chi-square goodness-of-fit of ICMP inter-packet delays against an expected distribution; emit Detection.

## Why
Covert timing channel indicator from Paper 1.

## Acceptance Criteria
- [ ] Chi2 statistic matches scipy on fixtures
- [ ] Flags a synthetic timing-channel pcap, not normal ping
- [ ] Documented expected-distribution assumption

## Blockers
SharedContracts

## Agent
Claude Code

## Owner
Shivansh

## Cycle
2

## Created
2026-10-18 (revised 2026-10-20)
