# CoverTrace Spec

Status: Draft, from the grilling on 2026-10-22 (issue #23). Vocabulary follows `GLOSSARY.md`. Respects ADR 0002 (independent detectors, in-process), ADR 0003 (gate correlates on Entity and window) and ADR 0008 (engine plus CLI is the product).

## Problem Statement

An analyst wants to know when a machine on the network is leaking secrets or data through a covert channel. Today CoverTrace catches only one kind: DNS tunnels with random-looking subdomain names, judged against a fixed limit. That has three weaknesses. It misses covert channels that hide in ping timing or in strange DNS shapes. It raises false alarms on harmless random-looking names such as CDN hashes and `.local`, because the limit is fixed for every network. And it flags a machine once and never again, so a second attack on the same machine is invisible.

## Solution

CoverTrace becomes a small set of checkers behind one entry point. Each checker looks for one kind of covert-channel behaviour. CoverTrace gives the gate one combined answer per Entity: a single Detection whose score is the highest checker score and whose features show every checker's value and which one fired.

The DNS entropy limit adapts: CoverTrace learns what normal looks like on this network and alarms only when traffic is far above it. Harmless look-alikes are skipped through a short configurable list. A machine can be flagged again after it has been quiet for a full window, so each attack gets its own alarm.

## User Stories

1. As an analyst, I want one CoverTrace alert per attack on a machine, so that I am not flooded with repeats.
2. As an analyst, I want a second attack on the same machine to raise a new detection after a quiet period, so that I do not miss repeat offenders.
3. As an analyst, I want to see which checker fired (DNS entropy, ping timing, DNS shape), so that I know why the machine was flagged.
4. As an analyst, I want every checker's value shown with the detection, so that I can judge how strong the evidence is.
5. As an analyst, I want a DNS tunnel with random-looking names flagged, so that data hidden in DNS is noticed.
6. As an analyst, I want a ping timing channel flagged, so that data hidden in the gaps between pings is noticed.
7. As an analyst, I want very long DNS names, mostly TXT or NULL record queries, and bursts of queries flagged, so that tunnels that avoid random names are still noticed.
8. As an analyst, I want harmless random-looking names (CDN hashes, `.local`, `.arpa`) not to trigger alarms, so that I can trust the alerts.
9. As an analyst, I want the threshold to follow what is normal on my network, so that a busy or unusual network does not drown me in false alarms.
10. As an analyst, I want an attacker not to be able to teach CoverTrace that bad traffic is normal, so that the learned normal stays trustworthy.
11. As the gate, I want exactly one CoverTrace Detection per Entity per episode with a score from 0 to 1, so that correlation with FlowSight stays simple.
12. As the gate, I want the Detection's Entity to be the source and destination pair, so that it joins with FlowSight on the same key.
13. As the gate, I want `threshold_used` set on every Detection, so that downstream tools know the limit that applied.
14. As a developer, I want each checker small and testable alone, so that I can change one without breaking the others.
15. As a developer, I want a single public entry point that takes one flow and returns a Detection or nothing, so that the backend wires CoverTrace the same way as any detector.
16. As a developer, I want CoverTrace to keep its own per-Entity state, so that tunnels made of many one-packet flows are seen.
17. As a developer, I want thresholds, window sizes and the skip-list in a settings file, so that I can tune without editing code.
18. As a developer, I want safe defaults used when the settings file is missing, so that CoverTrace always starts.
19. As a developer, I want a way to run the same traffic against two different learned normals, so that I can show the threshold really adapts.
20. As a developer, I want the checker order clear (entropy, ping timing, DNS shape, then web headers), so that I know what to build next and what drops first.
21. As an evaluator, I want precision, recall and false-alarm numbers to come from real tool-generated tunnel traffic, so that the report does not rest on faked data alone.
22. As an evaluator, I want to compare the fixed limit with the learned limit on the same traffic, so that the benefit of adaptation is measurable.
23. As an evaluator, I want benign test traffic to include CDN-style names, so that the false-alarm rate is reported honestly.
24. As a demo presenter, I want the demo pcap to raise one CoverTrace Detection for the tunnel and none for the control, so that the headline demo is reliable.
25. As a team lead, I want each checker to carry an honest ledger state (Designed, Partial, Working), so that the report claims only what exists.
26. As a team lead, I want the optional web header checker clearly marked as last and droppable, so that time pressure never breaks the core.
27. As a privacy-minded reviewer, I want CoverTrace to read only metadata, DNS names, ping times and header names from replayed lab data, so that no real user's content is inspected.
28. As a future maintainer, I want the learned normal kept in memory only for now, with persistence added by the backend later, so that this spec does not depend on Mongo.
29. As a future maintainer, I want the aggregator able to be split or weighted later without changing the gate, so that we can improve the combined score.
30. As the Paper 1 authors, I want the four Paper 1 CoverTrace indicators mapped to checkers (entropy, ping timing chi-square, header anomaly, protocol structure), so that the report links code to the paper.

## Implementation Decisions

- **Checkers.** CoverTrace holds a list of checkers. Build order: (1) DNS subdomain entropy (exists today), (2) ICMP timing chi-square, (3) DNS shape rules, (4) HTTP header anomaly, optional and last. Checker 4 drops first if time runs short.
- **One combined answer.** The CoverTrace entry point takes one `FlowRecord` and returns a `Detection` or nothing. Score is the highest checker score. `label` names the checker that produced it. `features` holds every checker's value as floats. `source` is `covertrace`. `threshold_used` is the limit that fired. This can be split or weighted later without changing the gate.
- **Entity and state.** The Entity is the source and destination pair (ADR 0003). CoverTrace keeps per-Entity state inside the object, because each tunnel query is often its own one-packet flow.
- **Episodes.** One Detection per Entity per episode. After an Entity is flagged, it is not flagged again until it has been quiet for one full window (default 60 seconds), then it can be flagged anew. The gate's one-open-alert-per-Entity rule is unchanged.
- **Score scale.** Every checker scores 0 to 1. Just past its threshold a checker scores about 0.5; clearly past it scores close to 1. The gate keeps its own threshold; whether 0.7 is right is for the evaluation spec to tune.
- **ICMP timing chi-square.** Needs at least 20 pings from an Entity in the window. Compares the spread of gaps between pings against a fixed expected "normal" spread, using the chi-square test as in Paper 1. A learned normal replaces the fixed guess later.
- **DNS shape rules.** Three rules add to the score: DNS names longer than 50 characters; more than half of queries being TXT or NULL records; more than 20 queries in 10 seconds from one Entity. All numbers are settings.
- **HTTP header anomaly (optional).** Needs the capture step to parse HTTP request headers, and probably a `FlowRecord` change beyond the current header-name list. That contract change needs every module owner's review and is decided only if this checker is built.
- **Adaptive Baseline.** One Baseline for the whole network (lab traffic has few Entities). It keeps a rolling mean and standard deviation of subdomain-label entropy over the last 15 minutes, updated per flow, using only Entities that are not currently flagged. Adaptive threshold = the larger of a safe floor (3.0 bits) and mean plus three standard deviations. Until it has seen 50 labels, the static limit of 3.5 bits applies. The Baseline lives in memory only; persistence arrives with the backend.
- **Skip-list.** A short list of name suffixes (examples: `.local`, `.arpa`, `cloudfront.net`, `akamaiedge.net`) is skipped before scoring. The list is a setting.
- **Settings.** A settings file inside the CoverTrace module holds thresholds, window sizes, the skip-list and every number above. Safe defaults in code apply when the file is missing.
- **Existing detector.** The current DNS entropy detector becomes the first checker. Its public behaviour (one Detection when mean label entropy crosses the limit with at least 20 queries in the window) must keep working until the adaptive rule replaces the fixed one.
- **Contracts.** No `FlowRecord`, `Detection`, `Alert` change is needed for checkers 1 to 3, because `features` is a free map of floats.
- **Honesty.** Each checker has its own ledger row. Paper 1 numbers are synthetic and are never quoted as results of this engine.

## Testing Decisions

- **Good test.** It checks external behaviour only: given flows in, does a Detection come out, with what score band, label and features. It never inspects private state or internal helper functions.
- **One seam.** The CoverTrace entry point that takes a `FlowRecord` and returns a `Detection` or nothing, fed by FlowRecords that `ReplaySource` builds from crafted pcaps. This is the highest existing seam (the pipeline already calls CoverTrace this way). One end-to-end check through the replay pipeline stays as a smoke test.
- **Per checker.** One pcap where the checker fires and one where it stays quiet. Covers DNS entropy, ping timing and each DNS shape rule.
- **Learned normal.** The same traffic run against two different normals yields two different thresholds and, at the edge, different outcomes. Also: a flagged Entity does not move the Baseline, and the first 50 labels use the static limit.
- **Skip-list.** CDN-style and `.local` names do not raise a Detection; the same shape of name on an unlisted suffix does.
- **Episodes.** After a flag, further traffic raises nothing; after a quiet window the same Entity can be flagged again.
- **Settings.** A missing settings file gives working defaults; a changed number changes behaviour.
- **Prior art.** The existing CoverTrace entropy tests, the replay tests that build pcaps with scapy, and the pipeline tests that assert one alert on the tunnel Entity and none on the control.
- **Real-tool traffic.** Tool-generated pcaps (iodine or dnscat2) are used for evaluation, not for unit tests.

## Out of Scope

- FlowSight, the gate's own logic, MimicNet and the closed-loop rules.
- Evaluation metrics and datasets (the evaluation spec covers them).
- Live capture, persistence of the Baseline in a database, and any machine-learning classifier.
- DNS over HTTPS or encrypted payload inspection.
- The HTTP header checker, unless time allows; it is optional and last.

## Further Notes

- Real tool-generated tunnel traffic (iodine or dnscat2 between two of the team's own laptops, with consent, labelled "tool-generated") is required before any CoverTrace evaluation number goes in the report. Crafted pcaps remain for the demo and tests.
- Design finding from Cycle 1: a tunnel can be one long single-port flow or many one-packet flows, so per-Entity aggregation is required for every checker.
- Suggested owner for the build: Shivansh, with Cycle 2 for checkers 2 and 3 and Cycle 4 for the adaptive Baseline (matching the cut line: adaptive is third from the drop-first end).
- Seam check: please confirm the single seam above (the CoverTrace entry point fed by replayed crafted pcaps) matches what you expect. If you want a lower seam for the Baseline maths, say so and the testing section changes.
