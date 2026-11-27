# Operation Cactus: Active Deception, Interactive Session Telemetry, and Closed-Loop Threat Feed Synthesis for Covert Network Exfiltration

**An Empirical Evaluation of the MimicNet Deception Architecture, Container Isolation Constraints, and MITRE ATT&CK Mapping**

| **Ayush Rathod**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* | **Sharukh Khan**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* | **Shivansh Tripathi**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* |
|:---:|:---:|:---:|
| **Bhargav Moray**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* | **Gerard Deepak**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* | **Shalini Ranjan**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* |

---

## Abstract
Operation Cactus pairs passive traffic analysis with an active deception subsystem, MimicNet, to contain and profile covert exfiltration sessions that bypass traditional perimeter defenses. When the detection pipeline flags an anomalous entity, MimicNet engages the suspect connection by spawning an isolated, ephemeral sandbox environment. This paper evaluates the architectural containment, runtime performance, and closed-loop threat feed synthesis of the MimicNet response engine. The sandbox enforces strict isolation boundaries: zero external network egress (`network_mode="none"`), an absolute 128 MB memory limit, a 0.5 CPU quota, complete Linux capability revocation (`cap_drop=["ALL"]`), and a 120-second hard watchdog timer. We evaluate session telemetry across 500 benchmark runs of a scripted reconnaissance and DNS tunneling trace modeled on standard post-compromise activity (`whoami`, `uname -a`, `cat /etc/passwd`, `iodine -f t.example.test`). The in-process shell emulator processes the complete interactive dialogue in an average of 0.0392 ms (standard deviation 0.0078 ms), while an automated keyword extraction engine maps typed commands to canonical MITRE ATT&CK enterprise techniques in 0.0151 ms with zero false attribution on unmapped inputs. From completed sessions, MimicNet synthesizes candidate detection rules in 0.0053 ms. Under a human-in-the-loop governance model, analyst approval promotes these rules into active CoverTrace filters, cutting re-detection latency from multi-packet sliding statistical windows down to immediate single-packet deterministic matching (0 ms algorithmic delay). Mutual exclusion locking prevents resource starvation by restricting active sandboxes to one per host, rejecting concurrent alerts within 0.002 ms. These empirical findings demonstrate that lightweight, resource-bounded container deception captures vital post-compromise intelligence without risking host stability or pipeline throughput.

*Index Terms*—cyber deception, honeypots, container sandboxing, covert channel containment, MITRE ATT&CK mapping, closed-loop threat intelligence, incident response.

---

## I. Introduction
Perimeter network defenses traditionally rely on dropping or resetting suspicious connections. While immediate blocking prevents direct data transfer, it provides security analysts with zero visibility into adversary intent, operational tools, or subsequent compromise stages. Furthermore, in environments where transport-layer encryption conceals application payloads, initial detection signals frequently carry operational uncertainty. Severing connections based solely on statistical anomalies risks disrupting legitimate business workflows.

Operation Cactus addresses this operational dilemma through an integrated two-stage defensive architecture:
1. **Detection Middleware (FlowSight and CoverTrace):** Monitors passive flow statistics and protocol-level covert channel indicators without inspecting encrypted payloads, as established in our initial baseline study [8].
2. **Deception Response Layer (MimicNet):** Dynamically redirects suspicious sessions into a locked-down, interactive decoy container instead of terminating the connection.

This architecture changes the defensive calculus. Benign sessions flagged by false positives interact with an emulated service without data loss or terminal disruption. Malicious actors, conversely, believe their compromise succeeded and proceed to execute reconnaissance and covert tunneling commands within a controlled observation environment.

We investigate two empirical research questions in this study:
- **RQ1:** Can an ephemeral containerized sandbox capture interactive adversary telemetry while strictly bounding host memory, compute resources, and network egress risks under strict operational concurrency limits?
- **RQ2:** How rapidly and reliably can interactive honeypot session events be transformed into verified MITRE ATT&CK technique tags and actionable Indicators of Compromise (IoCs) to accelerate subsequent detection cycles?

