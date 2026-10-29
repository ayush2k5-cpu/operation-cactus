"""Dump the backend OpenAPI description to dashboard/openapi.json."""

import json
import sys
from pathlib import Path

dashboard = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(dashboard.parent))

from backend.gkmkb.api import create_app  # noqa: E402
from backend.gkmkb.storage import MemoryStore  # noqa: E402

(dashboard / "openapi.json").write_text(
    json.dumps(create_app(MemoryStore()).openapi(), indent=2) + "\n", encoding="utf-8"
)
