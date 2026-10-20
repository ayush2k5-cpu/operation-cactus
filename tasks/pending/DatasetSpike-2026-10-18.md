# [GKMKB] Dataset spike for FlowSight and report

## What
Pick the public flow dataset (CIC-IDS2017 or alternative), check licence, size and feature mapping to the 4 flow features; write data/README.md and a download script.

## Why
Panel will ask for provenance; training needs real data.

## Acceptance Criteria
- [ ] data/README.md lists dataset, licence, citation, size
- [ ] scripts/fetch_data script works and is gitignored for big files
- [ ] Feature mapping to flow_avg_pkt_size_log, flow_pkt_size_variance, flow_iat_mean_ms, flow_burst_ratio documented
- [ ] Recommendation written, Ayush confirms D8

## Blockers
None

## Agent
Unassigned

## Owner
Sharukh

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-18 (revised 2026-10-20)

## Steps
1. List candidate public flow datasets (CIC-IDS2017 first; add one or two alternatives for DNS tunneling, e.g. CIC-Bell-DNS-EXF-2021).
2. For each: licence, size, download link, citation, which attacks it contains, and whether it has flows or pcaps.
3. Map available columns to the four FlowSight features (`flow_avg_pkt_size_log`, `flow_pkt_size_variance`, `flow_iat_mean_ms`, `flow_burst_ratio`). Mark each feature as direct, derivable or missing.
4. Write `data/README.md` rows for every dataset considered and a recommendation with reasons.
5. Do not download anything over 1 GB without asking Ayush.
6. Open a PR with the doc. Ayush confirms decision D8.