This paper presents the formal specification, security boundaries, and empirical performance benchmarks of the MimicNet subsystem under controlled lab testbed conditions.

---

## II. Related Work
Honeypots and cyber deception systems have evolved from static decoy daemons into dynamic virtualization environments. Provos introduced Honeyd, demonstrating that virtual honeypots simulating multiple network topologies could profile unauthorized network scans at scale [1]. Cohen established the formal theoretical basis for cyber deception, showing that misleading attackers alters the economics of intrusions by forcing adversaries to expend resources verifying system authenticity [2]. Modern honeypots operate across varying interaction levels, ranging from low-interaction banner grabbers to high-interaction virtual machines [3].

Containerization has significantly reduced the deployment overhead of high-interaction decoys. Bui demonstrated that Linux containers provide lightweight isolation suitable for security testing, provided cgroups and namespace constraints prevent privilege escalation [5]. Al-Daeef et al. cataloged container sandbox escape vectors, emphasizing that unrestricted kernel capability sets, shared socket mounts, and writable root filesystems represent critical operational risks in container honeypots [6]. MimicNet incorporates these lessons by enforcing complete capability stripping (`CAP_DROP=ALL`), read-only root mounts, and disconnected network namespaces.

Standardizing post-compromise telemetry is essential for threat intelligence. Strom et al. designed the MITRE ATT&CK framework to catalog adversarial tactics, techniques, and procedures (TTPs) based on real-world observations [4]. Recent research by Krupski, Graniszewski, and Szczypiorski (StegShield) explored deceptive techniques specifically targeted at covert channel exfiltration [7]. Our work builds upon these foundations by coupling interactive session capture directly with automated, evidence-backed ATT&CK tagging and human-in-the-loop rule synthesis.

---

## III. Problem Statement
Deploying automated deception mechanisms in enterprise environments introduces three primary engineering risks:
1. **Host Compromise and Containment Failure:** If an adversary compromises the decoy service, unrestricted container environments could allow lateral network traversal or local kernel privilege escalation.
2. **Resource Exhaustion (Denial of Service):** Spawning unconstrained virtualization instances for incoming security alerts can rapidly exhaust host CPU, memory, and process tables.
3. **Automated Feedback Poisoning:** Automatically converting untrusted honeypot artifacts into operational firewall rules without analyst validation risks self-inflicted denial of service.

MimicNet solves these challenges through strict isolation invariants, mutual-exclusion engagement locks, and an analyst-in-the-loop rule approval lifecycle. This paper benchmarks the computational latency, resource containment, technique mapping fidelity, and re-detection acceleration of the implemented MimicNet pipeline.

---

## IV. Methodology

### A. Deception Architecture and Sandbox Containment Model
MimicNet operates as an event-driven response module downstream of the correlation gate. When an Alert reaches the `open` state, the backend invokes `engage` to initialize an observation environment.

#### Container Boundary Rules and Resource Caps
To eliminate escape and resource starvation risks, every container instance is configured with five mandatory operational constraints:
- **Network Isolation:** Configured with `network_mode="none"`. The container possesses no external network interfaces, preventing outbound command-and-control, data exfiltration, or lateral network traversal.
- **Memory Ceiling:** Memory consumption is strictly hard-capped at 128 MB (`mem_limit="128m"`). Any process attempting to allocate beyond this boundary triggers immediate container termination.
- **CPU Quota:** Throttled to 0.5 logical cores (`nano_cpus=500000000`), preventing compute starvation of host detection pipelines.
- **Capability Revocation:** All Linux kernel capabilities are completely dropped (`cap_drop=["ALL"]`). The container filesystem is mounted strictly read-only (`read_only=True`), preventing persistence mechanisms, binary drops, or filesystem tampering.
- **Zero Host Mounts:** No host volumes, sockets (specifically `/var/run/docker.sock`), or sensitive paths are mounted into the container.

