# ADR 0009 — FlowSight judges per-Entity windows from metadata only

Status: Accepted 2026-10-22 (Ayush)
Date: 2026-10-22

## Context
A DNS tunnel can be one long single-port flow or many one-packet flows (a new source port per query). Per-flow statistics cannot see the second shape. FlowSight must also stay independent of CoverTrace (ADR 0002).

## Decision
FlowSight keeps a sliding Window per Entity (default 60 seconds) and pools the packets of every flow of that Entity inside it. It uses only packet sizes and gaps; it never reads DNS queries, ICMP times or HTTP header names. It emits at most one Detection per Entity per Episode, and only after the Window holds at least 20 packets. A rule-based scorer comes first and replaces the stub; a logistic regression trained on windows from real tool-generated captures replaces it later.

## Consequences
- Works on encrypted traffic and on both tunnel shapes.
- Features are computed over the pooled Window, not per flow, so the replay path and the training path must build windows the same way.
- Training and test data are split by capture, never by window.
