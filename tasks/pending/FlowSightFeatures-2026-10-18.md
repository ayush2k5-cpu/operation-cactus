# [GKMKB] FlowSight feature extraction

## What
Compute flow_avg_pkt_size_log, flow_pkt_size_variance, flow_iat_mean_ms, flow_burst_ratio from a FlowRecord.

## Why
Inputs to the FlowSight classifier; same feature names as Paper 1.

## Acceptance Criteria
- [ ] Pure function features(flow) -> dict
- [ ] Unit tests with hand-computed values
- [ ] Metadata only, no payload access

## Blockers
SharedContracts

## Agent
Claude Code

## Owner
Open

## Cycle
2

## Created
2026-10-18 (revised 2026-10-20)
