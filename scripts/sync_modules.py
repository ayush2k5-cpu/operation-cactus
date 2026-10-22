"""Lead-only: merge main into every mod/* branch so module branches do not drift.

  python scripts/sync_modules.py            sync all module branches
  python scripts/sync_modules.py mimicnet   sync one

Run after each merge to main. A clean merge is pushed; a conflict is left alone and listed so you
can merge that branch by hand. Works on a detached HEAD, so it creates and deletes no branch. Needs admin bypass on the
mod/** ruleset (you have it).
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode:
        sys.exit(f"git {' '.join(args)} failed:\n{r.stderr.strip() or r.stdout.strip()}")
    return r


def main() -> None:
    if git("status", "--porcelain").stdout.strip():
        sys.exit("Working tree has changes. Commit or stash them first.")
    original = git("branch", "--show-current").stdout.strip() or "main"
    git("fetch", "origin", "--quiet")
    wanted = sys.argv[1:]
    refs = git(
        "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin/mod/"
    ).stdout.split()
    branches = [
        r.removeprefix("origin/") for r in refs if not wanted or r.rsplit("/", 1)[-1] in wanted
    ]
    done, conflicts, current = [], [], []
    for branch in branches:
        behind = git("rev-list", "--count", f"origin/{branch}..origin/main").stdout.strip()
        if behind == "0":
            current.append(branch)
            continue
        git("checkout", "-q", "--detach", f"origin/{branch}")
        merged = git("merge", "--no-edit", "origin/main", check=False)
        if merged.returncode:
            git("merge", "--abort", check=False)
            conflicts.append(branch)
            continue
        git("push", "origin", f"HEAD:refs/heads/{branch}")
        done.append(branch)
    git("checkout", "-q", original)
    print("synced:", ", ".join(done) or "none")
    print("already current:", ", ".join(current) or "none")
    if conflicts:
        print("CONFLICT, merge by hand:", ", ".join(conflicts))


if __name__ == "__main__":
    main()
