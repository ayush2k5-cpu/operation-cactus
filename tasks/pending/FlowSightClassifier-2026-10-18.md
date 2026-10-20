# [GKMKB] FlowSight classifier train and infer

## What
Train a classifier on the chosen dataset using the 4 features, save model, expose flowsight.analyze(flow) -> Detection | None with score.

## Why
Gives the gate its behavioral signal.

## Acceptance Criteria
- [ ] Training script reproducible with fixed seed
- [ ] analyze returns Detection with score and threshold_used
- [ ] Metrics (precision, recall, F1, AUC) saved under eval/
- [ ] Stub version (fixed rule) merged first so the skeleton runs

## Blockers
FlowSightFeatures, DatasetSpike

## Agent
Claude Code

## Owner
Open

## Cycle
2

## Created
2026-10-18 (revised 2026-10-20)
