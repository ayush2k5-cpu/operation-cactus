# Backend Spec

Status: Draft, from the grilling on 2026-10-22 (issue #22, backend part). Vocabulary follows `GLOSSARY.md`. Respects ADR 0002 (detectors are independent, in-process), ADR 0008 (Engine plus CLI is the product, the Console is a viewer). ADRs 0003 (gate), 0004 (WebSocket) and 0005 (MongoDB) are still marked "Proposed" in the repo; Ayush accepted all three in the grilling, so this spec treats them as accepted.

## Problem Statement

The Engine works from the command line: `gkmkb replay <pcap>` runs a pcap through the detectors and the Gate and prints the result. That is enough for a developer, but not for the team or the panel. Nothing is saved, so every result vanishes when the command ends. The Console has nothing to talk to. Nobody can watch a replay happen live. Starting the whole thing needs several manual steps on every laptop. The Gate has no way to be told an Alert is finished, and IDs restart from 0001 on every run, so results from two runs cannot share one database.

## Solution

A thin backend wraps the Engine. An analyst asks it to replay a pcap from the lab data. The backend runs the replay in the background and pushes each Detection and Alert to the Console the moment it happens. It saves everything in MongoDB, so results can be listed afterwards and compared across replays. The analyst can close an Alert. One Docker compose command starts the database and the backend. One demo script starts the stack, replays the demo pcap and the control pcap, and prints which demo steps are built and which are not.

The CLI keeps working with no database and no web server. That is the fallback demo (ADR 0008).

## User Stories

1. As an analyst, I want to start a replay of a lab pcap from the Console, so that I can run the demo without a terminal.
2. As an analyst, I want to see each Detection appear while the replay runs, so that the demo feels live.
3. As an analyst, I want to see an Alert appear the moment the Gate raises it, so that I know right away when both detectors agree.
4. As an analyst, I want to see when a replay is finished, with its result counts, so that I know nothing more is coming.
5. As an analyst, I want a replay that fails (missing or broken pcap) to say so clearly, so that I do not wait for events that never arrive.
6. As an analyst, I want to list past Detections, so that I can study what the detectors saw.
7. As an analyst, I want single-signal Detections to be stored too, so that I can see what the Gate chose not to escalate.
8. As an analyst, I want to list Alerts, newest first, so that I see the latest first.
9. As an analyst, I want to filter Detections and Alerts by replay, so that I can look at one run at a time.
10. As an analyst, I want to list past replays with their pcap name, start and end time, result counts and state, so that I can find a run.
11. As an analyst, I want to close an Alert, so that the same machine can raise a new Alert later in the same replay.
12. As an analyst, I want closing an unknown or already closed Alert to give a clear answer, so that I am not confused by silent success.
13. As an analyst, I want the Alert, Detection and replay IDs to stay unique across runs, so that two replays never overwrite or mix each other.
14. As a Console developer, I want to load history over REST and then subscribe to live events, so that a page opened late still shows everything.
15. As a Console developer, I want every live message to have the same envelope (type, replay ID, data), so that one handler covers all message types.
16. As a Console developer, I want the data inside a message to be the same JSON as the REST contract models, so that I write one set of types.
17. As a Console developer, I want a dropped or reconnecting WebSocket client never to break a running replay, so that the demo survives a browser refresh.
18. As a Console developer, I want a health endpoint, so that I can tell whether the backend is up.
19. As a Console developer, I want the API described by OpenAPI that matches the contracts, so that I can generate or check types.
20. As a demo presenter, I want a delay between live events that I can set, so that a replay that takes milliseconds still looks live on screen.
21. As a demo presenter, I want the delay to default to zero, so that tests and the CLI are never slowed down.
22. As a demo presenter, I want one command that starts everything and replays the demo pcap, so that the panel sees a working system in minutes.
23. As a demo presenter, I want the demo to replay the control pcap too and show zero Alerts, so that the single-signal story is visible.
24. As a demo presenter, I want the demo script to say which of the seven demo steps are not built yet, so that nothing is faked.
25. As a demo presenter, I want the demo to fall back to the CLI when Docker is missing, so that a broken laptop does not end the demo.
26. As a developer, I want a second replay requested while one is running to be refused with a clear answer, so that state from two runs never mixes.
27. As a developer, I want each replay to start with a fresh Gate and fresh detectors, so that one run cannot affect the next.
28. As a developer, I want the pipeline to take a list of detectors, so that the real FlowSight and CoverTrace replace the stubs without touching the backend.
29. As a developer, I want the pipeline to yield each Detection and Alert as it happens, so that the CLI, the API and the WebSocket all share one source.
30. As a developer, I want the Gate window and threshold to come from settings, with CLI flags overriding them, so that tuning needs no code change.
31. As a developer, I want safe defaults when no settings are given, so that the backend always starts.
32. As a developer, I want storage behind a small interface with an in-memory fake, so that my tests need no Docker or database.
33. As a developer, I want the same storage tests to be runnable against real MongoDB when a database is available, so that the real version is checked too.
34. As a developer, I want `gkmkb serve` to start the API, so that the container and my laptop start it the same way.
35. As a developer, I want the CLI to behave exactly as it does today, so that existing tests and the headless demo keep working.
36. As a developer, I want the backend to be the only place that wires the modules together, so that module boundaries hold (ADR 0002).
37. As a security-minded reviewer, I want a replay request to accept only a pcap inside the data folder, so that nobody can read other files through the API.
38. As a security-minded reviewer, I want no file upload, so that no unknown pcap enters the system.
39. As a security-minded reviewer, I want the API to listen on the local machine only, so that a lab laptop is not exposed.
40. As a team lead, I want the data folder mounted read-only into the backend container, so that the backend cannot change lab data.
41. As a team lead, I want teardown to keep the database volume unless I ask to remove it, so that an accidental teardown loses nothing.
42. As a team lead, I want the ledger to say the Gate is Working and the backend API is Designed until it is built, so that the report claims only what exists.
43. As a future maintainer, I want the sessions, rules and baselines collections and their endpoints left for the MimicNet and CoverTrace work, so that this spec stays small.
44. As a future maintainer, I want the honeypot's Docker access flagged as a risk now, so that it is decided on purpose, not by accident.

## Implementation Decisions

- **Modules.** The backend wires a capture source, a list of detectors and the Gate. It is the only place that does so. Detectors are plain objects with an `analyze(flow)` call and no web or database code.
- **Pipeline as a stream.** The pipeline takes a pcap and a list of detectors, builds a fresh Gate, and yields each Detection and each Alert in order. The CLI collects the stream into its printed summary; the API pushes it to storage and the WebSocket. The CLI output and exit code stay as they are today.
- **Detector list.** The default list is the real CoverTrace and the FlowSight stub. When the real FlowSight lands, it replaces the stub in the list. Nothing else changes.
- **Replay ID and unique IDs.** Each replay gets a `replay_id`. Every Detection and Alert ID carries it as a prefix, so IDs from different runs never collide. The pipeline adds the prefix before a Detection reaches the Gate, so Alert references to Detections stay correct. Detector modules and the contract models do not change, because IDs are plain strings.
- **Fresh state per replay.** Each replay builds new detectors and a new Gate. Nothing carries over.
- **Settings.** Gate window, Gate threshold, the delay between live events, the MongoDB address and database name, and the data folder come from the environment, with safe defaults in code. CLI flags override the environment. The database address and name already exist in the example environment file; the delay and data folder are added.
- **Alert lifecycle.** An Alert is born `open`. The analyst closes it through the API, which also tells the Gate, so the same Entity can alert again within that replay. `engaged` is set by MimicNet later and is not part of this spec. Closing an unknown Alert gives "not found". Closing an already closed Alert gives a clear "already closed" answer and changes nothing.
- **Storage.** MongoDB (ADR 0005). Stored: every Detection (including single-signal ones), every Alert, and a `replays` record holding pcap name, start time, end time, state (running, done, failed), an error message when failed, and counts of flows, Detections and Alerts. The `sessions`, `rules` and `baselines` collections are left unused here. The API talks to a small storage interface with two implementations: the real MongoDB one and an in-memory fake.
- **CLI and database.** The CLI never touches the database. It works with no Mongo and no web server.
- **Replay execution.** The replay request returns the new `replay_id` at once, and the replay runs in a background worker. Only one replay runs at a time; a second request gets a "busy" answer (409). If the pcap is missing or unreadable, the replay record becomes `failed` with the reason, and the WebSocket sends the finish message with that state.
- **Pacing.** A setting holds a delay in milliseconds between live events. The default is 0. The demo script sets about 300 so that a replay that takes milliseconds looks live. The delay applies only to API replays, never to the CLI.
- **REST endpoints built here.**
  - Health check.
  - Start a replay (body: pcap name).
  - List Detections.
  - List Alerts.
  - Close an Alert.
  - List replays.
  - List the pcap names in the data folder (added after the dashboard spec, so the Console can offer a picker; ticket #70).
  
  List endpoints return newest first, accept an optional replay filter and a limit with a sensible default and maximum. The sessions and rules endpoints from the main spec are left to the MimicNet tickets.
- **Replay path rule.** The pcap name must resolve to a file inside the data folder. Anything that resolves outside it is rejected. There is no upload, no authentication (a main-spec non-goal), and the server listens on the local machine only.
- **WebSocket.** One endpoint, `/ws/events` (ADR 0004), pushes messages shaped `{type, replay_id, data}`. Types built here: `detection`, `alert`, `replay_done`. `data` holds the contract JSON for the first two; `replay_done` holds the final state and counts. A client that joins late receives nothing from the past: it reads REST first, then subscribes. A client that disconnects or reconnects never stops or crashes a replay. `session_event` and `rule` messages arrive with MimicNet.
- **`gkmkb serve`.** A new CLI command that starts the API. The container uses the same command.
- **Compose stack.** Two services, the database and the backend, each with a health check. The database has a named volume. The data folder mounts read-only into the backend. The environment comes from the example environment file. Teardown keeps the volume unless asked to remove it. The Console service is added when the Console exists.
- **Honeypot Docker access (flagged, not decided).** MimicNet will need the backend to start containers, which means giving the backend container access to the host Docker engine. That is a real security trade-off on a lab machine. It is decided in the MimicNet spec, not here.
- **Demo script.** One Python script (Python 3.12 is already required) replaces the separate PowerShell and shell scripts in the earlier demo ticket. It starts the stack and waits for health, replays the demo pcap and the control pcap, then prints the seven demo steps from the main spec, each marked built or "not built yet (Designed)". It never invents a result. If Docker is missing, it runs the CLI replay instead and says so.
- **Contracts.** No contract model changes. Replay state and the WebSocket envelope are backend shapes, not shared contracts.

## Testing Decisions

- **Good test.** It checks external behaviour only: what a caller sends in, what comes back, what the WebSocket receives, what the storage holds afterwards. It never inspects private state or helper functions.
- **One seam.** The HTTP API: a test client that calls the REST endpoints and a WebSocket connection, fed by crafted pcaps, with the in-memory fake storage. A test starts a replay, reads the live messages, then reads the stored results through REST. This is one new seam at the highest point; everything below it (stream, Gate, storage interface) is covered through it. Existing seams stay: the Gate unit tests and the pipeline and CLI tests on crafted pcaps keep running unchanged as the guard for the CLI.
- **Cases at the seam.**
  - A tunnel pcap gives live Detection messages, one Alert message and a finish message, and the same rows via REST.
  - The control pcap gives zero Alerts.
  - Two replays never share IDs.
  - A second replay while one runs gets 409.
  - A path outside the data folder, and a missing pcap, are rejected or recorded as failed with a clear reason.
  - Closing an Alert works once; unknown and already closed cases answer clearly; after closing, the same Entity can alert again within that replay.
  - A WebSocket client that disconnects mid-replay does not stop the replay.
  - List endpoints filter by replay and respect the limit and order.
  - The event delay setting changes pacing with a tiny delay; the default does not slow tests.
- **Storage.** The same storage tests run against the in-memory fake always, and against real MongoDB only when a database address is available, so CI and teammates without Docker stay green.
- **Compose and demo.** Not unit-tested. Verified by hand on a clean machine, tied to the setup verification ticket.
- **Prior art.** The Gate unit tests, and the pipeline and CLI tests that build pcaps with scapy and assert one Alert on the tunnel Entity and none on the control.

## Out of Scope

- The Console itself (its own spec).
- FlowSight, CoverTrace, MimicNet and the closed-loop rules.
- The sessions and rules endpoints and the `session_event` and `rule` messages.
- Persisting the CoverTrace Baseline, and anything in the `baselines` collection.
- Authentication, multi-user, remote access, upload, live capture.
- Starting honeypot containers, and the Docker access decision for it.
- Evaluation metrics and datasets.

## Further Notes

- **Honesty.** The Gate is merged and tested: it can move from Designed to Working. The backend API, storage, WebSocket and compose stack stay Designed until each ticket merges.
- **Seam check.** Please confirm the single seam above (the HTTP API with a test client, WebSocket and the fake storage) matches what you expect. If you want a lower seam for the Gate or the stream, say so and the testing section changes.
- **Suggested build split (for `/to-tickets`).** Pipeline stream, IDs, settings and `gkmkb serve` (Claude). Storage interface, fake and MongoDB version (`agy`). REST endpoints and path guard (`agy`). Background replay and WebSocket (Claude). Dockerfile and compose (Claude, hand-verified). Demo script (Claude, Cycle 5). All owned by Ayush. These replace the earlier backend, compose, WebSocket and demo tickets (#4, #6, #31, #13).
- **Shared-file changes needed (not made here).** Accept ADRs 0003, 0004 and 0005. Main spec sections 5 and 6: add the close endpoint, the health endpoint, the replays list and the `replay_done` message. Main spec ledger: Gate to Working. Glossary: add "Replay run" (`replay_id`). Earlier demo ticket: one Python script instead of two shell scripts. MimicNet spec: decide Docker access for the backend container.
