# [GKMKB] Cli Replay And Stub Gate

## What
Add the `gkmkb` CLI with `replay <pcap>`: run ReplaySource, stub FlowSight (fixed rule), the real CoverTrace entry point and a stub gate (entity + 60 s window), and print detections and alerts.

## Why
The engine is the product; the CLI is the stable interface and the Review 2 demo.

## Acceptance Criteria
- [ ] `gkmkb replay data/demo/dns_tunnel_plus_benign.pcap` prints detections and one alert for the tunnel entity
- [ ] Control pcap prints zero alerts
- [ ] Stub parts print a `[stub]` tag so nothing is passed off as real
- [ ] Gate has unit tests for both-signals, single-signal and window expiry

## Blockers
SharedContracts, ReplayCaptureSource

## Agent
Claude Code

## Owner
Ayush

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-20

## Steps
1. Create the package `backend/gkmkb/` with `__init__.py`, `gate.py`, `stubs.py`, `pipeline.py`, `cli.py`. Register a `gkmkb` console script in `pyproject.toml`.
2. `gate.py`: `Gate(window_seconds=60, threshold=0.7)`. It stores Detections per entity and returns an `Alert` when a FlowSight and a CoverTrace Detection with score at or above threshold both exist in the window. One open Alert per entity.
3. `stubs.py`: `FlowSightStub.analyze(flow)` flags flows with small uniform packets and regular inter-arrival times. Tag every output `[stub]`.
4. `pipeline.py`: `run(pcap_path)` wires `ReplaySource`, `FlowSightStub`, `DnsEntropyDetector` and `Gate`, and returns detections and alerts. Use the real detector from `covertrace/` if it is merged; else a labelled stub.
5. `cli.py`: `gkmkb replay <pcap>` prints detections and alerts, with `[stub]` tags.
6. Tests for the gate: both signals raise one Alert, one signal raises none, a Detection outside the window does not count.
7. Run on `data/demo/dns_tunnel_plus_benign.pcap` and `single_signal_control.pcap`. Save a screenshot for the Review 2 slides.

Expected output: one Alert on the tunnel entity, zero on the control; stub parts clearly tagged.
