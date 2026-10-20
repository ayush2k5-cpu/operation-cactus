# ADR 0008 — Product form: detection middleware with a thin web console

Status: Accepted 2026-10-20 (Ayush)
Date: 2026-10-20

## Context
The brief reads like a web app. The novelty (CoverTrace, gate, closed loop) is detection, and the demo is replay-based.

## Decision
The product is a headless detection engine with a CLI (`gkmkb replay <pcap>`). The FastAPI backend wraps the engine; the React dashboard is a viewer over REST and WebSocket. The engine never imports the dashboard or the web framework.

## Consequences
- The demo works from the CLI if the UI breaks.
- `eval/` calls the same engine code as the demo.
- Modules stay independent; the dashboard is replaceable.
- A live sensor can replace `ReplaySource` later without changing the product shape.
- Rejected: pure web app (UI becomes the work), desktop tool (no deception loop), research-only notebooks (weak capstone demo).
