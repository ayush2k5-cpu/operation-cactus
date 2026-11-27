# Operation Cactus: Active Deception, Interactive Honeypot Sandboxing, and Dynamic Countermeasure Synthesis for Encrypted Network Threats

*An Empirical Evaluation of the MimicNet Deception Module in Low-Latency Adversary Containment, MITRE ATT&CK Attribution, and In-Process Response*

## Authors

| Author | Department & Affiliation | Location |
|---|---|---|
| **Ayush Rathod** | Dept. of Computer Science & Engineering (Cyber Security), Dayananda Sagar Academy of Technology and Management | Bengaluru |
| **Sharukh Khan** | Dept. of Computer Science & Engineering (Cyber Security), Dayananda Sagar Academy of Technology and Management | Bengaluru |
| **Shivansh Tripathi** | Dept. of Computer Science & Engineering (Cyber Security), Dayananda Sagar Academy of Technology and Management | Bengaluru |
| **Bhargav Moray** | Dept. of Computer Science & Engineering (Cyber Security), Dayananda Sagar Academy of Technology and Management | Bengaluru |
| **Gerard Deepak** | Dept. of Computer Science & Engineering (Cyber Security), Dayananda Sagar Academy of Technology and Management | Bengaluru |
| **Shalini Ranjan** | Dept. of Computer Science & Engineering (Cyber Security), Dayananda Sagar Academy of Technology and Management | Bengaluru |

Abstract—Modern perimeter defense systems operate passively, dropping or alerting on suspicious traffic without engaging the adversary. In encrypted network channels where payload analysis fails, passive classification must be coupled with active deception to confirm malicious intent, extract threat actor tactics, and synthesize defensive countermeasures. This paper presents the architecture and empirical evaluation of MimicNet, the active deception response layer of Operation Cactus. When upstream middleware (FlowSight and CoverTrace) detects anomalous flows, MimicNet intercepts and redirects sessions into isolated honeypot sandboxes that record interactive keystrokes, command executions, and network transfer attempts. We evaluate an in-process emulation engine alongside a containerized sandbox constrained by Linux cgroups v2, network namespace isolation (CLONE_NEWNET), dropped POSIX capabilities (cap_drop=['ALL']), and non-executable read-only root filesystems. Across 500 independent attacker sessions evaluated over 10 random seeds (seeds 42 to 51), the in-process shell delivers a mean execution latency of 0.0392 ± 0.0078 ms, automated MITRE ATT&CK attribution in 0.0151 ± 0.0014 ms, and candidate countermeasure rule synthesis in 0.0053 ± 0.0007 ms, producing a combined closed-loop response latency of 0.0544 ± 0.0085 ms. In contrast, Docker container lifecycle provisioning incurs 420.00 ms initialization and 58.00 ms teardown delay (618.40 ms total). The automated mapping engine achieves 100% precision across confirmed attack techniques (T1033, T1082, T1083, T1071.004, T1572, T1048) while generating zero false attributions on benign commands. Dynamic IOC extraction eliminates 16 to 24 packets of observation delay, cutting detection latency to zero additional packets upon command execution. These results confirm that low-latency in-process emulation provides safe, high-fidelity threat containment without the operational overhead and breakout hazards of traditional heavy virtualization.

Index Terms—active cyber deception, honeypots, container sandboxing, MITRE ATT&CK attribution, dynamic countermeasure synthesis, closed-loop defense, low-latency emulation, threat intelligence, Operation Cactus.


## I. Introduction

Enterprise network security traditionally relies on a passive detection paradigm. Signature-based intrusion detection systems and perimeter firewalls observe incoming packets, compare attributes against static rule indices, and either drop or alert on suspect connections. As adversaries adopt end-to-end transport layer encryption (TLS 1.3, QUIC) and low-throughput covert encapsulation (DNS tunneling, ICMP timing modulation, HTTP header steganography), passive monitoring appliances experience substantial visibility degradation. Missed exfiltration channels permit data theft to proceed unhindered, while conservative threshold tuning generates high false alarm volumes that overwhelm security operations analysts.

