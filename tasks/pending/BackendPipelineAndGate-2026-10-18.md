# [GKMKB] Backend pipeline and correlation gate

## What
FastAPI app wiring ReplaySource, both detectors, the gate (ADR 0003) and Mongo persistence; expose REST endpoints from the spec. Use stub detectors until real ones land.

## Why
Walking skeleton spine; everything plugs in here.

## Acceptance Criteria
- [ ] POST /api/replay runs a pcap end to end
- [ ] Gate unit tests: both signals escalate, single does not, window expiry
- [ ] Detections and Alerts persisted
- [ ] OpenAPI matches contracts

## Blockers
SharedContracts, ComposeStack, ReplayCaptureSource

## Agent
Claude Code

## Owner
Ayush

## Cycle
2

## Created
2026-10-18 (revised 2026-10-20)
