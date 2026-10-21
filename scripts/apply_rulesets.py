"""Lead-only: create or update the branch rulesets in .github/rulesets/ on GitHub.

  python scripts/apply_rulesets.py            apply
  python scripts/apply_rulesets.py --check    only validate the JSON files

Rulesets need a public repository (or GitHub Pro). Run once after the repo is public,
and again whenever a file changes. Safe to re-run: an existing ruleset with the same
name is updated.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = sorted((ROOT / ".github" / "rulesets").glob("*.json"))


def gh(args: list[str], payload: dict | None = None) -> str:
    cmd = ["gh", "api", *args]
    if payload is not None:
        cmd += ["--input", "-"]
    r = subprocess.run(
        cmd,
        cwd=ROOT,
        input=json.dumps(payload) if payload else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if r.returncode:
        sys.exit(f"gh api failed: {' '.join(args)}\n{r.stderr.strip()}")
    return r.stdout


def main() -> None:
    rulesets = [json.loads(f.read_text(encoding="utf-8")) for f in FILES]
    for f, rs in zip(FILES, rulesets, strict=True):
        assert rs["name"] and rs["rules"], f"{f.name}: needs a name and rules"
    if "--check" in sys.argv:
        print(f"{len(rulesets)} ruleset files are valid JSON")
        return
    slug = json.loads(gh(["repos/{owner}/{repo}"]))["full_name"]
    existing = {r["name"]: r["id"] for r in json.loads(gh([f"repos/{slug}/rulesets"]))}
    for rs in rulesets:
        if rs["name"] in existing:
            gh(["-X", "PUT", f"repos/{slug}/rulesets/{existing[rs['name']]}"], rs)
            print("updated:", rs["name"])
        else:
            gh(["-X", "POST", f"repos/{slug}/rulesets"], rs)
            print("created:", rs["name"])


if __name__ == "__main__":
    main()
