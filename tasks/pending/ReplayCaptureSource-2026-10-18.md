# [GKMKB] Replay capture source (pcap to FlowRecord)

## What
Implement ReplaySource using scapy or dpkt: group packets into flows, fill FlowRecord including dns_queries, icmp_ts and http_header_names.

## Why
Single traffic source for the demo (ADR 0001).

## Acceptance Criteria
- [ ] ReplaySource(path).flows() yields valid FlowRecords
- [ ] Small test pcaps in data/test/ with expected FlowRecords
- [ ] Handles empty and truncated pcaps without crashing
- [ ] Throughput noted (packets per second) in the PR

## Blockers
SharedContracts

## Agent
Claude Code

## Owner
Ayush

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-18 (revised 2026-10-20)

## Steps
1. Create `capture/source.py` with a `CaptureSource` protocol: `flows() -> Iterator[FlowRecord]`.
2. Create `capture/replay.py` with `ReplaySource(path)`. Read the pcap with scapy `PcapReader` (streaming). Group packets into flows by 5-tuple with direction normalized; close a flow after 60 s idle.
3. Fill `pkt_sizes`, `iat_ms`, `pkt_count`, `byte_count`, `start_ts`, `end_ts`.
4. Extract DNS queries (`dns_queries`) and ICMP timestamps (`icmp_ts`). Leave `http_header_names` empty with a TODO ticket reference (Cycle 2).
5. Handle empty and truncated pcaps without crashing; log and skip bad packets.
6. Write tests that build tiny pcaps with scapy `wrpcap` into `tmp_path` (benign DNS, tunnel-like DNS, ICMP) and assert the FlowRecords.
7. Note packets per second on a 5 MB pcap in the PR.

Expected output: `ReplaySource("x.pcap").flows()` yields valid `FlowRecord`s; tests pass.
