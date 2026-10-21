# ADR 0005 — MongoDB in docker compose

Status: Accepted 2026-10-22 (Ayush)
Date: 2026-10-18

## Context
Brief names MongoDB; documents (detections, sessions with nested events) fit it.

## Decision
Single `mongo` container via docker compose. Collections: detections, alerts, sessions, rules, baselines. Python access via pymongo (or motor). Tests use a throwaway DB name.

## Consequences
Keeps the brief's stack. Postgres would also work; switching later costs a data-layer rewrite only.
