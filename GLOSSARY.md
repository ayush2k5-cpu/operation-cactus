# GKMKB Glossary

One word, one meaning. Use these terms in code, tickets, PRs and the report.

| Term | Meaning |
|---|---|
| **GKMKB** | Guarded Kill-chain Monitoring & Key Breach. The whole platform. |
| **Kill-chain** | Attacker stages from probe to exfiltration. GKMKB watches the covert-channel and exfiltration stages and traps the probe stage. |
| **Key Breach** | Exfiltration of secrets or data through a covert channel (e.g. credentials leaving by DNS tunnel). Decided 2026-10-20. |
| **Engine** | The headless detection pipeline (capture source, detectors, gate, MimicNet hooks). The product. Driven by the `gkmkb` CLI and wrapped by the backend. |
| **Console** | The web dashboard. A viewer over the backend, not the product. |
| **Replay** | Feeding a stored pcap through the pipeline as if it were live. The only traffic source for the demo. |
| **Capture source** | Component that turns packets into `FlowRecord`s. Today: `ReplaySource`. |
| **FlowRecord** | One network flow with metadata-only statistics, plus optional extracted DNS queries, ICMP timestamps and HTTP header names. Defined in `contracts/`. |
| **Entity** | The pair `(src_ip, dst_ip)`. The unit the gate correlates on. |
| **FlowSight** | Detector for statistical flow behavior. Reads metadata only, so it works on encrypted traffic. |
| **CoverTrace** | Detector for covert channels using entropy, chi-square timing and protocol validation. Flagship module. |
| **Detection** | One detector's verdict on one flow: `source`, `entity`, `score` (0 to 1), `label`, `features`. |
| **Gate** | Backend component that raises an `Alert` only when FlowSight and CoverTrace both emit a Detection at or above threshold for the same entity inside the correlation window. |
| **Alert** | Gate output. Escalates to MimicNet. A single-signal Detection is stored but never an Alert. |
| **MimicNet** | Response layer. Runs a Docker honeypot for an Alert and records the session. |
| **Honeypot session** | One attacker interaction recorded by MimicNet: events, MITRE mapping. |
| **Rule** | Detection rule generated from a honeypot session and fed back to FlowSight or CoverTrace. States: `proposed`, `approved`, `active`, `rejected`. |
| **Baseline** | Rolling per-network statistics CoverTrace uses to set adaptive thresholds. |
| **Adaptive threshold** | Entropy or chi-square cutoff computed from the Baseline instead of a fixed constant. |
| **Walking skeleton** | Thinnest end-to-end path (replay → detectors → gate → API → dashboard) with stub internals. Built first. |
| **Designed / Partial / Working** | Honesty labels. *Designed*: on paper only. *Partial*: runs but not evaluated or not complete. *Working*: merged, tested, demonstrable. Reports use these words exactly. |
