# Onboarding: read this first

You are joining a four-person final-year project. This page tells you exactly what to do and what not to do. If anything here is unclear, ask Ayush before you start, not after you break something.

## 1. What we are building
A detection engine that replays network traffic, spots data hidden in DNS and ping traffic with two independent detectors (FlowSight and CoverTrace), raises an alert only when both agree, traps the attacker in a fake honeypot, and learns new detection rules from what it saw. A small web console shows it live. All traffic is crafted or from public datasets. Nothing touches real people's traffic.

## 2. Your role and first ticket

| Person | Module | First ticket |
|---|---|---|
| Shivansh | CoverTrace and MimicNet | #46 CoverTrace entry point and settings |
| Bhargav | FlowSight | #51 FlowSight entry point, window state and episodes |
| Sharukh | Evaluation and MITRE | #81 pcap labels and the hard benign set, and #83 record team consent for captures |
| Ayush | Lead, backend, dashboard | all shared files and every merge to `main` |

Find all your tickets with the label `owner:<your name>` in the GitHub Issues tab.

## 3. Day 1 checklist
1. Accept the repo invite (email, or https://github.com/notifications).
2. Clone and run setup. Windows, in PowerShell:
   ```powershell
   git clone https://github.com/ayush2k5-cpu/operation-cactus.git
   cd operation-cactus
   Set-ExecutionPolicy -Scope Process Bypass
   .\scripts\setup.ps1
   ```
   macOS or Linux: `bash scripts/setup.sh`. It takes a few minutes. It installs what is missing, creates `.venv`, and runs the tests. At the end it must say `46 passed` or more.
3. Do what the script's `[todo]` lines say. Usually that is your git name and email:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   gh auth login
   ```
4. Install the shared AI skills once: follow `docs/WorkflowSetup.md` section 3.
5. Tell Ayush: your operating system, which AI tool you use, and anything in steps 1 to 4 that failed (paste the exact error line).
6. Read `GLOSSARY.md` (ten minutes). We use those words exactly.

## 4. Your daily loop
```
pick a ticket -> start it -> build -> submit -> merge into your module branch
```
1. **Pick** an open issue with your `owner:` label. Read all of it.
2. **Start:** `python scripts/ticket.py start <issue number>`. It makes your own branch from your module branch.
3. **Build** with your AI tool, one step at a time. Tell it: "Work only on this ticket and follow AGENTS.md." Commit small and often with messages like `feat: add subdomain entropy function`.
4. **Check your own diff.** You must be able to explain every line to the panel. If you cannot, ask your AI tool to simplify it.
5. **Submit:** `python scripts/ticket.py submit <issue number>`. It runs the checks and opens a pull request (PR) into your module branch.
6. **Merge:** when the checks are green, click merge on your PR (a normal merge commit). Do not delete the branch.
7. Ayush merges your module branch into `main` later. The issue closes then.

Not sure what a command will do? Add `--dry-run` to `ticket.py` and it only tells you.

## 5. The branch map
```
main                  only Ayush merges here
 mod/covertrace       one long branch per module
 mod/flowsight
 mod/mimicnet
 mod/backend
 mod/eval
   covertrace/shivansh-<ticket>   your short ticket branch, made by ticket.py
```
You only ever work on your ticket branch. You only ever merge into your module branch.

## 6. DO
- Do work on a ticket branch made by `ticket.py start`.
- Do keep commits small and write the message in plain English.
- Do run the checks before you submit (`ticket.py submit` does it for you).
- Do write tests with your code. A change without a test is not finished.
- Do stay inside your module's folder.
- Do write down in your PR which capability changed (Designed, Partial or Working) in the Ledger box. Ayush records it.
- Do mark any placeholder code with `[stub]`.
- Do ask Ayush when something is unclear, and send the exact command and the exact error text.
- Do tell the truth in docs and slides: only claim what is merged and tested.

## 7. DON'T
- Don't work on `main` or on any `mod/` branch directly. Never push to them.
- Don't delete any branch, ever. Cleanup is done by Ayush when he asks.
- Don't use `git push --force` or `git reset --hard` or rewrite history.
- Don't merge your PR into `main`. Your PR goes into your module branch only.
- Don't edit the shared files: `GLOSSARY.md`, `docs/adr/`, `docs/specs/`, `docs/Ledger.md`, `docs/report/`, `contracts/`, `CONTRIBUTING.md`. If you need a change, say so in your PR and Ayush does it.
- Don't touch another module's folder without asking Ayush.
- Don't put AI tool names or "Co-Authored-By" lines in commits, PRs or code comments. Our git rules forbid it (`docs/rules/GitRules.md`). We disclose AI use once, in the report.
- Don't paste code you cannot explain.
- Don't commit secrets, passwords, tokens, the `.env` file, or big pcap files.
- Don't capture, test against or replay anyone's real traffic or systems. Lab pcaps and public datasets only. Captures on your own laptop need the written consent record (ticket #83) first.
- Don't ignore a red check. Fix it or ask.

## 8. When something goes wrong
- **A check failed (red):** read the first error line, fix it, commit, run `ticket.py submit` again. Still stuck after 30 minutes: ask Ayush.
- **You committed on the wrong branch or on `main` by mistake:** stop. Do not push. Tell Ayush what you ran. He will fix it.
- **You already pushed to `main` by mistake:** tell Ayush immediately. Do not try to undo it yourself.
- **Merge conflict:** stop and ask Ayush. Do not guess.
- **`ticket.py` says a module branch does not exist:** tell Ayush.
- **Your AI tool does something strange (edits many files, ignores the ticket):** stop it, run `git status`, and ask Ayush before committing anything.

## 9. Working with your AI tool
- Give it the whole ticket and tell it to follow `AGENTS.md`.
- Tickets with numbered `## Steps`: do them one at a time and check each result.
- Unclear ticket? Run the grilling skill (`/grill-with-docs`) and answer its questions. It may suggest glossary or decision changes: put them in your PR text, do not edit the shared files.
- The spec and ticket skills (`/to-spec`, `/to-tickets`) are Ayush's.

## 10. Where things live
- Your tickets: GitHub Issues, label `owner:<name>`.
- What to build: `docs/specs/<Module>Spec.md` for your module.
- Shared words: `GLOSSARY.md`. Big decisions: `docs/adr/`.
- What is really done: `docs/Ledger.md`.
- Rules for agents: `AGENTS.md`. Git rules: `docs/rules/GitRules.md`.

## 11. Quick card
```
python scripts/ticket.py start <n>      begin a ticket
python scripts/ticket.py submit <n>     checks, push, open the PR
git status                              what changed, which branch am I on
git branch --show-current               my branch name
```
Never on main. Never delete. Never force. Never edit the shared files. When in doubt, ask Ayush.
