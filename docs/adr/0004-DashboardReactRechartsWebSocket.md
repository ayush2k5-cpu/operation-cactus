# ADR 0004 — Dashboard: React + Recharts over WebSocket

Status: Proposed (Ayush to accept or change)
Date: 2026-10-18

## Context
D3 is powerful but slow to build; polling feels dead in a demo.

## Decision
Vite + React + Recharts. FastAPI WebSocket `/ws/events` pushes events. D3 only for one custom view if time remains. The SENTINEL tactical mock prompts are a visual reference, not a requirement.

## Consequences
Fewer moving parts for students; live feel for the demo. Reversible: the REST API serves the same data.
