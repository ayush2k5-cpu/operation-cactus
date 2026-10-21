# FlowSight Spec

Status: Draft, from the grilling on 2026-10-22 (issue #22, FlowSight part). Vocabulary follows `GLOSSARY.md`. Respects ADR 0002 (independent detectors, in-process), ADR 0003 (gate correlates on Entity and window) and ADR 0008 (engine plus CLI is the product).

## Problem Statement

An analyst wants a second opinion on a suspicious machine that does not depend on reading DNS names. Today FlowSight is a placeholder: a fixed rule that flags many small packets at an even pace, tagged `[stub]`. It has no flow features and no trained model. Any alert in the demo therefore rests on one real signal (CoverTrace) and one stub, so the gate has never been tried against a real second detector.

A plain per-flow approach would also fail. A DNS tunnel can be one long flow on a single port, or thousands of one-packet flows with a new port per query. A one-packet flow has no packet-size spread and no gaps between packets, so features computed per flow measure nothing.

## Solution

FlowSight watches the traffic of each Entity (source and destination pair) over a sliding window, pools the packets from all of that Entity's flows in the window, and scores the pooled behaviour. A long single flow and many tiny flows look the same to it.

It reads only metadata: packet sizes and the gaps between packets. It never reads DNS names, ICMP times or HTTP header names, so it stays independent of CoverTrace and works on encrypted traffic.

It is built in two steps. Step 1 is a rule-based scorer on four window features and replaces the stub. Step 2 is a small trained classifier behind the same entry point. If step 2 slips, step 1 ships and the ledger says so.

## User Stories

1. As an analyst, I want FlowSight to flag a machine that sends small packets at a machine-like rhythm, so that a covert channel is noticed even when its content is hidden.
2. As an analyst, I want a tunnel built from one long flow flagged, so that single-port tunnels are not missed.
3. As an analyst, I want a tunnel built from many one-packet flows flagged, so that tunnels that change source port per query are not missed.
4. As an analyst, I want one FlowSight Detection per attack on a machine, so that I am not flooded with repeats.
5. As an analyst, I want the same machine flagged again after it has been quiet for a full window, so that a second attack is not hidden by the first.
6. As an analyst, I want each Detection to show the four feature values, so that I can judge how strong the evidence is.
7. As an analyst, I want benign human-paced traffic to score low, so that I can trust FlowSight alerts.
8. As an analyst, I want FlowSight to work when the traffic is encrypted, so that hidden payloads do not blind it.
9. As the gate, I want exactly one FlowSight Detection per Entity per episode with a score from 0 to 1, so that correlation with CoverTrace stays simple.
10. As the gate, I want the Detection's Entity to be the source and destination pair, so that it joins with CoverTrace on the same key.
11. As the gate, I want `threshold_used` set on every Detection, so that downstream tools know which limit applied.
12. As the gate, I want FlowSight to ignore DNS, ICMP and HTTP fields, so that its signal is independent of CoverTrace and a double count never raises an Alert.
13. As a developer, I want one public entry point that takes one flow and returns a Detection or nothing, so that the backend wires FlowSight the same way as any detector.
14. As a developer, I want FlowSight to keep its own per-Entity state, so that tunnels made of many flows are seen.
15. As a developer, I want the four features as small pure functions over a window, so that each is testable by hand.
16. As a developer, I want the window length, burst limit, minimum packet count and score cut in a settings file, so that I can tune without editing code.
17. As a developer, I want safe defaults used when the settings file is missing, so that FlowSight always starts.
18. As a developer, I want the rule-based scorer and the classifier behind the same entry point, so that swapping one for the other changes nothing else.
19. As a developer, I want the stub deleted when the real scorer lands, so that no two FlowSights exist.
20. As a developer, I want the same code to build windows for training and for live replay, so that training data and run data cannot drift apart.
21. As an evaluator, I want precision, recall, F1 and AUC saved by the training step, so that the report numbers are reproducible with a fixed seed.
22. As an evaluator, I want train and test split by capture, not by window, so that near-identical windows do not leak into the test set.
23. As an evaluator, I want results on real tool-generated tunnel traffic kept apart from results on crafted pcaps, so that the report never presents synthetic numbers as real.
24. As an evaluator, I want to compare the gate with FlowSight alone and with CoverTrace alone, so that the benefit of two signals is measurable.
25. As a demo presenter, I want the demo pcap to raise one FlowSight Detection for the tunnel and none for the control, so that the headline demo stays reliable.
26. As a team lead, I want FlowSight's ledger state to be Stub, then Partial with rules, then Working only with a measured classifier, so that the report claims only what exists.
27. As a team lead, I want the classifier to be droppable under time pressure while the rule-based scorer stays, so that the core never breaks (cut line).
28. As a privacy-minded reviewer, I want FlowSight to use only sizes and timings from lab or public data, so that no real user's content is inspected.
29. As a future maintainer, I want the trained model stored as a file and loaded at start, so that the detector has no network or database call.
30. As the Paper 1 authors, I want the four Paper 1 feature names kept, so that the report links code to the paper.

## Implementation Decisions

- **Unit of judgment.** FlowSight keeps a sliding window per Entity (source and destination pair, ADR 0003). Packets from every flow of that Entity inside the window are pooled. Default window 60 seconds, a setting. Per-packet times inside a long flow are rebuilt from the flow's start time and its gaps, then old packets are trimmed by time, so a flow longer than the window is handled.
- **Features.** Four, with the Paper 1 names, over the pooled window: `flow_avg_pkt_size_log` (log of mean packet size), `flow_pkt_size_variance` (variance of packet size), `flow_iat_mean_ms` (mean gap between packets in milliseconds), `flow_burst_ratio` (share of gaps below a burst limit, limit is a setting). Each is a pure function. All four go into the Detection `features` map.
- **Metadata only.** FlowSight uses packet sizes and gaps. It must not read DNS queries, ICMP times or HTTP header names. This keeps it independent of CoverTrace (ADR 0002) and usable on encrypted traffic.
- **Entry point.** One function takes one `FlowRecord` and returns a `Detection` or nothing. `source` is `flowsight`. `score` is 0 to 1. `threshold_used` is the score cut that applied. `label` names the scorer that fired.
- **Minimum evidence.** No Detection until the window holds at least 20 packets (setting).
- **Episodes.** One Detection per Entity per episode, as in the CoverTrace spec: after a flag, nothing more until the Entity has been quiet for one full window, then it can be flagged anew. The gate's one-open-alert-per-Entity rule is unchanged.
- **Step 1, rule-based scorer.** Scores the four window features against settings (small mean size, low spread, short even gaps, high burst share). Replaces the stub. Score is 0 to 1; a Detection is emitted at 0.5 or above. All thresholds are settings.
- **Step 2, classifier.** A logistic regression on the four scaled features, trained with a fixed seed and saved as a model file that FlowSight loads at start. Score is the predicted attack probability. A Detection is emitted at 0.5 or above (setting, reported as `threshold_used`). Same entry point as step 1. A larger model only if measured recall is poor.
- **Gate.** The gate keeps its own threshold (0.7 today). Whether 0.7 is right is for the evaluation spec.
- **Training data.** Windows are built by the same replay path used at run time, from real tool-generated tunnel captures (candidate: CIC-Bell-DNS-EXF-2021, plus the team's own laptop capture) with benign traffic as negatives. CIC-IDS2017 is dropped for FlowSight training: it has no DNS tunneling and its rows are whole flows, not windows. This overturns the dataset spike's recommendation, ADR 0007 wording and decision D8; those need an update.
- **Dataset gate.** Before any download, a human confirms the dataset page: licence, size, real link. Any download over 1 GB needs Ayush's approval. If no real tunnel data is verified by the end of Cycle 2, the classifier is not built and FlowSight stays rule-based.
- **Train and test split.** Split by capture (or by Entity), never by window. Fixed seed. Precision, recall, F1 and AUC are written by the training step as files in the evaluation folder.
- **Settings.** A settings file inside the FlowSight module holds window, burst limit, minimum packets, score cut and the rule thresholds. Safe defaults in code apply when it is missing.
- **Contracts.** No change to `FlowRecord`, `Detection` or `Alert`. `features` is a free map of floats.
- **State.** In memory only. No database or network call inside FlowSight (project rule).
- **Stub.** The stub is deleted when the rule-based scorer lands. The existing pipeline tests that assert one alert on the tunnel Entity and none on the control stay green.
- **Ledger.** FlowSight is Stub today. Partial when the rule scorer is merged and tested. Working for the classifier only with held-out metrics from real captures. Paper 1 numbers are synthetic and never quoted as results of this engine.

## Testing Decisions

- **Good test.** It checks external behaviour only: flows in, does a Detection come out, with what score band, label and features. It never inspects private state or helper functions.
- **One seam.** The FlowSight entry point (one `FlowRecord` in, a `Detection` or nothing out), fed by FlowRecords that `ReplaySource` builds from crafted pcaps. This is the highest existing seam; the pipeline already calls detectors this way. One end-to-end smoke test through the replay pipeline stays.
- **Both tunnel shapes.** One pcap with a tunnel as a single long flow (the demo pcap) and one as many one-packet flows (as in the Cycle 1 pipeline tests). Each fires; a benign human-paced pcap stays quiet.
- **Features.** Hand-computed values on small fixed windows, including the edge cases of an empty window and a single packet. These are small checks of the pure feature functions; they are the one exception to the single seam because the numbers must be exact.
- **Independence.** A flow whose DNS fields change but whose sizes and gaps do not gives the same FlowSight result. This proves FlowSight ignores DNS.
- **Episodes.** After a flag, more traffic raises nothing; after a quiet window the same Entity can be flagged again.
- **Settings.** A missing settings file gives working defaults; a changed number changes behaviour.
- **Classifier.** Training is reproducible: same seed, same metrics. Metrics files exist after a run. Held-out captures are separate from training captures.
- **Prior art.** The replay tests that build pcaps with scapy, the pipeline tests that assert one alert on the tunnel Entity and none on the control, and the CoverTrace detector tests.

## Out of Scope

- CoverTrace, the gate's own logic, MimicNet and closed-loop rules.
- Evaluation harness and datasets beyond what FlowSight training needs (the evaluation spec covers them).
- FlowSight explainability (future work, spec non-goal).
- Live capture, DNS over HTTPS inspection, payload inspection.
- A deep or fused model; the Paper 1 fused classifier stays in the evaluation folder as a baseline (ADR 0002).

## Further Notes

- Design finding from Cycle 1: a tunnel can be one long single-port flow or many one-packet flows, so FlowSight needs per-Entity windows. The demo pcap uses the long-flow shape; the pipeline tests use the many-flow shape.
- Fact from the replay source: a flow is emitted only after it is closed, so a long flow reaches FlowSight late. Fine for replay; a live capture source would need a different hand-off.
- Suggested owner: Bhargav (data and lab pcaps), with Ayush reviewing every PR. Cycle 2 for the entry point, window state, features and rule scorer; Cycle 4 for training and the classifier.
- Suggested tickets (routing by complexity, not size): (1) entry point, window state, episodes, settings, tests for both shapes: Claude, Cycle 2. (2) four feature functions with hand-computed tests: `agy`, Cycle 2, blocked by 1. (3) rule scorer wired in, stub deleted: Claude, Cycle 2, blocked by 1 and 2. (4) verify the real tunnel dataset page, licence and size: human, Bhargav, Cycle 2. (5) window dataset builder and training script with split by capture and metrics: Claude, Cycle 4, blocked by 3, 4 and the real laptop capture ticket. (6) classifier replaces the rule scorer, model file, ledger update: Claude, Cycle 4, blocked by 5. Old tickets #15 and #16 close as superseded.
- Shared-file changes this spec implies, not made here: GLOSSARY (add Window and Episode), a new ADR on per-Entity windows and metadata-only features, ADR 0007 and the data README D8 row, the main spec owner and ledger rows, the report outline, and the contributing owner line.
- Seam check: please confirm the single seam above (the FlowSight entry point fed by replayed crafted pcaps) matches what you expect. If you want a lower seam for the feature maths, say so and the testing section changes.
