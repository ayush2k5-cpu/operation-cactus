# ADR 0006 — Closed loop: automated extraction, analyst approval

Status: Proposed (Ayush to accept or change)
Date: 2026-10-18

## Context
Open item: manual vs automated rule conversion. Fully autonomous self-modifying detection is risky and hard to defend in a viva.

## Decision
`mimicnet.rules_from(session)` extracts a small fixed rule set: IoC rules (qname suffix, source IP, payload string) and threshold nudges. Rules are born `proposed`; an analyst approves in the dashboard before they become `active`. Detectors load active rules at start of each replay.

## Consequences
Demonstrable, bounded, safe. Honesty: label as Partial until evaluated; the claim is rule generation plus a measured detection delta, not general learning.

## Addendum 2026-10-22 (MimicNet grilling)
The first cut has two Rule kinds, both aimed at CoverTrace: a query-name suffix match and a source-address match. The "payload string" kind is out because no detector reads payload, and "threshold nudge" is out as cut-line depth. Every Rule is still born proposed and needs analyst approval. Active Rules reach CoverTrace through one call that sets its rule list; a matching flow gives a Rule hit (score 1.0).
