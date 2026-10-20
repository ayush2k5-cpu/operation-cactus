# [GKMKB] Honeypot container with session recording

## What
Build one emulated service (SSH-like or HTTP) in Docker that records every command and payload as session events; mimicnet.engage(alert) starts and stops it.

## Why
Core of the response layer.

## Acceptance Criteria
- [ ] engage returns HoneypotSession with events after a scripted attacker run
- [ ] Container isolated, no host mounts, resource limited
- [ ] Only one container at a time
- [ ] Tests mark Docker requirement

## Blockers
SharedContracts, ComposeStack

## Agent
Claude Code

## Owner
Open

## Cycle
3

## Created
2026-10-18 (revised 2026-10-20)
