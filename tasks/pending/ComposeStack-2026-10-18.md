# [GKMKB] Docker compose stack (Mongo + backend)

## What
Add docker-compose.yml with mongo and backend services, healthchecks, .env.example wiring.

## Why
One command brings up storage for every teammate.

## Acceptance Criteria
- [ ] docker compose up -d gives healthy mongo
- [ ] Backend container starts and reports /health
- [ ] Teardown script leaves no orphan volumes unless asked

## Blockers
RepoSkeletonAndCi

## Agent
Claude Code

## Owner
Ayush

## Cycle
2

## Created
2026-10-18 (revised 2026-10-20)
