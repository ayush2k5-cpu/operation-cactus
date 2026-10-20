# Domain Docs

Single-context repo. How skills and agents consume the domain documentation.

## Before exploring, read these
- `GLOSSARY.md` at the repo root.
- `docs/adr/`: read the ADRs that touch the area you are about to work in.
- `docs/specs/GkmkbSpec.md` and `docs/Architecture.md`.

If a file is missing, proceed silently.

## Use the glossary's vocabulary
Use terms exactly as in `GLOSSARY.md` (Detection, Alert, Entity, Gate, Engine, Console) in ticket titles, tests, commits and PRs. Do not drift to synonyms. If a needed concept is missing, note it for `/domain-modeling` instead of inventing a word.

## Flag ADR conflicts
If your output contradicts an ADR, say so explicitly:

> _Contradicts ADR 0002 (independent detectors), but worth reopening because…_

## Layout
```
GLOSSARY.md
docs/adr/        ← numbered decisions (0001-...)
docs/specs/      ← GkmkbSpec.md
docs/agents/     ← this folder: tracker and domain config for skills
```