#### Concurrency Locks and Execution Lifecycles
Host stability requires strict concurrency control. MimicNet implements a process-level mutual exclusion lock (`_running = threading.Lock()`). Exactly one container session may execute at any given time. Any secondary Alert arriving while a session is active is rejected with an `EngageBusy` exception.

Every session is protected by a 120-second watchdog timer (`max_life_s = 120`). If an attacker remains connected or stalls execution, the runtime forcefully issues `SIGKILL` to the container and appends a `timeout` record to the session log. In all execution paths (normal exit, timeout, or uncaught exception), a `finally` block executes `container.remove(force=True)`, guaranteeing that no orphaned containers or lingering state remain on the host.

### B. Interactive Emulation and Session Telemetry Capture
Inside the sandbox, MimicNet executes an interactive shell emulator (`SshLikeShell`) written exclusively in standard Python libraries. This avoids external dependencies and permits identical execution in both containerized environments and in-process test harnesses.

The shell displays an authentic initial banner (`SSH-like service (lab honeypot, not SSH)`) and simulates common UNIX utility responses (`whoami`, `id`, `uname -a`, `pwd`, `ls`, `cat /etc/passwd`). Commands are logged as structured JSON objects containing timestamps, event types, and payload metadata:
- `connect`: Records the remote attacker IP address, timestamp, and active service banner.
- `command`: Captures the raw input string typed by the actor and the corresponding emulated stdout reply.
- `disconnect`: Records clean termination via standard exit commands (`exit`, `logout`) or script exhaustion.
- `timeout`: Appends an explicit timeout marker if the session reached the maximum duration limit.

### C. Automated Threat Attribution and MITRE ATT&CK Mapping
Upon session completion, the telemetry log is ingested by `tag_events()` in `eval/mitre.py`. The engine matches typed command strings against a curated mapping table verified against canonical definitions on `attack.mitre.org`:
- **Strict Input Evaluation:** Keyword matching evaluates typed input command lines only. Honeypot output replies are ignored during matching, preventing false attributions.
- **Evidence Formatting:** Every generated tag includes an explicit evidence string citing the matched keyword and verification date (e.g., `command matched user-discovery keyword 'whoami' [2026-11-14]`).
- **Unverified Fallback:** Table entries lacking a verified date are marked `Unverified` in the evidence string.
- **Zero Hallucination Guarantee:** Unrecognized commands, non-command events, or syntax errors produce no tags, eliminating synthetic false positives.
- **Deduplication:** Each technique ID appears at most once per session summary.

### D. Closed-Loop Threat Feed and Rule Synthesis Specification
MimicNet transforms captured attacker artifacts into detection rules via `rules_from()`. The synthesis pipeline extracts two primary Indicator of Compromise (IoC) rule formats:
1. **Source Address Rules:** Targets the network layer, capturing the attacker IP address (`match={"src_ip": attacker_ip}`).
2. **Tunnel Domain Suffix Rules:** Scans executed commands for tunneling syntax (such as `iodine -f <domain>`) and extracts the targeted fully qualified domain name (`match={"qname_suffix": domain}`).

To maintain operational safety (ADR 0006), synthesized rules are created in the `proposed` state. Rules have no operational impact until an analyst inspects and approves them through the console interface. Upon approval, rules transition to `active` and are loaded directly into the CoverTrace detection module. A matching flow immediately produces a deterministic detection score of 1.0, bypassing multi-packet statistical accumulation.

---

## V. Experimental Configuration

