"""Teammate helper: start a ticket on the right branch and submit it as a PR.

  python scripts/ticket.py start <issue>     makes <module>/<owner>-<title> from mod/<module>
  python scripts/ticket.py submit <issue>    runs the checks, pushes, opens a PR into mod/<module>

The module comes from the issue's `module:` label, the owner from its `owner:` label.
Only needs git, the gh CLI and Python. Run `gh auth login` once first.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES = {
    "covertrace": "covertrace",
    "flowsight-capture": "flowsight",
    "mimicnet": "mimicnet",
    "backend-console": "backend",
    "data-eval": "eval",
}


def module_of(labels: list[str]) -> str | None:
    """Short module name from the module: label, or None (work goes straight to main)."""
    for name in labels:
        if name.startswith("module:"):
            return MODULES.get(name.split(":", 1)[1])
    return None


def owner_of(labels: list[str]) -> str:
    for name in labels:
        if name.startswith("owner:"):
            return name.split(":", 1)[1]
    return "dev"


def slug(title: str, limit: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:limit].strip("-")


def branch_name(module: str | None, owner: str, title: str) -> str:
    prefix = module or "work"
    return f"{prefix}/{owner}-{slug(title)}"


def base_branch(module: str | None) -> str:
    return f"mod/{module}" if module else "main"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if check and result.returncode:
        sys.exit(
            f"command failed: {' '.join(cmd)}\n{result.stderr.strip() or result.stdout.strip()}"
        )
    return result


def load_issue(number: str) -> dict:
    out = run(["gh", "issue", "view", number, "--json", "number,title,labels,state"]).stdout
    issue = json.loads(out)
    issue["label_names"] = [lab["name"] for lab in issue["labels"]]
    return issue


def python_exe() -> str:
    for rel in (".venv/Scripts/python.exe", ".venv/bin/python"):
        if (ROOT / rel).exists():
            return str(ROOT / rel)
    return sys.executable


def start(number: str, dry_run: bool = False) -> None:
    issue = load_issue(number)
    module = module_of(issue["label_names"])
    base = base_branch(module)
    branch = branch_name(module, owner_of(issue["label_names"]), issue["title"])
    if dry_run:
        print(
            f"[dry run] would create {branch} from origin/{base} and comment 'taking this' on #{number}"
        )
        return
    run(["git", "fetch", "origin", "--quiet"])
    if run(["git", "rev-parse", "--verify", f"origin/{base}"], check=False).returncode:
        sys.exit(f"origin/{base} does not exist yet. Ask Ayush to create it.")
    run(["git", "checkout", "-b", branch, f"origin/{base}"])
    run(["gh", "issue", "comment", number, "--body", "taking this"], check=False)
    print(f"On branch {branch}, cut from {base}.")
    print("Build the ticket, commit small, then run: python scripts/ticket.py submit " + number)


def submit(number: str, dry_run: bool = False) -> None:
    issue = load_issue(number)
    module = module_of(issue["label_names"])
    base = base_branch(module)
    if dry_run:
        print(
            f"[dry run] would run ruff, ruff format check and pytest, push, and open a PR into {base} for #{number}"
        )
        return
    branch = run(["git", "branch", "--show-current"]).stdout.strip()
    if branch in ("main", "") or branch.startswith("mod/"):
        sys.exit(f"You are on '{branch}'. Switch to your ticket branch first.")
    if run(["git", "status", "--porcelain"]).stdout.strip():
        sys.exit("You have uncommitted changes. Commit them first.")
    py = python_exe()
    for cmd in (
        [py, "-m", "ruff", "check", "."],
        [py, "-m", "ruff", "format", "--check", "."],
        [py, "-m", "pytest", "-q"],
    ):
        print("running:", " ".join(Path(c).name if i == 0 else c for i, c in enumerate(cmd)))
        result = run(cmd, check=False)
        if result.returncode:
            sys.exit(
                (result.stdout + result.stderr).strip()[-1500:]
                + "\nChecks failed. Fix, commit, run submit again."
            )
    run(["git", "push", "-u", "origin", branch])
    body = (
        f"Closes #{number}\n\n"
        "## What changed\n\n"
        "## Ledger\nState change for Ayush to record (Designed, Partial or Working), or none:\n"
    )
    out = run(
        [
            "gh",
            "pr",
            "create",
            "--base",
            base,
            "--head",
            branch,
            "--title",
            issue["title"],
            "--body",
            body,
        ]
    )
    print(out.stdout.strip())
    if base == "main":
        print(
            "PR opened into main. Ayush merges it. Do not merge it yourself. Do not delete the branch."
        )
    else:
        print(
            f"PR opened into {base}. Merge it yourself once CI is green. Do not delete the branch."
        )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("start", "submit"):
        p = sub.add_parser(name)
        p.add_argument("issue")
        p.add_argument(
            "--dry-run", action="store_true", help="show what would happen, change nothing"
        )
    args = parser.parse_args(argv)
    {"start": start, "submit": submit}[args.command](args.issue.lstrip("#"), args.dry_run)


if __name__ == "__main__":
    main()