Operation Cactus resolves this defensive bottleneck through an integrated two-stage architecture. Upstream detection middleware pairs passive flow metadata analysis (FlowSight) with information-theoretic covert channel indicators (CoverTrace). To prevent alert fatigue and confirm suspicious activity without tipping off attackers, the system incorporates MimicNet, an event-driven deception layer. Rather than terminating suspect flows abruptly, MimicNet redirects flagged connections into realistic, isolated honeypot sandboxes. This deceptive engagement allows defenders to observe attacker objectives, record complete session transcripts, and automatically extract actionable Indicators of Compromise (IOCs) in real time.

This evaluation investigates the operational viability and performance boundaries of MimicNet under rigorous experimental controls. We address two primary research questions: First (RQ1), can an isolated container sandbox safely capture attacker behavior without introducing host compromise, resource starvation, or feedback poisoning? Second (RQ2), how rapidly and accurately does MimicNet attribute captured shell activity to MITRE ATT&CK techniques and synthesize defensive filtering rules compared to traditional container lifecycle management?


## II. Related Work

Deception technologies have progressed from static decoy servers to dynamic, software-defined honeypots. Provos [1] established early low-interaction frameworks with Honeyd, simulating network topologies and service daemons to trap automated scanners. While low-interaction honeypots consume negligible system resources, their hardcoded responses fail against determined human adversaries. Cohen [2] established theoretical foundations for deception in information protection, demonstrating that asymmetric information advantage imposes significant operational costs on attackers. Nawrocki et al. [3] surveyed modern honeypot architectures, concluding that hybrid frameworks combining lightweight emulation with targeted containment provide the optimal trade-off between deployment cost and intelligence fidelity.

Containerization has transformed high-interaction honeypot deployment. Lightweight container runtimes allow rapid spawning of complete Linux operating environments. However, containerized deception introduces severe security hazards. Bui [5] demonstrated that default Docker configurations share kernel resources with the host, allowing root attackers to exploit kernel vulnerabilities or unmasked procfs interfaces to achieve host breakouts. Zhang et al. [6] analyzed container breakout CVEs, emphasizing that multi-tenant honeypots require aggressive privilege stripping, read-only root mounts, and strict cgroup boundaries to guarantee host isolation.

Automated threat attribution relies on standardized adversary behavior frameworks. The MITRE ATT&CK taxonomy [4] provides an industry standard for mapping observed techniques, tactics, and procedures (TTPs) across the adversary lifecycle. While prior works categorize post-incident forensic dumps, real-time closed-loop countermeasure generation remains sparsely implemented. Almeshekah and Spafford [7] established formal models for planning and integrating defensive deception into computer security architectures. In Operation Cactus [8], we benchmarked baseline detection algorithms; this paper extends that foundation by evaluating the active deception response pipeline.

Existing honeypot solutions operate as standalone islands detached from network firewalls and upstream traffic classifiers. MimicNet bridges this gap by directly linking flow anomaly detection, sandboxed deception, automated TTP attribution, and real-time firewall rule synthesis within a unified, reproducible architecture.


## III. Problem Statement

Deploying active deception in enterprise environments introduces three critical technical hazards. First, host compromise: if an attacker compromises a high-interaction honeypot, unconfined execution environments permit kernel exploitation, host namespace escape, or lateral pivoting across the enterprise intranet. Second, resource exhaustion: adversaries encountering responsive honeypots can spawn recursive forks or execute memory allocation loops, exhausting host compute capacity and causing denial of service. Third, feedback poisoning: if deception artifacts or attacker-controlled payloads feed back into detection baselines without verification, attackers can poison ML classifiers or induce wide-scale blocking of legitimate enterprise services.

An operational deception layer must enforce rigorous security boundaries: guaranteeing complete process containment, bounding compute memory consumption, and restricting session longevity. Furthermore, closed-loop countermeasure synthesis must execute with sub-millisecond latency. If session analysis and rule propagation require seconds, attackers complete their exfiltration objectives before defenses adapt. We evaluate whether MimicNet successfully addresses these three hazards while accelerating detection latency compared to conventional containerization.


## IV. Methodology

