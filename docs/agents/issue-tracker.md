# Issue tracker: Local Markdown in `tasks/`

Tickets for this repo are markdown files in `tasks/`. GitHub Issues are not used. Skills that say "publish to the issue tracker" write here.

## Conventions

- State is the folder: `tasks/pending/` → `tasks/in-progress/` → `tasks/done/` (or `tasks/failed/` with the reason appended).
- File name: `PascalCaseTitle-YYYY-MM-DD.md` (creation date).
- One ticket per file. Never a combined tickets file.
- Format (headings in this order): `# [GKMKB] Title`, `## What`, `## Why`, `## Acceptance Criteria` (checkboxes), `## Blockers`, `## Agent`, `## Owner`, `## Cycle`, `## Created`. Optional `## Steps` for tickets handed to people who follow instructions.
- Blocking: list ticket names under `## Blockers`. A ticket is unblocked when each listed ticket is in `tasks/done/`.
- Comments and conversation append to the bottom under `## Comments`.
- Cycle (1 to 5) is defined in `docs/specs/GkmkbSpec.md` section 9. The index is `tasks/README.md`.

## When a skill says "publish to the issue tracker"
Create a new file in `tasks/pending/` using the format above. Do not use `.scratch/`. Specs live in `docs/specs/`, not in the ticket folders.

## When a skill says "fetch the relevant ticket"
Read the file at the path or name the user gives. Search all four state folders.

## Claiming and finishing
- Claim: set `## Owner` to your name and move the file to `tasks/in-progress/` in your first commit.
- Finish: move to `tasks/done/` in the merge PR.
