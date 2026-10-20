# [GKMKB] CoverTrace DNS subdomain entropy

## What
Shannon entropy of subdomain labels per entity over a sliding window, plus query-rate and label-length checks; emit Detection above threshold.

## Why
Core of the headline demo and Paper 1.

## Acceptance Criteria
- [ ] entropy(label) matches hand-checked values
- [ ] Detector flags a lab tunnel pcap and not benign DNS fixtures
- [ ] Detection.features includes entropy, query_count, mean_label_len
- [ ] Static threshold first, configurable

## Blockers
SharedContracts, ReplayCaptureSource

## Agent
Claude Code

## Owner
Shivansh

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-18 (revised 2026-10-20)

## Steps
1. Read `GLOSSARY.md`, `docs/specs/GkmkbSpec.md` section 4 and `contracts/models.py` (Detection, FlowRecord).
2. Create `covertrace/entropy.py` with `shannon_entropy(text) -> float` (bits per character). Tests: `"aaaa"` is 0.0, `"ab"` is 1.0, a 32-char random base32 string is above 3.5.
3. Create `covertrace/dns.py` with a class `DnsEntropyDetector(config)`. It keeps in-memory state per entity `(src_ip, dst_ip)`: a sliding window (default 60 s) of subdomain labels from `flow.dns_queries`. Each tunnel query is its own flow, so the detector must aggregate across flows.
4. `analyze(flow) -> Detection | None`: compute mean label entropy, query count and mean label length for the entity window. Return a `Detection` (`source="covertrace"`) when mean entropy is above the threshold (default 3.5 bits) and the query count is at least 20. Put thresholds in a config dataclass, not constants. `features` holds `entropy`, `query_count`, `mean_label_len`; `threshold_used` is set.
5. Score in 0 to 1: scale entropy above the threshold toward 1.
6. Tests: benign domains stay below threshold; synthetic tunnel queries trigger; fewer than 20 queries do not trigger.
7. When Bhargav's `data/demo/dns_tunnel_plus_benign.pcap` lands, add a test that runs `ReplaySource` through the detector and expects a Detection for the tunnel source IP only. Skip the test if the file is missing.

Expected output: tests pass; detector flags the tunnel entity and not the benign one.
