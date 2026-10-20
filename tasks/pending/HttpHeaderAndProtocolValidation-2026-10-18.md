# [GKMKB] CoverTrace HTTP header anomaly and protocol validation

## What
Score unusual HTTP header sets and malformed DNS/ICMP structure; emit Detection.

## Why
Completes the 4 CoverTrace indicators.

## Acceptance Criteria
- [ ] http_header_anomaly_score and protocol_struct_deviation defined in docs
- [ ] Fixtures: benign, header-stego, malformed DNS
- [ ] Scores in 0 to 1

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