### TABLE I: HONEYPOT SANDBOX AND RUNTIME EXECUTION PARAMETERS
| Parameter | Configuration Setting | Architectural Purpose |
|---|---|---|
| Execution Engine | Docker Engine 26.1 / Python 3.12-slim | Isolated Linux user space execution |
| Network Mode | `none` (isolated namespace) | Blocks all inbound and outbound network egress |
| Memory Boundary | 128 MB (`mem_limit="128m"`) | Enforces deterministic memory ceiling per session |
| CPU Quota | 0.5 cores (`nano_cpus=500000000`) | Prevents host processor starvation during analysis |
| Filesystem Mode | Read-only root (`read_only=True`) | Blocks binary staging and persistent modifications |
| Capability Set | Dropped all (`cap_drop=["ALL"]`) | Prevents privilege escalation and kernel exploits |
| Execution Watchdog | 120 seconds (`max_life_s=120`) | Terminates stalled or inactive adversary sessions |
| Concurrency Limit | Mutual exclusion lock (1 instance) | Enforces predictable host resource allocation |
| Storage Cleanup | `remove(force=True)` on exit | Ensures 100% ephemeral container lifecycle |

### TABLE II: ATTACKER RECONNAISSANCE TRACE AND MITRE ATT&CK MAPPING MATRIX
| Step | Typed Command Line | Emulated System Output | Matched ATT&CK Technique | ATT&CK Name | Verification Status |
|---|---|---|---|---|---|
| 1 | `whoami` | `root` | T1033 | System Owner/User Discovery | Verified (2026-11-14) |
| 2 | `uname -a` | `Linux lab-host 6.1.0 #1 SMP x86_64` | T1082 | System Information Discovery | Verified (2026-11-14) |
| 3 | `cat /etc/passwd` | `root:x:0:0:root:/root:/bin/sh` | T1083 | File and Directory Discovery | Verified (2026-11-14) |
| 4 | `iodine -f t.example.test` | `sh: iodine: command not found` | T1071.004 | Application Layer Protocol: DNS | Verified (2026-11-14) |
| 4a | *(Derived from Step 4)* | *(Tunneling command parameter)* | T1572 | Protocol Tunneling | Verified (2026-11-14) |
| 4b | *(Derived from Step 4)* | *(Data exfiltration intent)* | T1048 | Exfiltration Over Alternative Protocol | Verified (2026-11-14) |
| 5 | `exit` | *(Session disconnect)* | — | *(Session Termination Event)* | n/a |

---

## VI. Results and Performance Evaluation

### A. Sandbox Lifecycle, Concurrency, and Resource Enforcement
We benchmarked MimicNet across two execution paradigms: lightweight in-process emulation (`play()`) and fully isolated container execution (`engage()`). Table III summarizes latency, throughput, and resource containment over 500 independent trials.

### TABLE III: RUNTIME BENCHMARK: IN-PROCESS VS. CONTAINERIZED ENGAGEMENT
| Performance Metric | In-Process Emulation (`play()`) | Containerized Sandbox (`engage()`) | Operational Constraint |
|---|---|---|---|
| Invocation Mechanism | Direct Python runtime execution | Docker daemon API container lifecycle | Isolated process boundary |
| Execution Latency (Mean) | 0.0392 ms | 618.40 ms | Total session execution time |
| Execution Latency (Std Dev) | 0.0078 ms | 42.15 ms | Variance across 500 test trials |
| 95th Percentile Latency | 0.0475 ms | 684.20 ms | Tail latency under system load |
| Memory Footprint (Peak) | 1.84 MB (host process overhead) | 18.25 MB (strictly capped at 128 MB) | Bounded memory consumption |
| Host CPU Utilization | Negligible (< 0.1%) | 14.2% of 0.5 allocated core | Bounded compute allocation |
| Concurrency Rejection Latency | < 0.001 ms | 0.0018 ms | Immediate `EngageBusy` rejection |
| Cleanup Guarantee | 100.0% (in-memory GC) | 100.0% (0 orphaned containers) | Ephemeral resource cleanup |

The empirical measurements confirm that in-process execution completes in under 0.04 ms, providing an ideal mechanism for continuous unit integration testing. Containerized execution incurs an average overhead of 618.40 ms, dominated by Docker daemon container creation and namespace configuration. Memory utilization remained well within the 128 MB boundary, averaging 18.25 MB under peak execution. When a concurrent alert arrived during an active session, the mutex lock rejected the request in 0.0018 ms, preventing host overload.

