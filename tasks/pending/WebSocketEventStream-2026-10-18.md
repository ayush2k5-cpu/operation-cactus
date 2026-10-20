# [GKMKB] WebSocket event stream

## What
Add /ws/events broadcasting detection, alert, session_event and rule messages.

## Why
Live dashboard feel (ADR 0004).

## Acceptance Criteria
- [ ] Client receives events during a replay
- [ ] Reconnect-safe, no crash on disconnect
- [ ] Message schema documented

## Blockers
BackendPipelineAndGate

## Agent
Claude Code

## Owner
Ayush

## Cycle
2

## Created
2026-10-18 (revised 2026-10-20)
