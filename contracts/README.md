# contracts

Shared data types for every module. Source of truth is `docs/specs/GkmkbSpec.md` section 4; the code here must match it.

- `models.py`: pydantic v2 models `FlowRecord`, `Detection`, `Alert`, `HoneypotSession`, `Rule` (plus `Entity`, `DnsQuery`, `SessionEvent`, `MitreTag`). Unknown fields are rejected. Timestamps must be timezone-aware.
- `schemas/`: JSON Schema per model. Regenerate with `python -m contracts.export_schemas`.
- `fixtures/`: one valid and one invalid JSON file per model. Reuse them in your module tests.
- `test_contracts.py`: validation tests.

## Notes
- An `Alert` needs at least two `detection_ids` (one FlowSight, one CoverTrace). The gate is the only producer.
- `Detection.score` is 0 to 1. `threshold_used` is whatever threshold the detector applied, in the detector's own unit.

## Change policy
Modules import types from `contracts.models` only. A change to this folder needs a PR approved by every module owner. When you change a model, update the spec section, the fixtures, and re-run the schema export in the same PR.
