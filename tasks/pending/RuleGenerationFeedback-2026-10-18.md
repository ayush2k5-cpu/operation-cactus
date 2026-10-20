# [GKMKB] Closed-loop rule generation

## What
Implement mimicnet.rules_from(session) producing proposed Rules (IoC and threshold nudges) and detector-side loading of active rules.

## Why
Phase-II novelty 1 (ADR 0006).

## Acceptance Criteria
- [ ] Rules validate against contracts
- [ ] Approved rule changes detection on re-replay (test)
- [ ] Rejected rule has no effect
- [ ] Honesty ledger updated

## Blockers
HoneypotContainer, DnsEntropyDetector

## Agent
Claude Code

## Owner
Open

## Cycle
4

## Created
2026-10-18 (revised 2026-10-20)
