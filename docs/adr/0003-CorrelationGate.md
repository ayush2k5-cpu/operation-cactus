# ADR 0003 — Gate correlates on entity and time window

Status: Accepted 2026-10-22 (Ayush)
Date: 2026-10-18

## Context
Flow 5-tuples differ per DNS query (source port changes), so flow IDs cannot join the two detectors.

## Decision
Entity = `(src_ip, dst_ip)`. Gate raises an Alert when both a FlowSight and a CoverTrace Detection with `score >= threshold` exist for the same entity within a 60 s window (configurable). Single-signal Detections are stored, not escalated. One open Alert per entity until closed.

## Consequences
Simple, explainable, testable with fixtures. Window and thresholds go in config and in the evaluation (gate vs single detector false positives).
