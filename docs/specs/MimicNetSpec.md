# MimicNet Spec

Status: Draft, from the grilling on 2026-10-22 (issue #22, MimicNet part). Vocabulary follows `GLOSSARY.md`. Respects ADR 0002 (independent modules, in-process), ADR 0006 (closed loop: automated extraction, analyst approval) and ADR 0008 (engine plus CLI is the product).

## Problem Statement

When the gate raises an Alert, an analyst knows a machine is probably leaking data through a covert channel, but learns nothing about what the attacker does next. The analyst also has to write detection rules by hand, so the next attack by the same attacker is caught no sooner than the first. GKMKB has no response layer today: the MimicNet folder is empty and its pieces (honeypot, MITRE mapping, rule generation, banner variation) exist only as open tickets with no owner.

## Solution

MimicNet becomes a small response layer behind two entry points. When an Alert arrives, `engage` starts one isolated Docker container that runs a fake SSH-like shell and records everything an attacker types as a Honeypot session. When the session ends, `rules_from` reads it and proposes detection Rules (the tunnel domain and the attacker address). An analyst approves or rejects each Rule. Approved Rules reach CoverTrace, which then flags matching traffic at once instead of waiting to collect evidence. The session also gets MITRE ATT&CK tags, so the analyst sees what kind of behaviour was seen, and an unknown behaviour gets no tag.

In the lab, the team plays the attacker with a fixed script. No real attacker traffic is claimed anywhere.

## User Stories

1. As an analyst, I want an Alert to start a honeypot automatically, so that I learn what the attacker does after the covert channel is found.
2. As an analyst, I want exactly one honeypot at a time, so that the lab laptop is not overloaded.
3. As an analyst, I want a second Alert during a running session to be refused clearly, so that I know why no second honeypot started.
4. As an analyst, I want the Alert status to change to engaged and carry the session id, so that I can open the right session.
5. As an analyst, I want every command and connection in the session logged with a time, so that I can replay what happened.
6. As an analyst, I want the attacker address stored in the session, so that I can block it.
7. As an analyst, I want a session to end by itself after a maximum time, so that a stuck attacker cannot hold the honeypot forever.
8. As an analyst, I want a session to end when the attacker disconnects, so that results arrive quickly.
9. As an analyst, I want MITRE ATT&CK tags with the evidence line next to each tag, so that I can check why a tag was given.
10. As an analyst, I want behaviour the table does not know to get no tag, so that I am never shown a guessed technique.
11. As an analyst, I want proposed Rules to appear after a session, so that I do not write them by hand.
12. As an analyst, I want a Rule to show which session it came from, so that I can trust or reject it.
13. As an analyst, I want a Rule to do nothing until I approve it, so that a bad Rule cannot raise false alarms on its own.
14. As an analyst, I want a rejected Rule to have no effect, so that rejecting is safe.
15. As an analyst, I want an approved Rule to catch the same attacker earlier on replay, so that I can see the closed loop pay off.
16. As an analyst, I want a Rule hit to be labelled with the Rule id, so that I can tell it from a statistical Detection.
17. As an analyst, I want the Rule hit to score high enough for the gate to count it, so that the loop actually changes the outcome.
18. As a team member playing the attacker, I want a fixed command script, so that every demo run gives the same session.
19. As a team member, I want the demo script to run the attacker after `engage` starts the container, so that the full demo runs from one command.
20. As a developer, I want the fake shell to be a plain class I can test without Docker, so that tests run on any laptop and in CI.
21. As a developer, I want only the container wrapper to need Docker, so that a missing Docker install fails one marked test, not the suite.
22. As a developer, I want the container to have no host mounts, a memory cap, a CPU cap and no way out to other networks, so that a mistake cannot touch the host.
23. As a developer, I want the container removed after every session, even after an error, so that no stray containers pile up.
24. As a developer, I want `rules_from` to read only the session, so that it is a pure function I can test with a hand-made session.
25. As a developer, I want no contracts change, so that the other owners are not blocked.
26. As the report author, I want each MimicNet claim to have its own honesty ledger row, so that I only claim what is Working.
27. As the report author, I want the docs to say the shell is "SSH-like" and not real SSH, so that the report does not overclaim.
28. As a reviewer, I want fingerprint variation listed as the first item on the cut line, so that dropping it is expected, not a failure.
29. As a viva examiner, I want the list of defended probes written down, so that I can see what the honeypot does not defend.
30. As a teammate picking up a ticket, I want each piece small and independently testable, so that an agent can build it without Docker knowledge.

## Implementation Decisions

- **Two entry points, as in the main spec.** `engage(alert)` returns a Honeypot session. `rules_from(session)` returns a list of proposed Rules. Both stay inside the MimicNet module and import only from the shared contracts.
- **Fake shell.** One SSH-like text service written in plain Python. It prints a banner, accepts typed lines, answers from a small canned table and logs every line. It has no real login and no real cryptography. All docs and output call it "SSH-like".
- **Shell is a plain class.** The shell logic is separate from the network and container code, so tests drive it with a list of commands in process. The container only runs the shell.
- **Session events.** The first event is a connect event holding the attacker address. Each typed line is a command event. The last event is a disconnect or a timeout. Event data stays string-to-string, as the contracts require.
- **Container control.** `engage` uses the Python `docker` package, already in the requirements. It starts one container with no host mounts, a memory cap, a CPU cap, no outbound network and a maximum life of 120 seconds. The shell prints events as JSON lines and `engage` reads them from the container logs. The container is removed at the end, including after an error. A second `engage` while one runs is refused with a clear error.
- **Settings.** Maximum life, caps, banner list and the listening port are settings with defaults, not constants.
- **Scripted attacker.** A fixed command list in the repo, played by the team. `engage` does not run it; the demo script does, after `engage` has started the container. One command in the list is a tunnel-client command that contains the tunnel domain.
- **Rule source.** `rules_from` reads only the session events. It takes the attacker address from the connect event and the tunnel domain from command text. The Alert carries no domain or address, so this keeps the contracts unchanged.
- **Rule kinds, first cut.** Two kinds only, both targeting CoverTrace: a query-name suffix match and a source-address match. Every Rule is born proposed. The "payload string" and "threshold nudge" kinds from ADR 0006 are out of the first cut (no detector reads payload; threshold nudges are cut-line depth).
- **Rule states.** Proposed, then approved or rejected by the analyst, then active when loaded. Only active Rules reach CoverTrace.
- **Rule loading.** The backend hands the active Rules to CoverTrace through one call that sets its rule list. A flow that matches an active Rule gives a Detection at once with score 1.0 and a label made from the Rule id. This is what "caught earlier" means in demo step 6 of the main spec. This is a separate small CoverTrace ticket, not part of the CoverTrace tickets #46 to #48.
- **MITRE interface.** A function takes session events and returns MITRE tags, each with an evidence line, from a keyword table. Unknown behaviour returns no tag. The table contents are decided in the evaluation and MITRE grilling (#25); every technique id is checked against attack.mitre.org by Sharukh and stays Unverified until then.
- **Fingerprint variation.** Last MimicNet ticket, Cycle 4, first on the cut line. A seeded pick chooses one of three banners per session, plus a small response delay. The docs list the defended probes: banner grab only. Timing stays "not defended" until measured.
- **Owner and cycles.** Shivansh owns MimicNet; Ayush reviews. Honeypot and `engage` are Cycle 3. MITRE mapping is Cycle 3. Rule generation, rule loading and fingerprint variation are Cycle 4.
- **Routing (complexity decides, not size).** To `agy`: fake shell and scripted attacker, `rules_from`, MITRE keyword table, banner pick, CoverTrace rule loading. These are plain Python the dispatcher can test. To Claude: Docker wrapper and `engage`, because `agy` cannot run Docker.

## Testing Decisions

- **Good test.** It checks external behaviour only: given commands or flows in, what session, tags, Rules or Detections come out. It never reads private state or internal helpers.
- **Seam 1, main, no Docker.** Scripted attacker commands go into the fake shell and give a session; `rules_from` turns the session into Rules. One seam covers the shell, event logging, MITRE mapping, banner pick and rule extraction. Checks: events and order, attacker address captured, expected tags for the scripted session, no tag for unknown commands, Rules valid against the contracts, and every Rule born proposed.
- **Seam 2, Docker smoke, one test with a Docker mark.** `engage` runs a real container against the scripted attacker. Checks: the session has events, the container is gone afterwards, and a second `engage` while one runs is refused.
- **Seam 3, existing CoverTrace seam.** A flow in, a Detection or nothing out, fed by replayed crafted pcaps. Checks: a matching active Rule gives an immediate Detection with the Rule label; a proposed or rejected Rule changes nothing; an approved Rule raises the score on re-replay compared with no Rule.
- **Banner and timing.** Two sessions with different seeds show different banners; the same seed gives the same banner. A banner-grab probe test passes.
- **Prior art.** The gate tests (a pure function over hand-made Detections), the CoverTrace entropy and replay tests that build pcaps with scapy, and the pipeline tests that assert one alert on the tunnel Entity and none on the control.
- **No real-attacker tests.** All sessions in tests come from the team's script or from hand-made sessions.

## Out of Scope

- Real SSH, real login, a second service, or more than one container at a time.
- Real attacker traffic, internet-facing honeypots, or any live deployment.
- Rule kinds "payload string" and "threshold nudge", and Rules that target FlowSight.
- Automatic approval of Rules; the analyst always decides.
- The MITRE table contents (evaluation and MITRE spec, #25), the dashboard session and Rule views (dashboard spec, #24), and persistence of sessions (backend spec).
- Defending against timing probes, TLS or process fingerprinting.

## Further Notes

- **Shared files not edited. Needed changes for Ayush:**
  - `GkmkbSpec.md`: M3 first cut targets CoverTrace only; the loading hook is a rule-setting call on CoverTrace; the M3 owner is Shivansh.
  - ADR 0006: drop "payload string" and "threshold nudge" from the first cut.
  - `GLOSSARY.md`: add "Scripted attacker" and "Rule hit".
- **Stale blockers.** #18 lists #6 (Mongo compose), which MimicNet does not need; drop it. #28 lists #11 and #29, both closed; drop them. A new CoverTrace rule-loading ticket is needed and must block #28's acceptance of "approved Rule changes detection on re-replay".
- **Honesty ledger rows to add**, all starting Designed: honeypot with session recording, MITRE tagging, rule generation, rule loading in CoverTrace, banner variation. The report claims only rows marked Working.
- **Lab safety.** The container runs only in the isolated lab on team-owned machines. The ethics text in the report outline already states this; no change needed.
- **Seam check.** Three seams as agreed: in-process session-to-rules, one Docker smoke test, and the existing CoverTrace entry point.
