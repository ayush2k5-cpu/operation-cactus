"""FlowSight module settings, read from environment variables.

Each setting has a safe default so FlowSight starts even when .env is missing
(FlowSightSpec § Implementation Decisions, US 17).

Other settings (window length, minimum packet count, score cut, rule
thresholds) will be added by the entry-point and scorer tickets.
"""

import os

FLOWSIGHT_BURST_LIMIT_MS: float = float(os.getenv("FLOWSIGHT_BURST_LIMIT_MS", "100.0"))
