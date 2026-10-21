"""Lead-only helper: open the PR that merges a module branch into main.

  python scripts/release.py <module>

Lists the ticket PRs merged into mod/<module> since the last release and writes a
`Closes #N` line for each ticket, so the issues close when you merge to main.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(f"command failed: {' '.join(cmd)}\n{r.stderr.strip()}")
    return r.stdout.strip()


def merged_pr_numbers(log: str) -> list[int]:
    return [int(n) for n in re.findall(r"Merge pull request #(\d+)", log)]


def closes_in(body: str) -> list[int]:
    return [int(n) for n in re.findall(r"[Cc]loses #(\d+)", body or "")]


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/release.py <module>")
    module = sys.argv[1]
    branch = f"mod/{module}"
    run(["git", "fetch", "origin", "--quiet"])
    log = run(["git", "log", f"origin/main..origin/{branch}", "--merges", "--format=%s"])
    prs = merged_pr_numbers(log)
    if not prs:
        sys.exit(f"Nothing to release: {branch} has no merged ticket PRs ahead of main.")
    lines, closes = [], []
    for number in sorted(prs):
        info = json.loads(run(["gh", "pr", "view", str(number), "--json", "title,body"]))
        lines.append(f"- #{number} {info['title']}")
        closes += closes_in(info["body"])
    body = (
        f"Release of {branch} into main.\n\n## Ticket PRs\n"
        + "\n".join(lines)
        + "\n\n"
        + "\n".join(f"Closes #{n}" for n in sorted(set(closes)))
        + "\n\n## Before merging\n- [ ] CI green\n- [ ] Ledger, glossary and spec updated for the state changes noted in the ticket PRs\n"
    )
    print(
        run(
            [
                "gh",
                "pr",
                "create",
                "--base",
                "main",
                "--head",
                branch,
                "--title",
                f"Release {module} to main",
                "--body",
                body,
            ]
        )
    )


if __name__ == "__main__":
    main()
