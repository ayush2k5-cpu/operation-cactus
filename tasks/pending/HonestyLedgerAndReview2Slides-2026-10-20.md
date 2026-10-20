# [GKMKB] Honesty Ledger And Review2 Slides

## What
Turn spec section 8 into a status table with evidence links and build the Review 2 slides: what is done, partial, designed, next cycle.

## Why
Review 2 is a progress discussion; honest, evidenced status is the deliverable.

## Acceptance Criteria
- [ ] Ledger lists every capability with state and link to PR or file
- [ ] Slides: problem, architecture, what is done (CLI demo screenshot), what is next, team split
- [ ] Every 'done' claim has evidence; stubs are labelled stub
- [ ] Ayush reviews both before Oct 24

## Blockers
CliReplayAndStubGate (for the screenshot)

## Agent
Unassigned

## Owner
Sharukh (ledger) + Bhargav (slides)

## Cycle
1 (Review 2, 2026-10-24)

## Created
2026-10-20

## Steps
Sharukh:
1. Copy the table from `docs/specs/GkmkbSpec.md` section 8 into `docs/Ledger.md`. Add columns: evidence (PR or file link), date, owner.
2. On 2026-10-23, update every row to its true state (Designed, Partial, Working, Stub). A row is Working only if a merged PR and a passing test prove it.

Bhargav:
3. Create the slides from `docs/specs/GkmkbSpec.md` and `docs/Architecture.md`: problem, product form (middleware + CLI), architecture diagram, what is done (screenshot of `gkmkb replay`), what is partial or stub, cycles and cut line, team split, ethics.
4. Every "done" claim on a slide must match a row in the ledger.
5. Share the draft with Ayush on 2026-10-23 for review.

Expected output: `docs/Ledger.md` and a slide deck in which nothing is claimed beyond the ledger.