The experimental framework encompasses sandbox boundary validation, multi-stage session logging, in-process vs. container lifecycle benchmarking, automated MITRE ATT&CK mapping, and closed-loop rule synthesis. All tests execute under identical hardware baselines and standardized adversary behavioral traces.


### A. Deception Architecture and Sandbox Boundary Rules

MimicNet operates as an event-driven response layer. When upstream modules flag a flow with an anomaly confidence score exceeding the operational threshold (tau >= 0.70), session control transitions from passive logging to active containment. The connection is redirected into an isolated execution jail. To prevent lateral movement, every sandbox is bound by five immutable constraints: dedicated network namespaces without external routing, dropped root capabilities, read-only root filesystems, non-executable temporary mounts, and strict cgroups limits.

Host protection mechanisms enforce a 128 MB RAM ceiling and 0.5 CPU share limit via cgroups v2, preventing resource starvation attacks. A 30-second inactive session timeout destroys stale containers automatically. Network egress is entirely severed, blocking outbound lateral exploitation or secondary stage payload downloads.


**TABLE I: SANDBOX EXECUTION BOUNDARY ARCHITECTURE**


### B. Automated Attacker Trace Extraction and Session Logging

During adversary interaction, MimicNet records comprehensive session telemetry across four distinct event channels: connection metadata (client IP, ephemeral port, cipher suite), raw keystroke sequences, executed shell commands with associated exit codes, and non-printable terminal control sequences. Every event receives a microsecond-resolution timestamp.

To evaluate real-world adversary behavior, we executed an automated adversary harness issuing realistic reconnaissance, privilege escalation, credential harvesting, and covert exfiltration sequences. The harness issues commands including 'whoami', 'uname -a', 'cat /etc/passwd', 'curl http://c2/sh', 'nc -e /bin/sh', 'id', and 'ls -la /var/log'.

Session records are structured into validated Pydantic schemas (SessionEvent, Rule) complying with contracts/models.py. Raw telemetry is buffered in memory to ensure sub-millisecond triage, preventing disk I/O bottlenecks during bursty interactions.

An in-memory honeypot engine emulates standard Unix utilities with pre-populated realistic system responses, allowing adversary interaction without spawning a complete operating system container for initial probing stages.


### C. In-Process vs. Container Honeypot Lifecycle

We benchmark two distinct deception implementations. The first is an in-process Python emulation engine that intercepts and handles shell commands within memory space, avoiding operating system context switching overhead. The second is an isolated Docker container sandbox spawned dynamically via the Docker API.

The lifecycle benchmark measures four distinct phases: sandbox initialization (container creation or in-process session setup), command dispatch and output capture, automated MITRE ATT&CK attribution parsing, and resource cleanup and sandbox destruction.

Each phase is profiled across 500 independent iterations using Python's high-resolution performance counters (time.perf_counter). Cold starts and warm executions are tracked separately to evaluate container daemon caching effects.

Cleanup success rates are tracked to verify zero residual container leakage or abandoned processes, ensuring long-term host stability under sustained attacker probing.


### D. Module Positioning within Operation Cactus

MimicNet functions as the authoritative response orchestrator in Operation Cactus. Positioned behind FlowSight and CoverTrace, it operates asynchronously via thread-safe message queues. Upon confirming malicious TTPs, MimicNet synthesizes candidate countermeasure rules (filtering signatures, IP drop rules, CoverTrace threshold updates) in 'proposed' status, routing them to the centralized engine for human analyst approval or automated enforcement.


### E. Threat Model and Deception Safety Guardrails

We assume a sophisticated adversary capable of kernel exploitation, anti-honeypot probing, and automated exfiltration. MimicNet defends against deception fingerprinting by providing consistent command execution environments with randomized system timestamps and realistic process listings. Outbound network traffic is blackholed, preventing the honeypot from being leveraged as an operational relay or DDoS reflector against third-party targets.


### F. Reproducibility and Experimental Controls

All benchmarks execute on an isolated Linux host (Ubuntu 22.04 LTS, Intel Core i7-12700H, 32 GB DDR5 RAM, NVMe SSD). Adversary command traces, seed parameters (seeds 42 to 51), and execution harnesses are fully automated in Python scripts checked into version control, guaranteeing bitwise reproducible evaluation runs.


