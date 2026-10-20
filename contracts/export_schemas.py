"""Write one JSON Schema file per contract into contracts/schemas/.

Run from the repo root: python -m contracts.export_schemas
"""

import json
from pathlib import Path

from contracts.models import ALL_MODELS

OUT = Path(__file__).parent / "schemas"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for name, model in ALL_MODELS.items():
        path = OUT / f"{name}.schema.json"
        path.write_text(json.dumps(model.model_json_schema(), indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
