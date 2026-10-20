# GKMKB — Architecture

Single host. Decisions: see `docs/adr/`. Shapes: see `docs/specs/GkmkbSpec.md` section 4.

```
pcap (replay)
  |
ReplaySource  (capture/)            -> FlowRecord stream
  |
  +--> FlowSight.analyze   (flowsight/)   -> Detection
  +--> CoverTrace.analyze  (covertrace/)  -> Detection   <-- Baseline (adaptive thresholds)
          |
      Gate (backend/)  same entity + window + both >= threshold
          |
        Alert --> Mongo (detections, alerts)
          |
      MimicNet.engage (mimicnet/, Docker honeypot) -> HoneypotSession (+ MITRE)
          |
      MimicNet.rules_from -> Rule(proposed) --analyst approves--> Rule(active)
          |                                                          |
          +----------------------------------------------------------+--> loaded by FlowSight / CoverTrace
          |
  FastAPI REST + WebSocket /ws/events  -->  React dashboard
```

## Repo layout
```
capture/     M2  pcap to FlowRecord
flowsight/   M2  flow features + classifier
covertrace/  M1  entropy, chi-square, protocol checks, baseline
mimicnet/    M3  honeypot, MITRE map, banner variation, rule generation
backend/     M4  FastAPI, gate, persistence, WebSocket
dashboard/   M4  React + Recharts
contracts/   M4  pydantic models + JSON schemas + fixtures (shared, change by PR with all owners reviewing)
eval/        M4  metric scripts, Paper 1 baseline
data/            pcaps and datasets (large files gitignored)
scripts/         setup, demo
(tickets live in GitHub Issues)
```

## Boundary rules
- Modules import only from `contracts/`, never from each other. The backend is the only place that wires modules together.
- A contracts change needs a PR approved by every module owner.
- Each module has its own tests under its folder and must pass without Docker, except `mimicnet/` Docker tests.