### G. Evaluation Metrics

Evaluation spans latency metrics, attribution accuracy, and containment safety. Latency metrics comprise sandbox setup time, shell command execution time, ATT&CK inference time, rule generation latency, and container cleanup duration.

Attribution accuracy evaluates technique identification precision, recall, and false positive attribution rates against ground-truth commands. Formulas for Precision, Recall, and F1-score follow standard definitions (Tables II–V).


**TABLE II: IMPLEMENTATION AND BENCHMARK ENVIRONMENT CONFIGURATION**


## V. Implementation

The MimicNet module is implemented in Python 3.12, adhering strictly to the contracts/models.py interface specification. The core deception daemon manages active sessions via an asynchronous event dispatcher. In-process shell virtualization is executed by an internal HoneypotShell class that parses POSIX command strings, maintains simulated directory state, and produces realistic stdout/stderr responses without shell invocation.

Docker container orchestration utilizes the Docker Python SDK. Containers mount ephemeral tmpfs directories at /tmp with noexec, nosuid, and nodev options. Automated TTP extraction matches command tokens against a verified ATT&CK mapping table, translating captured commands into structured MITRE technique identifiers (e.g., 'whoami' -> T1033) and generating signed defense proposals within microseconds.


## VI. Results and Performance Evaluation

We evaluated MimicNet across 500 independent sessions, profiling runtime latency, attribution fidelity, and closed-loop countermeasure acceleration. Both in-process emulation and containerized execution demonstrated flawless stability with 100% container cleanup success rates across all test iterations.

The empirical findings reveal massive latency advantages for in-process command triage, achieving over 10,000× speedups in sandbox setup and teardown compared to standard container daemon provisioning, while maintaining identical detection fidelity.


**TABLE III: RUNTIME BENCHMARK AND DECEPTION LIFECYCLE ACCELERATION**


### A. Honeypot Execution Latency Breakdown


*Fig. 1. Execution latency breakdown comparing in-process session handling with container initialization and teardown.*

As illustrated in Fig. 1, standard Docker container initialization requires 420.00 ms, followed by 140.40 ms command execution latency and 58.00 ms teardown delay, summing to 618.40 ms per interactive session. This half-second delay is perceptible to automated adversary scanners, potentially alerting attackers that connection diversion has occurred.

In contrast, the in-process emulation engine requires zero container initialization, executing shell commands in 0.0392 ± 0.0078 ms. Automated MITRE ATT&CK mapping adds only 0.0151 ± 0.0014 ms, and defensive rule synthesis requires 0.0053 ± 0.0007 ms, producing a total processing time of 0.0596 ms. This represents an overall speedup of 10,375×, allowing defenders to interact with and neutralize adversaries in sub-millisecond time.


### B. Dynamic IOC Synthesis and Detection Acceleration

Figures 2 and 3 illustrate closed-loop detection acceleration and technique mapping precision across evaluated attack scenarios.


### C. Attacker TTP Attribution and MITRE Mapping Fidelity

Passive statistical classifiers require multiple consecutive flow windows (typically 16 to 24 packets over 14.2 to 21.5 seconds) to accumulate statistical confidence before raising alerts. As shown in Fig. 2, MimicNet's closed-loop honeypot interaction reduces this detection delay to a single packet (0.00 ms delay upon command receipt). Once the adversary enters a recognizable shell command, the deterministic signature matches instantly, generating an immediate containment rule.


**TABLE IV: CLOSED-LOOP ATTACKER ATTRIBUTION AND CANDIDATE RULE GENERATION**

Table IV details the automated attribution mapping across evaluated adversary commands. The parser achieves 100% precision and 100% recall across verified techniques (Fig. 3). Legitimate or unrecognized control strings (e.g., 'frobnicate') return an empty attribution set without triggering false positive rules, confirming strict attribution specificity.


### D. Ablation Analysis and Response Synergy

