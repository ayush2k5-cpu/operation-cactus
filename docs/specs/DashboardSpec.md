# Dashboard Spec

Status: Draft, from the grilling on 2026-10-22 (issue #24). Vocabulary follows `GLOSSARY.md`. The dashboard is the Console. Respects ADR 0002 (modules are independent), ADR 0004 (React, Recharts, WebSocket) and ADR 0008 (the Engine plus CLI is the product, the Console is a viewer). It builds on the Backend Spec, which defines the API the Console talks to; the backend code is not built yet (tickets #63 to #67), so the Console is built against that spec.

## Problem Statement

The Engine works from the command line and, once the backend is built, saves results and pushes live events. But the team and the panel cannot see any of it without a terminal. An analyst cannot start a replay and watch Detections and Alerts appear. Past runs cannot be compared. An Alert cannot be closed from a screen. Later, the analyst also needs to see what the attacker did in the honeypot, approve or reject proposed Rules, and see that the adaptive threshold changes the cutoff on the same traffic. Today there is no place to do any of this, and the `dashboard/` folder is empty.

A viewer also has two honesty traps. The detectors emit a Detection only at a score of 0.5 or above, so benign flows never reach the Console, and the main spec's demo step "benign flows scoring low" cannot be shown. And the Baseline lives in CoverTrace memory only, so a "Baseline view" would have no data.

## Solution

A small web Console, a viewer over the backend. The analyst picks a lab pcap from a list, starts a replay, and watches Detections and Alerts appear live. Result counts (flows, Detections, Alerts) show when the replay finishes, so the control pcap visibly gives zero Alerts. The analyst can browse past replays, Detections and Alerts, and close an Alert. Later cycles add a honeypot session timeline with MITRE tags (from an Alert that has a session), Rule approve and reject, and a threshold compare view that puts two replays side by side. A page opened late reads history over REST first and then follows the live feed. If the backend is down, the Console says so in plain words. The CLI stays the fallback demo, so the Console is never required.

## User Stories

1. As an analyst, I want to pick a lab pcap from a list, so that I do not have to type or know file names.
2. As an analyst, I want to start a replay from the Console, so that I can run the demo without a terminal.
3. As an analyst, I want each Detection to appear while the replay runs, so that the demo feels live.
4. As an analyst, I want an Alert to appear the moment the Gate raises it, so that I see right away when both detectors agree.
5. As an analyst, I want each Detection to show its source, score, label, Entity and feature values, so that I can judge how strong the evidence is.
6. As an analyst, I want a Detection from CoverTrace to show which checker fired, so that I know why the machine was flagged.
7. As an analyst, I want a Rule hit to look different from a statistical Detection, so that I can tell the closed loop at work.
8. As an analyst, I want to see when a replay is finished, with flow, Detection and Alert counts, so that I know nothing more is coming.
9. As an analyst, I want the control pcap to show zero Alerts with its counts, so that the single-signal story is visible without showing benign flows.
10. As an analyst, I want a failed replay to show the reason, so that I do not wait for events that never arrive.
11. As an analyst, I want a clear message when a replay is already running, so that I understand why my request was refused.
12. As an analyst, I want a list of past replays with pcap name, start and end time, state and counts, so that I can find a run.
13. As an analyst, I want to open one past replay and see its Detections and Alerts, so that I can study one run at a time.
14. As an analyst, I want a list of Alerts, newest first, so that I see the latest first.
15. As an analyst, I want a list of Detections, newest first, including single-signal ones, so that I see what the Gate chose not to escalate.
16. As an analyst, I want to close an Alert from the list, so that the same machine can alert again later in the replay.
17. As an analyst, I want a clear answer when an Alert is already closed or no longer exists, so that I am not confused by silent success.
18. As an analyst, I want to open an Alert that has a session and see the honeypot session timeline, so that I learn what the attacker did.
19. As an analyst, I want session events in time order, with a live update while the session runs, so that I can follow it as it happens.
20. As an analyst, I want MITRE tags with the evidence line next to each tag, so that I can check why a tag was given.
21. As an analyst, I want behaviour with no tag to say "no tag", so that I am never shown a guessed technique.
22. As an analyst, I want the attacker address visible in the session, so that I can block it.
23. As an analyst, I want a list of Rules with status, target and source session, so that I know where each Rule came from.
24. As an analyst, I want approve and reject buttons only on proposed Rules, so that I cannot change a finished decision by mistake.
25. As an analyst, I want a Rule to show its new status after I act, so that I know my decision was saved.
26. As a demo presenter, I want to put two replays side by side with their CoverTrace thresholds and scores, so that I can show same traffic, two cutoffs.
27. As a demo presenter, I want the compare view labelled "from Detections", so that it never claims to be a Baseline curve.
28. As a demo presenter, I want clear empty states, so that a blank screen never looks like a bug.
29. As a demo presenter, I want a plain "backend is down" message, so that a failed start is understood at once.
30. As a demo presenter, I want the Console to keep working after the backend restarts, so that the demo can recover.
31. As a Console developer, I want to load history over REST and then follow the live feed, so that a page opened late still shows everything.
32. As a Console developer, I want duplicate Detections and Alerts dropped by ID, so that the same item never shows twice.
33. As a Console developer, I want the Console to read REST again after the WebSocket reconnects, so that nothing missed during the gap stays missing.
34. As a Console developer, I want a visible "reconnecting" banner when the socket drops, so that a stale screen is never trusted.
35. As a Console developer, I want one handler for every live message, based on the shared envelope, so that new message types need little work.
36. As a Console developer, I want API types generated from the backend OpenAPI description, so that the Console cannot drift from the contracts.
37. As a Console developer, I want a dev server that forwards API and WebSocket calls to the backend, so that I need no cross-origin setup.
38. As a Console developer, I want tests that run against a fake backend, so that I need no Docker or database.
39. As a Console developer, I want lint, tests and build to run in CI, so that a broken Console cannot merge.
40. As a team lead, I want the Console never to be required, so that the CLI demo still works if the Console breaks.
41. As a team lead, I want visual styling kept as a separate human ticket, so that taste work does not block the working views.
42. As a team lead, I want the visual polish to be first on the cut line, so that dropping it is expected, not a failure.
43. As a team lead, I want the ledger to keep the Dashboard at Designed until a view is merged and tested, so that the report claims only what exists.
44. As a security-minded reviewer, I want the Console to hold no secrets and no upload, so that nothing sensitive can leak through it.
45. As a security-minded reviewer, I want the Console to talk only to the local backend, so that a lab laptop is not exposed.
46. As a future maintainer, I want no Baseline curve until CoverTrace persists its Baseline, so that the view never shows data that does not exist.

## Implementation Decisions

- **Scope.** A viewer only (ADR 0008). No authentication, no upload, no live capture, no editing of detectors or settings. Owner is Ayush.
- **Views and cycles.** Cycle 2: replay start with live feed, Alerts with close, Detections, Replays history, error and empty states. Cycle 3: honeypot session timeline with MITRE tags. Cycle 4: Rules approve and reject, and the threshold compare view. Cycle 5: visual style, done by Ayush by hand (separate human ticket).
- **Technology.** Vite, React, TypeScript and Recharts (ADR 0004; D3 only for one custom view if time remains). The React and Recharts part of ADR 0004 is confirmed here.
- **Types.** API types are generated from the OpenAPI description of the backend, which the Backend Spec says matches the contracts. The WebSocket envelope (`type`, `replay_id`, `data`) is typed by hand because it is a backend shape, not a shared contract.
- **Start a replay.** The Console shows a dropdown of the pcaps in the data folder. This needs one small endpoint that lists the pcaps in the data folder, added to the backend replay API work (see Further Notes). The Console sends the chosen pcap name and gets back a `replay_id` at once.
- **Live feed.** One WebSocket connection, handled by one function that switches on message type. Built types are `detection`, `alert` and `replay_done`. `session_event` and `rule` are added when MimicNet exists. Unknown types are ignored, not fatal.
- **Late load and reconnect.** On page load the Console reads REST history first, then opens the WebSocket. It drops items it already has, by ID. After a reconnect it reads REST again. A banner shows while the socket is down.
- **Replay result instead of benign flows.** Detectors emit a Detection only at 0.5 or above and there is no flows endpoint, so benign flows never reach the Console. The Console shows replay counts (flows, Detections, Alerts). The control pcap shows zero Alerts. No flows endpoint is added.
- **Alerts and Detections.** Both list views show newest first, with an optional filter by replay. The Alert list has a close button. A Detection shows source, score, label, Entity and its feature map. A Rule hit (score 1.0, label made from the Rule id) is styled differently from a statistical Detection.
- **Session timeline.** Opened from an Alert that has a `session_id`, through the single-session endpoint. There is no sessions list. Events show in time order and update live through `session_event`. MITRE tags show with their evidence line. Behaviour with no tag shows "no tag".
- **Rules view.** Lists Rules with status, target, source session and match. Approve and reject buttons appear only on `proposed` Rules, call the API, and update the row from the response and from the live `rule` message.
- **Threshold compare (not a Baseline view).** The Baseline has no endpoint and stays in CoverTrace memory only, so there is no Baseline view in this spec. The compare view puts two replays side by side using `threshold_used` and the score of their CoverTrace Detections. It is labelled "from Detections". It covers demo step 7 honestly. A real Baseline curve waits until CoverTrace persists its Baseline.
- **Errors.** Plain messages for: backend down, replay failed (with the reason), replay already running (409), unknown or already closed Alert, and no data. The Console never blocks the CLI path.
- **Dev connection.** The Vite dev server forwards the API and WebSocket paths to the local backend, so no cross-origin setup is needed. The backend stays local-only. The Console service is added to the compose stack in the one-command demo ticket (#67), as the Backend Spec says.
- **CI.** The existing dashboard job runs install, lint and build. A test step is added.
- **Style.** First cut is a plain, clean dark layout. Visual polish, including the SENTINEL mock direction, is a separate human ticket in Cycle 5, owned by Ayush, and is first on the cut line.
- **Contracts.** No contract change. The Console only reads and renders them.

## Testing Decisions

- **Good test.** It checks external behaviour only: what the user sees and which API calls the Console makes, given what the backend sends. It never inspects component internals or state.
- **One seam.** The whole Console against a fake backend, with mocked REST responses and a mocked WebSocket, using Vitest and Testing Library. Everything below the screen (API client, live handler, views) is covered through it.
- **Cases at the seam.**
  - Pick a pcap, start a replay, see live Detections, one Alert and the finish counts.
  - The control run shows zero Alerts in its counts.
  - A page opened mid-replay shows history from REST and then live items, with no duplicates.
  - After a socket reconnect, the Console reads REST again and the banner clears.
  - Close an Alert once; an already closed or unknown Alert shows a clear message.
  - Replay failed shows the reason; replay already running (409) shows a clear message.
  - Backend down shows a plain message and the Console recovers when it returns.
  - Empty states for each list.
  - Later cycles: session timeline with tags and "no tag"; Rule approve and reject only on proposed Rules; the compare view shows two thresholds.
- **Not tested here.** The real stack is checked by hand in the demo, tied to the one-command demo ticket. Visual style is judged by Ayush, not by tests. No browser end-to-end tests.
- **Prior art.** The Backend Spec's seam (an API test client fed by crafted pcaps) and the pipeline tests that assert one Alert on the tunnel Entity and none on the control. The Console tests use the same two pcap stories as mock data.

## Out of Scope

- The backend itself (its own spec and tickets #63 to #67), the detectors, MimicNet and the Gate.
- A flows endpoint and any display of benign flows.
- A Baseline curve or Baseline view, and persistence of the Baseline.
- A sessions list, authentication, multi-user, remote access, file upload, live capture.
- Editing detector settings or Rules from the Console, and automatic approval of Rules.
- Visual style and SENTINEL polish (separate human ticket).
- Browser end-to-end tests.

## Further Notes

- **Honesty.** The Dashboard stays Designed in the ledger until a view is merged and tested. A view that needs MimicNet data (session, Rules) stays Designed until MimicNet ships its endpoints.
- **Suggested tickets (routing by complexity, not size).** All owner Ayush, label `module:backend-console`. The dispatcher checks only Python and `agy` cannot run `npm`, so every Console ticket goes to Claude. (1) Scaffold, API client, replay start and live feed: Claude, Cycle 2, blocked by #65. (2) Alerts with close, Detections, Replays history, error and empty states: Claude, Cycle 2, blocked by 1. (3) Session timeline with MITRE tags: Claude, Cycle 3, blocked by 2 and the session endpoint. (4) Rules approve and reject: Claude, Cycle 4, blocked by 2 and the Rules endpoints. (5) Threshold compare view: Claude, Cycle 4, blocked by 2. (6) Visual style and SENTINEL polish: human task, no agent label, Ayush, Cycle 5, first on the cut line; the SENTINEL mock prompts were not found in the Downloads folder, so Ayush shares them when that ticket starts. Old tickets #8 and #9 close as superseded; #24 closes with the spec PR.
- **Shared-file changes needed (not made here).** Backend Spec and ticket #65: add the endpoint that lists pcaps in the data folder, and name the WebSocket path (ADR 0004 says `/ws/events`). Main spec: reword demo step 2 (show replay counts, not benign flows), demo step 7 and the Baseline wording (threshold compare), add the pcap list to section 5, update the Dashboard ledger row. CI workflow: add the test step. ADR 0004: mark fully Accepted now that React and Recharts are confirmed. Glossary: optionally add "Threshold compare".
- **Seam check.** One seam as agreed: the whole Console against a fake backend with mocked REST and WebSocket. Changed from the grilling: none.