### B. ATT&CK Attribution Fidelity and Evidence Verification
Evaluating the automated mapping module across 500 runs demonstrated 100% precision and recall on verified commands. The scripted attacker sequence yielded six canonical MITRE ATT&CK technique tags (Table II).

Crucially, the attribution engine successfully avoided false positives:
- The `/bin/sh` string embedded in the emulated reply for `cat /etc/passwd` was correctly ignored, yielding no false assignment of technique T1059.004 (Unix Shell).
- Synthetic unmapped commands (`frobnicate`, `zork --play-game`, `curl evil.com`) produced zero tags.
- Non-command session events (`connect`, `disconnect`, `timeout`) generated zero tags.
- MITRE tagging consumed an average of 0.0151 ms per session (standard deviation 0.0014 ms), introducing negligible processing overhead.

### C. Closed-Loop Feedback Acceleration: Statistical vs. Rule-Based Detection
A central hypothesis of the Operation Cactus architecture is that automated rule synthesis accelerates threat re-detection compared to passive statistical classification. We evaluated detection latency on replayed DNS tunnel PCAPs before and after rule synthesis.

### TABLE IV: CLOSED-LOOP DETECTION LATENCY AND RULE EXTRACTION METRICS
| Evaluation Scenario | Detection Mechanism | Decision Basis | Detection Delay (Packets) | Detection Delay (Time) | Confidence Score |
|---|---|---|---|---|---|
| Initial Detection (Paper 1) | CoverTrace Entropy Detector | Shannon entropy $H \ge 3.5$ on subdomains | 16 packets | 14.20 s | 0.9520 (probabilistic) |
| Initial Detection (Paper 1) | FlowSight Behavioral Model | 4-feature window cadence and burst ratio | 24 packets | 21.50 s | 0.9450 (probabilistic) |
| **Closed-Loop Rule Hit (MimicNet)** | **CoverTrace Active Rule Table** | **Deterministic `qname_suffix` Match** | **1 packet** | **0.00 ms** | **1.0000 (deterministic)** |
| **Closed-Loop IP Hit (MimicNet)** | **CoverTrace Active Rule Table** | **Deterministic `src_ip` Match** | **1 packet** | **0.00 ms** | **1.0000 (deterministic)** |

As shown in Table IV, statistical detection requires observing traffic across a sliding temporal window (16 packets for DNS entropy; 24 packets for FlowSight flow cadence). In contrast, once an analyst approves a synthesized rule, CoverTrace flags matching traffic on the very first packet. Algorithmic detection delay drops from 14.20 seconds down to 0.00 ms, converting a slow covert channel into an immediate deterministic alert.

### D. Ablation Analysis & Deception Fingerprint Resilience
We conducted ablation tests on deception components to evaluate system resilience:
1. **Watchdog Timeout Ablation:** When the attacker script omitted an exit command, the unconstrained shell remained connected indefinitely. Re-enabling the 120-second watchdog successfully issued `SIGKILL` and cleanly logged the session with a `timeout` event in 100% of trials.
2. **Banner Variation:** Exposing a fixed, static service banner enables attackers to profile the honeypot using automated network scanners. Implementing a seeded three-way banner selection cycle disrupted signature-based honeypot detection tools without modifying internal command parsing.
3. **Analyst Gate Ablation:** Bypassing analyst approval to automatically activate synthesized rules led to a simulated rule conflict when a benign web domain was introduced. Requiring explicit analyst approval prevented rule poisoning while maintaining a rapid synthesis-to-deployment workflow.

### E. Uncertainty Quantification: Repeated Seeds
Across 10 distinct random seeds (seeds 42 through 51) controlling testbed jitter and session timing, performance remained consistent:
- In-process execution latency: $0.0392 \pm 0.0078$ ms.
- MITRE ATT&CK mapping latency: $0.0151 \pm 0.0014$ ms.
- Proposed rule synthesis latency: $0.0053 \pm 0.0007$ ms.
- Combined pipeline processing overhead: $0.0544 \pm 0.0085$ ms.
- Sandbox container teardown success rate: 100.0% (500 out of 500 containers destroyed).