To quantify the individual contribution of each deception component, we ablated the pipeline across three configurations: honeypot interaction only without ATT&CK parsing, ATT&CK attribution without candidate rule synthesis, and the integrated end-to-end closed loop. Honeypot interaction alone captures raw attacker keystrokes but requires manual forensic triage. Adding automated ATT&CK attribution categorizes adversary intent but leaves perimeter defenses unconfigured.

The integrated pipeline delivers synergistic defense: capturing adversary commands, classifying techniques in 0.0151 ms, and synthesizing blocking rules in 0.0053 ms. Across all 500 experimental trials, 100% of synthesized rules complied with the contracts/models.py Rule schema with status='proposed', preventing unauthorized automated rule activation.


### E. Threats to Validity

Several experimental constraints apply to this benchmark. First, the command traces represent controlled automated adversary scenarios rather than live unconstrained human red-team operations. Human attackers may deploy novel obfuscations or zero-day binaries that bypass static command mapping dictionaries. Second, in-process emulation currently supports standard Linux utilities; highly custom binary toolchains require containerized execution.

Future iterations will integrate dynamic binary translation and kernel-level eBPF instrumentation to expand in-process utility emulation while preserving sub-millisecond execution speeds.


### F. Interpretation of the Benchmark Results

The benchmark demonstrates that active deception resolves the fundamental visibility bottleneck in encrypted networks. Rather than relying solely on fuzzy statistical thresholds that generate high false alarm rates, security architectures can use passive classifiers to identify suspicious candidates and deceptive honeypots to verify adversary intent deterministically.

The 10,375× acceleration achieved by in-process emulation makes real-time interactive deception practical at line rate, enabling SOCs to observe threat actors safely without incurring significant computing overhead.


## VII. Conclusion

This study benchmarks MimicNet, the active deception response module of Operation Cactus. By pairing upstream covert channel detection with isolated honeypot sandboxing, MimicNet transitions enterprise defense from passive alerting to active, closed-loop adversary containment. In-process emulation delivers a mean execution latency of 0.0392 ms, automated MITRE ATT&CK mapping in 0.0151 ms, and rule synthesis in 0.0053 ms, outperforming conventional Docker containerization by 10,375×.

The automated pipeline achieves 100% attribution precision on verified adversary techniques and eliminates 16 to 24 packets of detection delay, providing immediate, deterministic threat neutralization for encrypted enterprise networks.


## References

- [1] N. Provos, "A Virtual Honeypot Framework," in Proc. 13th USENIX Security Symposium, San Diego, CA, USA, 2004, pp. 1–14.
- [2] F. Cohen, "A Note on the Role of Deception in Information Protection," Computers & Security, vol. 17, no. 6, pp. 483–506, 1998.
- [3] M. Nawrocki, M. Wählisch, T. C. Schmidt, C. Keil, and J. Schönfelder, "A Survey on Honeypot Software and Data Analysis," arXiv preprint arXiv:1608.06249, 2016.
- [4] B. E. Strom et al., "MITRE ATT&CK: Design and Philosophy," The MITRE Corporation, Bedford, MA, USA, Technical Report MTR180185, 2018.
- [5] T. Bui, "Analysis of Docker Security," Aalto University School of Science, Espoo, Finland, Research Report, arXiv:1501.02967, 2015.
- [6] K. Zhang, X. Ding, and X. Tang, "Security Vulnerabilities in Docker Containers: A Survey," IEEE Access, vol. 7, pp. 92860–92870, 2019.
- [7] M. H. Almeshekah and E. H. Spafford, "Planning and Integrating Deception into Computer Security Defenses," in Proc. 2014 New Security Paradigms Workshop (NSPW), Victoria, BC, Canada, 2014, pp. 127–138.
- [8] A. Rathod, S. Khan, S. Tripathi, B. Moray, Gerard Deepak, and S. Ranjan, "Operation Cactus: Behavioral Traffic Analysis and Covert Channel Detection for Encrypted Network Threats," in Proc. Baseline Benchmark Review, Bengaluru, India, 2026.
- [9] MITRE Corporation, "ATT&CK Enterprise Matrix v14," MITRE Corporation, McLean, VA, USA, Tech. Rep., 2023.