# Evaluation and MITRE Spec

Status: Draft, from the grilling on 2026-10-22 (issue #25). Vocabulary follows `GLOSSARY.md`. Respects ADR 0002 (independent detectors; fused model kept as a baseline), ADR 0003 (gate correlates on Entity and window), ADR 0006 (closed loop, analyst approval), ADR 0007 (datasets and ethics) and ADR 0008 (engine plus CLI is the product). Owner: Sharukh. Every decision here can be changed by Sharukh in a PR; contract changes and shared-file changes need Ayush's review.

## Problem Statement

The team wants to say in the report how well GKMKB finds covert channels. Today it cannot say anything honest. No evaluation code exists. The only numbers near the project are Paper 1's, and those come from synthetic records. The crafted benign pcap has one machine and no hard cases (no CDN hash names, no `.local`, no bursty human traffic), so a false-alarm rate on it would look perfect and mean nothing. The demo control pcap is built so that only one signal fires, so the gate wins on it by design. No tool-generated tunnel traffic exists yet. The MITRE table has no content and no verified technique ids. A panel member can ask "how do you know?" and the team has no answer that survives the question.

## Solution

An evaluation harness replays labelled pcaps through the real detectors and the gate and counts, per Entity, which tunnels were found and which benign machines were wrongly flagged. Every number comes from a seeded script and an output file. Results from crafted pcaps and from real tool-generated captures sit in separate tables and are never mixed. Each percent shows its raw count, because the captures are few.

The harness answers four questions with one table each: how each detector and the gate compare on the same data; whether the learned limit beats the fixed limit; how a retrained Paper 1 model compares on the same data; and how much earlier an approved Rule catches a known attacker. A small, verified MITRE keyword table tags honeypot sessions, and a plain test checks that the table does what it says.

## User Stories

1. As the evaluator, I want hits and false alarms counted per Entity episode, so that one-packet tunnel flows do not inflate the numbers.
2. As the evaluator, I want a hit defined as a tunnel Entity that gets a Detection (or an Alert for the gate), so that the definition is the same in every table.
3. As the evaluator, I want a false alarm defined as a benign Entity that gets a Detection or an Alert, so that wrong flags are counted the same way everywhere.
4. As the evaluator, I want missed tunnels counted too, so that recall is honest.
5. As the evaluator, I want time to first Detection reported, so that speed is part of the story, not only accuracy.
6. As the evaluator, I want a labels file beside every pcap that names each Entity as tunnel or benign, so that ground truth is written by a person and never guessed from detector output.
7. As the evaluator, I want the labels file written by whoever made the capture, so that the label has an owner.
8. As the evaluator, I want crafted results and real tool-generated results in two separate tables, so that synthetic data is never presented as real.
9. As the evaluator, I want every percent to show its raw count next to it, so that a reader sees how small the sample is.
10. As the evaluator, I want tuning on one set and scoring on a different held-out set, so that no number is fitted to itself.
11. As the evaluator, I want splits made by capture, never by window, so that near-identical windows do not leak into the test set.
12. As the evaluator, I want a fixed seed on every script, so that anyone can reproduce a number.
13. As the evaluator, I want no number in the report without a script and an output file behind it, so that the AI-assistance disclosure stays true.
14. As the evaluator, I want precision, recall, F1, AUC and false-alarm rate as small pure functions, so that each can be checked by hand.
15. As the evaluator, I want results saved as CSV files, so that tables and plots can be rebuilt.
16. As the evaluator, I want a ROC plot per detector, so that the threshold trade-off is visible.
17. As the evaluator, I want the harness to use the same replay path as the CLI, so that evaluated behaviour is the behaviour users get.
18. As the evaluator, I want an evaluation set of benign pcaps with CDN-style names, `.local` names and bursty human traffic, so that false alarms are tested on hard cases.
19. As the evaluator, I want the hard benign set labelled "crafted", so that nobody mistakes it for real traffic.
20. As the evaluator, I want at least three tunnel captures per tool (iodine and dnscat2), different in day, domain and payload size, so that the split by capture has something to split.
21. As the evaluator, I want at least three benign captures from consenting team members, so that benign results do not rest on one machine.
22. As the evaluator, I want a consent record for each teammate and each benign capture, so that the ethics section is backed by paper.
23. As the evaluator, I want CIC-Bell-DNS-EXF-2021 used only after a person verifies the page (licence, size, real link), so that no unverified download enters the project.
24. As the evaluator, I want any download over 1 GB approved by Ayush first, so that laptops and quotas are protected.
25. As the evaluator, I want evaluation v1 in Cycle 2 to run on crafted pcaps only and be labelled synthetic, so that the harness is tested before real data exists.
26. As the evaluator, I want CoverTrace alone, FlowSight alone and the gate compared on the same held-out data, so that the benefit of two signals is measurable.
27. As the evaluator, I want the threshold swept, with false alarms shown at equal hits, so that the comparison is fair across thresholds.
28. As the evaluator, I want the gate threshold chosen on the tuning set, not the test set, so that the gate is not tuned to its own exam.
29. As the evaluator, I want the report to say that the crafted control favours the gate by design, so that only the real and hard-benign results count as evidence.
30. As the evaluator, I want the fixed limit (3.5 bits) and the learned limit run on the same traffic, so that the benefit of adaptation is measurable.
31. As the evaluator, I want false alarms on the CDN-style benign set compared at the same hits, so that adaptation is judged where it should help.
32. As the evaluator, I want the Paper 1 fused model retrained on the same features and the same capture split as our engine, so that the baseline is fair.
33. As the evaluator, I want Paper 1's own 96.0% accuracy and 0.970 AUC quoted in one sentence marked "synthetic, from the paper", so that those numbers are cited and never compared with ours.
34. As the evaluator, I want the closed loop measured as flows and seconds to the first Detection, with and without an approved Rule, so that "earlier" is a number.
35. As the evaluator, I want a check that a Rule never fires on benign traffic, so that a bad Rule's cost is visible.
36. As the evaluator, I want a tunnel on a different domain shown as not caught by the Rule, so that the limit of the closed loop is stated.
37. As the evaluator, I want the report to say the attacker script is ours and that a Rule hit scores 1.0 by design, so that the claim is "caught earlier on a known attacker", not "better detection".
38. As an analyst, I want MITRE ATT&CK tags with an evidence line beside each tag, so that I can check why a tag was given.
39. As an analyst, I want behaviour the table does not know to get no tag, so that I am never shown a guess.
40. As Sharukh, I want each table row to carry the technique id, name, keyword, evidence line, source URL and verified date, so that every row can be traced.
41. As Sharukh, I want every technique id checked on attack.mitre.org before it is marked verified, so that no wrong id reaches the report.
42. As Sharukh, I want the table small (about 8 to 10 rows), so that every row can be defended in the viva.
43. As Sharukh, I want tags to come from the honeypot session only, so that the table maps what the attacker did, not what a detector guessed.
44. As a developer, I want the MITRE function to take session events and return tags, so that MimicNet and the harness call it the same way.
45. As a developer, I want the table to be data in one place, so that adding or fixing a row is a one-line change.
46. As a developer, I want the MITRE test to be an exact match on the scripted session, so that a change to the table or the script shows up at once.
47. As the report author, I want the MITRE check described as a table-correctness test and not as "MITRE accuracy", so that the report does not overclaim.
48. As the report author, I want one line per dataset in `data/README.md` (name, licence, citation, URL, date fetched), so that the ethics section is complete.
49. As the report author, I want the evaluation chapter filled from output files and not typed from memory, so that every number has a link.
50. As the report author, I want the limitations listed next to the results (few captures, lab data, replay only), so that the reader sees the limits where the numbers are.
51. As a team lead, I want each harness piece to carry its own ledger row (Designed, Partial, Working), so that the report claims only what exists.
52. As a team lead, I want the evaluation tickets timed to the cycles in which their inputs exist, so that nobody waits on data that is not there.
53. As a team lead, I want ticket routing by complexity, not size, so that simple work goes to `agy` and unclear work goes to Claude.
54. As a privacy-minded reviewer, I want pcaps checked for personal data (hostnames, queried domains, IPs) before they are committed or shown on a slide, so that no real user is exposed.
55. As a viva examiner, I want the definition of a hit, a false alarm and the split written in one place, so that I can test the team's answers against the text.

## Implementation Decisions

- **Unit of count.** Per Entity (source and destination pair, ADR 0003), per Episode (GLOSSARY). Hit: a tunnel Entity gets a Detection from that detector, or an Alert for the gate. False alarm: a benign Entity gets one. Missed: a tunnel Entity gets none. The harness also records time to first Detection per tunnel Entity.
- **Ground truth.** One small labels file per capture, written by the person who made the capture, naming each Entity as tunnel or benign. The harness reads labels and never derives them from detector output.
- **Data sets.** Four kinds, always reported in two groups. Crafted group: the existing lab pcaps plus a new crafted benign set holding CDN-hash names, `.local` and `.arpa` names, and bursty human traffic; every crafted file is labelled "crafted". Real group: the team's own iodine and dnscat2 captures (ticket #49), the team's consented benign captures, and CIC-Bell-DNS-EXF-2021 only after a person verifies the page. CIC-IDS2017 stays dropped (ADR 0007 addendum). The Paper 1 synthetic generator stays a baseline source.
- **Capture counts.** At least three tunnel captures per tool, varying in day, domain and payload size, and at least three benign captures. Needed early in Cycle 4 because the FlowSight classifier also trains on them. If the team can only make fewer, the report says so; fewer is allowed, hiding it is not.
- **Split.** Tune on one set of captures, score on a separate held-out set. Split by capture, never by window. Fixed seed. The gate threshold and every other tunable number are chosen on the tuning set only.
- **Honest-number rules.** (a) Crafted and real results in separate tables. (b) Every percent shows its raw count. (c) Tune and test on different captures. (d) Fixed seed. (e) No number in the report without an `eval/` script and an output file behind it.
- **Metric functions.** Pure functions over lists of per-Entity outcomes: hits, misses, false alarms, precision, recall, F1, false-alarm rate, ROC points and AUC. Each checkable by hand. No framework.
- **Runner.** A command in `eval/` replays labelled pcaps through the real detectors and the gate by the same replay path the CLI uses, collects per-Entity outcomes, and writes CSV files. Run as a module, seeded, reproducible. Evaluation v1 (Cycle 2) uses crafted pcaps only and its output is labelled synthetic.
- **Gate vs single detector.** One table on the same held-out data: CoverTrace alone, FlowSight alone, the gate. Sweep the threshold; show false alarms at equal hits and a ROC curve per detector. Include the hard benign cases. The gate threshold (0.7 today) is chosen on the tuning set. The report states that the crafted control favours the gate by design, so only real and hard-benign results count as evidence.
- **Adaptive vs fixed.** The same traffic through CoverTrace with the fixed 3.5-bit limit and with the learned limit. Compare false alarms on the CDN-style benign set at the same hits. Demo step 7 (same traffic, two baselines, two cutoffs) is shown separately and is not an evaluation number.
- **Paper 1 baseline.** The Paper 1 fused model (logistic regression on its 8 features) is retrained on the same features and the same capture split as the engine, and lives in `eval/` as ADR 0002 requires. Paper 1's own figures (1,000 synthetic records, LR 96.0% accuracy, 0.970 AUC) are quoted in one sentence marked "synthetic, from the paper" and never share a table row with engine results.
- **Closed loop.** Run the scripted attacker session, approve its Rule, then replay the same tunnel with and without the Rule. Measure flows and seconds to the first Detection and the score. Also check that a Rule never fires on benign traffic, and that a tunnel on a different domain is not caught. The claim is "caught earlier on a known attacker". The report states that the attacker script is ours and that a Rule hit scores 1.0 by design (MimicNet spec).
- **MITRE table.** Data kept in one place: each row has technique id, technique name, keyword, evidence line, source URL and verified date. About 8 to 10 rows. Starting rows, all Unverified until Sharukh checks attack.mitre.org: T1071.004 (application layer protocol: DNS), T1572 (protocol tunneling), T1048 (exfiltration over alternative protocol), T1059.004 (unix shell), T1082 (system information discovery), T1083 (file and directory discovery), T1033 (system owner or user discovery), T1105 (ingress tool transfer). Sharukh may add, drop or rename rows. Unknown behaviour returns no tag.
- **MITRE function.** Takes the session events and returns tags, each with its evidence line. Called by MimicNet and by the harness the same way (interface agreed in the MimicNet spec). Tags come from the honeypot session only, not from detector output. Alert-level tags are future work.
- **MITRE check.** An exact-match test on the scripted session plus a no-tag test for an unknown command. The report describes it as a table-correctness test, not as "MITRE accuracy".
- **Ethics and data hygiene.** A consent record for each teammate and each benign capture. Pcaps are checked for personal data (hostnames, queried domains, IPs) before commit or slide use. One line per dataset in `data/README.md`. A person verifies the CIC-Bell page before any download; downloads over 1 GB need Ayush's approval.
- **Contracts.** No change to `FlowRecord`, `Detection`, `Alert` or `Rule`. The harness only reads them.
- **Ownership.** Sharukh owns evaluation and MITRE and the code in the evaluation folder. Ayush reviews every PR. `GkmkbSpec.md` currently puts that folder under M4 (Ayush); see Further Notes.
- **Cycles.** Cycle 2: labels file, crafted benign set, metric functions, runner v1 on crafted data, consent record, dataset page check. Cycle 3: MITRE table, function and id verification. Cycle 4: Paper 1 baseline retrained, after the real captures exist. Cycle 5: gate sweep, adaptive vs fixed, closed-loop run, report chapter.
- **Routing (complexity decides, not size).** To `agy`: crafted benign set and labels file, metric functions, MITRE table and function. To Claude: runner, Paper 1 baseline, gate sweep, adaptive vs fixed, closed-loop script. Human tasks (no agent label): consent record, dataset page check, MITRE id verification, report chapter.

## Testing Decisions

- **Good test.** It checks external behaviour only: given outcomes or sessions in, what numbers or tags come out. It never reads private state or helper functions.
- **Metric functions.** Hand-computed values on tiny fixed lists, including empty lists, all-hit, all-miss and single-class cases (AUC undefined). These are the one exception to a single seam because the numbers must be exact.
- **Runner seam.** One seam: the runner command on small crafted pcaps with a labels file gives the expected CSV (hit and false-alarm counts per detector and for the gate). The same seed gives byte-identical output. A missing labels file fails with a clear message.
- **Honesty.** A test checks that crafted and real results are written to separate files and that every percent row carries a count column.
- **Held-out.** A test that the tuning set and the test set share no capture.
- **MITRE.** Exact-match test on the scripted session; no tag for an unknown command; every table row has all required fields; a row with no verified date is marked Unverified in the output.
- **Closed loop.** Reuses the CoverTrace seam: with an approved Rule the first Detection arrives earlier; with a proposed or rejected Rule it does not change; benign traffic gives no Rule hit.
- **Not unit-tested.** The report chapter and real-capture results; they are checked by hand against output files.
- **Prior art.** The gate unit tests, the CoverTrace and FlowSight replay tests built with scapy, and the pipeline tests that assert one alert on the tunnel Entity and none on the control.

## Out of Scope

- The detectors, the gate logic, MimicNet and the Console themselves; this spec only measures them.
- Live capture, DNS over HTTPS, and any dataset beyond those listed.
- A claim of general accuracy on real networks; results are lab results.
- Alert-level MITRE tags (tags from detector output).
- A new fused or deep model; only the Paper 1 baseline is retrained.
- Statistical significance tests beyond raw counts next to percents.
- Writing the report text (a human task from the output files).

## Further Notes

- **Shared files not edited. Needed changes for Ayush:**
  - `GkmkbSpec.md` section 7: add the per-Entity counting rule, the crafted vs real split and the MITRE row. Section 3: say Sharukh owns the code in the evaluation folder and Ayush reviews.
  - `Ledger.md`: add rows for the evaluation harness pieces, the retrained Paper 1 baseline and the MITRE table, all Designed.
  - `GLOSSARY.md`: add Hit, False alarm and Held-out set.
  - ADR 0007 and `data/README.md`: add the extra crafted benign set, the consent record and the CIC-Bell page check.
  - `docs/report/ReportOutline.md` section 5: add the tune-and-test-apart rule and the crafted vs real split; drop the "blocked by #10 and #12" line if those are closed.
- **Stale tickets.** #7 (CoverTrace evaluation harness) and #21 (MITRE tagging with verified table) are replaced by the tickets from this spec and close as superseded. #25 closes when this spec merges. The dataset page check duplicates #52; link to it, do not recreate it. The real-capture ticket is #49 and the closed-loop inputs are #58.
- **Dependencies.** The gate sweep needs the real FlowSight (#54 to #56). Adaptive vs fixed needs the learned normal from the CoverTrace tickets. The closed-loop script needs CoverTrace rule loading (#58). The Paper 1 baseline needs the real captures (#49).
- **Honesty.** No evaluation number exists today and none may be quoted until a script and an output file exist.
- **Seam check.** Two seams: pure metric functions (exact numbers, hand-computed) and the runner command on small crafted pcaps. Please confirm this matches what you expect. If you want only one, the metric functions are tested through the runner and the testing section changes.
