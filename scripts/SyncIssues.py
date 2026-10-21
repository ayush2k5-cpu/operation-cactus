"""Mirror GitHub Issues into local tasks/ ticket files for the Ojas dispatcher.

GitHub Issues stay the source of truth. tasks/ is a generated, gitignored mirror.
Run from anywhere:  python scripts/SyncIssues.py [--repo owner/name]
Idempotent: existing ticket files are never overwritten; a closed issue moves its file to done/.
"""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"
STATES = ("pending", "in-progress", "done", "failed")
AGENTS = {"agent:claude": "Claude Code", "agent:agy": "Antigravity (agy)"}


def gh_issues(repo: str | None) -> list[dict]:
    cmd = [
        "gh",
        "issue",
        "list",
        "--state",
        "all",
        "--limit",
        "300",
        "--json",
        "number,title,body,state,labels,createdAt",
    ]
    if repo:
        cmd += ["--repo", repo]
    out = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", check=True, cwd=ROOT
    )
    return json.loads(out.stdout)


def section(body: str, name: str) -> str:
    m = re.search(rf"^## {name}\s*\n(.*?)(?=^## |\Z)", body, re.S | re.M)
    return m.group(1).strip() if m else ""


def pascal(text: str) -> str:
    return "".join(w[:1].upper() + w[1:] for w in re.findall(r"[A-Za-z0-9]+", text))


def find_existing(slug: str) -> tuple[str, Path] | None:
    for state in STATES:
        d = TASKS / state
        if d.is_dir():
            for f in d.glob(f"{slug}-*.md"):
                return state, f
    return None


def render(issue: dict, agent: str) -> str:
    body = issue["body"] or ""
    parts = [f"# [GKMKB] {issue['title']}", "", "## Issue", f"#{issue['number']}", ""]
    for name in ("What", "Why", "Acceptance Criteria", "Blockers", "Steps"):
        text = section(body, name)
        if text:
            parts += [f"## {name}", text, ""]
    parts += ["## Agent", agent, "", "## Created", issue["createdAt"][:10], ""]
    return "\n".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo")
    args = ap.parse_args()
    for state in STATES:
        (TASKS / state).mkdir(parents=True, exist_ok=True)
    made = moved = 0
    for issue in sorted(gh_issues(args.repo), key=lambda i: i["number"]):
        labels = {lab["name"] for lab in issue["labels"]}
        m = re.search(r"Ticket id:\*\*\s*`([^`]+)`", issue["body"] or "")
        slug = m.group(1) if m else pascal(issue["title"])
        existing = find_existing(slug)
        if issue["state"] == "CLOSED":
            if existing and existing[0] in ("pending", "in-progress"):
                shutil.move(existing[1], TASKS / "done" / existing[1].name)
                moved += 1
            continue
        if existing:
            continue
        agent = next((AGENTS[lab] for lab in labels if lab in AGENTS), "Claude Code")
        path = TASKS / "pending" / f"{slug}-{issue['createdAt'][:10]}.md"
        path.write_text(render(issue, agent), encoding="utf-8")
        made += 1
    print(f"created {made}, moved to done {moved}")


if __name__ == "__main__":
    main()