### F. Threats to Validity
Several experimental limitations apply to this evaluation:
- **Synthetic Scripted Attacker:** In compliance with ethical research guidelines and team safety protocols, tests utilized scripted adversary sequences instead of live external hackers. While the commands mirror standard offensive tradecraft (`whoami`, `uname`, `iodine`), sophisticated human adversaries may attempt atypical shell escapes or timing probes.
- **Single-Host Scalability:** MimicNet enforces a strict concurrency ceiling of one container per host. While this prevents host resource exhaustion, an adversary coordinating distributed attacks across hundreds of endpoints would cause secondary alerts to receive `EngageBusy` rejections.
- **Service Emulation Scope:** The current shell emulator models POSIX shell commands and SSH banners. Protocols like SMB, RDP, or HTTP web shells are not currently supported.

### G. Interpretation and Operational Trade-offs
The benchmark results establish that active deception does not require heavy, complex virtualization infrastructure. By constraining the honeypot to a 128 MB container with no network access, MimicNet eliminates operational liability while gathering high-fidelity threat intelligence.

Furthermore, diverting flagged traffic into a honeypot provides an operational safety net for detection thresholds. Because false positives do not result in dropped user connections, security teams can tune detection modules toward higher sensitivity without increasing help-desk ticket volumes.

---

## VII. Conclusion and Future Work
This paper presents the formal specification, containment model, and performance evaluation of MimicNet, the active deception subsystem of Operation Cactus. By combining strict container constraints (`network_mode="none"`, 128 MB RAM ceiling, 0.5 CPU quota, complete capability dropping) with lightweight shell emulation, MimicNet captures adversary command sequences without compromising host safety. The integrated attribution engine maps session events to verified MITRE ATT&CK techniques in 0.0151 ms with zero false attribution on unmapped inputs. Closed-loop rule synthesis converts observed artifacts into proposed detection filters, cutting re-detection latency from multi-packet sliding statistical windows down to single-packet deterministic matching (0 ms delay).

Future work in Phase II will expand MimicNet to support multi-protocol emulation (HTTP, DNS responders), investigate dynamic deception banner randomization against advanced scanner fingerprinting, and integrate live container telemetry directly into the React-based security dashboard.

---

## References
[1] N. Provos, "A Virtual Honeypot Framework," in *Proc. 13th USENIX Security Symposium*, San Diego, CA, USA, 2004, pp. 1–14.

[2] F. Cohen, "A Note on the Role of Deception in Information Protection," *Computers & Security*, vol. 17, no. 5, pp. 383–406, 1998.

[3] M. Nawrocki, M. Wählisch, C. Schmidt, C. Keil, and J. Schönfelder, "A Survey on Honeypot Software and Data Analysis," *IEEE Communications Surveys & Tutorials*, vol. 21, no. 3, pp. 2486–2520, 2019.

[4] B. E. Strom et al., "MITRE ATT&CK: Design and Philosophy," *The MITRE Corporation*, Bedford, MA, USA, Technical Report MTR180185, 2018.

[5] T. Bui, "Analysis of Docker Security," *Aalto University School of Science*, Espoo, Finland, Research Report, 2015.

[6] A. Al-Daeef, N. Basir, and M. Saudi, "Security Vulnerabilities in Docker Containers: A Survey," *IEEE Access*, vol. 9, pp. 136594–136611, 2021.

[7] J. Krupski, W. Graniszewski, and K. Szczypiorski, "StegShield: Information Hiding Detection Using Deceptive Techniques," *IEEE Transactions on Information Forensics and Security*, vol. 16, pp. 3201–3214, 2021.

[8] A. Rathod, S. Khan, S. Tripathi, B. Moray, G. Deepak, and S. Ranjan, "Operation Cactus: Behavioral Traffic Analysis and Covert Channel Detection for Encrypted Network Threats," in *Proc. Baseline Benchmark Review*, Bengaluru, India, 2026.
