# Tickets

Folders: `pending/` → `in-progress/` → `done/` (or `failed/` with reason appended). Format and rules: `CONTRIBUTING.md`.

Each ticket has `## Owner` and `## Cycle`. Cycles are defined in `docs/specs/GkmkbSpec.md` section 9.

## Cycle 1 — Review 2 (2026-10-24)
| Ticket | Owner |
|---|---|
| RepoSkeletonAndCi | Ayush |
| SharedContracts | Ayush |
| AgentsMdAndConventions | Ayush |
| ReplayCaptureSource | Ayush |
| CliReplayAndStubGate | Ayush |
| DnsEntropyDetector | Shivansh |
| DnsTunnelLabPcaps | Bhargav |
| DatasetSpike | Sharukh |
| ReportEthicsAndEvaluationDraft | Sharukh |
| HonestyLedgerAndReview2Slides | Sharukh + Bhargav |
| TeammateSetupVerification | Shivansh, Bhargav, Sharukh |
| ModuleSpecCoverTrace | Shivansh |
| ModuleSpecEvaluationAndMitre | Sharukh |
| ModuleSpecDashboard | Bhargav |
| ModuleSpecBackendFlowSightMimicNet | Ayush |

Cycle 1 rule: every owner hands each ticket's `## Steps` to their agent one step at a time, and runs `/grill-with-docs`, `/to-spec`, then `/to-tickets` for their own next-cycle module. The resulting tickets replace the placeholder tickets below.

## After Review 2
Cycle 2: ComposeStack, BackendPipelineAndGate, WebSocketEventStream, DashboardShell, IcmpTimingChiSquare, HttpHeaderAndProtocolValidation, CoverTraceEvaluation, FlowSightFeatures, FlowSightClassifier.
Cycle 3: HoneypotContainer, MitreMapping.
Cycle 4: AdaptiveBaseline, RuleGenerationFeedback, FingerprintVariation, DashboardViews.
Cycle 5: EndToEndDemoReplay.

Order on the critical path: SharedContracts → ReplayCaptureSource → DnsEntropyDetector → CliReplayAndStubGate. DnsTunnelLabPcaps must land by 2026-10-21 so Shivansh and Ayush can test against it.
