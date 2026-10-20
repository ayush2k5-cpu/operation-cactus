# ADR 0002 — FlowSight and CoverTrace are independent in-process libraries

Status: Accepted 2026-10-20 (Ayush)
Date: 2026-10-18

## Context
Paper 1 benchmarks one fused 8-feature classifier. The Phase-II gate needs two signals that can disagree.

## Decision
Each detector exposes `analyze(flow) -> Detection | None` and owns its own score. The backend imports them in-process. The Paper 1 fused classifier stays in `eval/` as a baseline to compare against, not as the runtime path.

## Consequences
Independent scores make the gate meaningful (corroboration, not one model). In-process calls avoid inter-service plumbing on a single host. Detectors stay testable with plain pytest.

## Addendum 2026-10-20
Report wording: Paper 1 benchmarked a fused 8-feature classifier on synthetic data. Phase II splits the features into two independent detectors plus a gate and evaluates on lab pcaps. The fused model stays in `eval/` as the comparison baseline.
