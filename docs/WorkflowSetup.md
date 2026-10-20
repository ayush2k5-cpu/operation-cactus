# Workflow Setup — same AI workflow for every teammate

Goal: all four of us plan, build and review the same way, even though only Ayush has the Ojas system. You need nothing from Ojas. You need this repo, an AI coding tool and about 10 minutes.

## 1. What you need
- Repo cloned and `scripts/setup.ps1` (Windows) or `scripts/setup.sh` done (see `README.md`).
- One AI coding tool: **Claude Code** or **Antigravity** (both read `AGENTS.md`).
- Node.js (installed by the setup script).

## 2. Open the tool in the repo
Open the repo folder as your workspace.
- Claude Code: `cd fyp-untitled` then `claude`. `CLAUDE.md` imports `AGENTS.md`.
- Antigravity: open the folder. It reads `AGENTS.md`.

Check: ask the agent "What are the GKMKB glossary terms for a covert-channel verdict and the thing the gate raises?" It should answer Detection and Alert. If not, tell the agent to read `AGENTS.md` first.

## 3. Install the shared skills (once per machine)
The skills come from `mattpocock/skills` (MIT). Ayush reviewed the source at commit `49dd158d`. Install them in your own terminal, not through the agent:

```bash
npx skills add mattpocock/skills
```

When asked which skills to install, select only these seven:
- `grill-with-docs`
- `grilling`
- `domain-modeling`
- `to-spec`
- `to-tickets`
- `codebase-design`
- `pr`

Do **not** install: `setup-matt-pocock-skills` (config is already committed here), `triage`, `code-review` (clashes with Claude Code's built-in command), `git-guardrails-claude-code` (blocks `git push`).

Installed skills live on your machine (`.agents/` or `.claude/skills/`). They are gitignored. Never commit them.

Check in Claude Code: type `/` and look for `/grill-with-docs`. Antigravity: skill support depends on your version. If skills do not appear, the workflow still works. `AGENTS.md` carries the same rules in plain text. Tell Ayush which tool and version you use.

If the install fails, run `npx skills --help` and check Node is 20 or newer (`node -v`). Ask Ayush before trying other sources.

## 4. The loop (everyone)
Cycle 1 rule: hand the ticket's `## Steps` to your agent **one step at a time**. Then run `/grill-with-docs` → `/to-spec` → `/to-tickets` for your own next-cycle module (your `ModuleSpec...` ticket).

1. **Pick** a ticket in `tasks/pending/` for your name. Read the whole file.
2. **Claim**: set `## Owner` to your name, move the file to `tasks/in-progress/`, create the branch `dev/<name>-<ticket>`.
3. **Clarify** if anything is vague: run `/grill-with-docs` and answer its questions. It updates `GLOSSARY.md` or proposes an ADR when a decision settles. Commit those with your PR.
4. **Build** with your agent. Tell it: "Work only on this ticket, follow AGENTS.md, write tests first or with the code." Small steps.
5. **Check** locally: ruff, pytest (and the dashboard lint/build if you touched it). See `CONTRIBUTING.md`.
6. **Explain**: read your own diff. If you cannot explain a line, ask the agent to explain it or rewrite it simpler.
7. **PR**: run `/pr` to draft the body, fill `.github/PULL_REQUEST_TEMPLATE.md`, link the ticket, update the honesty ledger if a capability changed state (Designed, Partial, Working).
8. **Review**: another teammate reads the diff and runs the tests. Ayush reviews every PR in Cycle 1. Squash merge after green CI.
9. **Finish**: move the ticket to `tasks/done/` in the merge PR.

## 5. Role notes
**Coders (Ayush, Shivansh):** use `/to-spec` for a new feature, then `/to-tickets` to split it. New tickets go to `tasks/pending/` in the repo format. Use `/codebase-design` before changing a module boundary.

**Bhargav and Sharukh:** your tickets have numbered `## Steps`. Give the whole ticket to your agent and ask it to do the steps one at a time, showing you the result after each step. Do not skip the "expected output" line at the end of a ticket. If a step is unclear, run `/grill-with-docs` before guessing. Slides and report text must come from the honesty ledger, never from the plan.

## 6. Rules that apply to every skill and agent
- Use `GLOSSARY.md` terms exactly.
- Modules import only from `contracts/`.
- No real users' traffic. Pcaps are crafted or from public datasets.
- Follow `docs/rules/GitRules.md` (no AI attribution in commits, PRs or code comments).
- AI-written code is allowed. You must be able to explain it in the viva. The report discloses AI assistance.
- Mark stub code `[stub]`. Never claim a capability beyond what is merged and tested.

## 7. When something breaks
- Agent ignores the rules: tell it "Read AGENTS.md and your ticket first."
- Skill missing: use the plain rules in `AGENTS.md`.
- Merge conflict in `GLOSSARY.md`: keep both terms, ask Ayush if two definitions clash.
- Anything else: message Ayush with the command and the error text.
