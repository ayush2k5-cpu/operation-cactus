# Operation Cactus: Active Deception, Interactive Session Telemetry, and Closed-Loop Threat Feed Synthesis for Covert Network Exfiltration

**An Empirical Evaluation of the MimicNet Deception Architecture, Container Isolation Constraints, and MITRE ATT&CK Mapping**

| **Ayush Rathod**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* | **Sharukh Khan**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* | **Shivansh Tripathi**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* |
|:---:|:---:|:---:|
| **Bhargav Moray**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* | **Gerard Deepak**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* | **Shalini Ranjan**<br>*Dept. of Computer Science & Engineering (Cyber Security)*<br>*Dayananda Sagar Academy of Technology and Management*<br>*Bengaluru* |

---

## Abstract
Operation Cactus connects passive flow analysis with an active deception module, MimicNet, to inspect covert network exfiltration when payload encryption blocks deep packet inspection. Once the detection pipeline raises an alert on an entity, MimicNet redirects the session into an emulated, short-lived sandbox. This benchmark measures the containment boundaries, runtime overhead, and threat intelligence synthesis of the response engine. The sandbox enforces five invariants: zero external network routing (`network_mode="none"`), a 128 MB RAM ceiling, a 0.5 CPU quota, complete Linux capability dropping (`cap_drop=["ALL"]`), and a 120-second execution timer. Over 500 test trials on a scripted adversary trace (`whoami`, `uname -a`, `cat /etc/passwd`, `iodine -f t.example.test`), the Python shell emulator processes the interactive session in an average of 0.0392 ms (standard deviation 0.0078 ms). An automated keyword matcher extracts canonical MITRE ATT&CK techniques in 0.0151 ms with zero false attribution on negative controls. MimicNet then extracts candidate detection rules from session logs in 0.0053 ms. Under human analyst review, an approved candidate rule enters CoverTrace. This drops re-detection delay from sliding statistical windows down to immediate single-packet matching (0 ms algorithmic delay). An inter-process mutex limits active sandboxes to one per host; concurrent alerts receive an `EngageBusy` rejection in 0.0018 ms. These benchmarks show that constrained container deception captures threat telemetry without compromising host stability or throughput.

*Index Terms*—cyber deception, honeypots, container sandboxing, covert channel containment, MITRE ATT&CK mapping, closed-loop threat intelligence, incident response.

---

## I. Introduction
Network security teams generally react to intrusions by dropping packets or resetting TCP handshakes. Outright termination stops the active connection, but it reveals nothing about who is attacking or what software they planned to execute. In networks secured by transport-layer encryption, detection models must make decisions on noisy metadata. Severing connections based on probabilistic thresholds alone disrupts legitimate enterprise traffic.

Operation Cactus implements a two-stage response structure:
1. Detection Middleware (FlowSight and CoverTrace): Evaluates flow statistics and protocol-level covert channel indicators without decrypting payloads [8].
2. Deception Response Layer (MimicNet): Routes flagged connections into an isolated honeypot container instead of closing the TCP socket.

This split alters the operational response. False alarms interact with an emulated service, so legitimate users face no connection drops. Malicious programs receive emulated command prompts and proceed to run discovery commands. Their tooling is thus recorded in an instrumented sandbox.

This evaluation answers two practical research questions:
- RQ1: Can a container sandbox capture interactive command telemetry while maintaining fixed memory ceilings, CPU allocations, and network boundaries under concurrency locks?
- RQ2: How fast and accurately can raw session logs produce verified MITRE ATT&CK technique tags and new detection rules for earlier re-detection?

This paper presents the formal specification, isolation mechanics, and empirical runtime measurements of the MimicNet subsystem under lab benchmark conditions.

---

## II. Related Work
Honeypots have developed from early static shell listeners into dynamic virtualization systems. Provos designed Honeyd to demonstrate that simulated network topologies could log port scans and probe activity across unused subnets [1]. Cohen formalized deception in computer defense; deceptive environments force attackers to spend time verifying system authenticity [2]. Modern systems use varying interaction levels from simple port emulators to full virtual machines [3].

Lightweight containerization lowered the compute requirements of honeypots. Bui evaluated container security boundaries and showed that cgroups and namespace restrictions prevent host compromise when properly applied [5]. Al-Daeef et al. cataloged container breakout methods. They identified broad kernel capabilities, writable filesystems, and mounted control sockets as the primary hazards in container honeypots [6]. MimicNet mitigates these risks: it drops all capabilities (`CAP_DROP=ALL`), mounts the root filesystem read-only, and detaches network namespaces.

Systematic threat categorization requires shared frameworks. Strom et al. built MITRE ATT&CK to index post-compromise adversary tactics based on public incident reports [4]. Krupski, Graniszewski, and Szczypiorski (StegShield) studied deception mechanisms focused on covert channels [7]. MimicNet extends this work by pairing emulated command execution with evidence-based ATT&CK tagging and analyst-approved rule extraction.

---

## III. Problem Statement
Automated deception in enterprise environments faces three specific technical hurdles:
1. Host Compromise: Poorly isolated decoys can give attackers a foothold for local privilege escalation or lateral network scanning.
2. Resource Exhaustion: Spawning an unconstrained container for every alert risks exhausting host memory, CPU cores, and process tables.
3. Feedback Poisoning: Auto-activating untrusted rules generated from honeypot data risks self-inflicted denial of service.

MimicNet counters these hazards through strict namespace boundaries, a single-instance mutual exclusion lock, and an analyst-in-the-loop approval workflow. This study benchmarks the execution latency, memory boundaries, ATT&CK mapping accuracy, and re-detection latency of the system.

---

## IV. Methodology

### A. Deception Architecture and Sandbox Containment Model
MimicNet acts as an event-driven response engine downstream of the correlation gate. When an Alert reaches the `open` state, the backend calls `engage` to spawn an isolated container.

#### Container Boundary Rules and Resource Caps
To eliminate breakout and resource exhaustion hazards, each container runs under five static limits:
- Network Isolation: Configured with `network_mode="none"`. The container has no network interfaces beyond loopback. This blocks outbound command-and-control, data exfiltration, and lateral scans.
- Memory Boundary: Memory consumption is capped at 128 MB (`mem_limit="128m"`). The Linux kernel terminates any process attempting allocations beyond this ceiling.
- CPU Quota: Throttled to 0.5 logical cores (`nano_cpus=500000000`) to protect host detection processes from starvation.
- Capability Revocation: All kernel capabilities are stripped (`cap_drop=["ALL"]`). The container root filesystem is mounted read-only (`read_only=True`) to prevent file tampering and binary installation.
- Mount Restrictions: No host directories, volumes, or control sockets (`/var/run/docker.sock`) enter the container.

#### Concurrency Locks and Execution Lifecycles
Single-host deployments require predictable resource boundaries. MimicNet implements an inter-process mutex (`_running = threading.Lock()`). Only one container can run at any given moment. Any incoming Alert during an active session is rejected with an `EngageBusy` error.

Each session includes a 120-second watchdog timer (`max_life_s = 120`). If an attacker halts or stays connected, the runtime sends a `SIGKILL` signal to the container and appends a `timeout` record to the session log. An exit `finally` block always executes `container.remove(force=True)`, so zero abandoned containers or lingering disk states remain behind.

### B. Interactive Emulation and Session Telemetry Capture
Inside the container, MimicNet runs an interactive shell script (`SshLikeShell`) written in standard Python. It uses no third-party libraries, which maintains identical behavior across in-process unit tests and real containers.

The shell displays an emulated banner (`SSH-like service (lab honeypot, not SSH)`) and returns canned output for standard UNIX discovery commands (`whoami`, `id`, `uname -a`, `pwd`, `ls`, `cat /etc/passwd`). Commands stream to stdout as JSON lines:
- `connect`: Stores the attacker IP address, connection time, and service banner.
- `command`: Logs the exact typed command string and the emulated output.
- `disconnect`: Records session termination through `exit`, `logout`, or script completion.
- `timeout`: Marks sessions terminated by the execution timer.

### C. Automated Threat Attribution and MITRE ATT&CK Mapping
When a session concludes, `tag_events()` in `eval/mitre.py` parses the telemetry stream. The mapping table checks inputs against technique definitions verified on `attack.mitre.org`:
- Strict Input Evaluation: The engine matches only typed commands. It ignores output text, which prevents false positive tags.
- Evidence Documentation: Every tag records the matching keyword and verification date (for instance, `command matched user-discovery keyword 'whoami' [2026-11-14]`).
- Unverified Marker: Entries without a verification date carry an `Unverified` tag in the log.
- Zero Hallucination: Unrecognized commands, errors, and system events receive no tags.
- Deduplication: Each technique ID appears once per session.

### D. Closed-Loop Threat Feed and Rule Synthesis Specification
MimicNet converts session artifacts into operational detection rules using `rules_from()`. The engine produces two rule types:
1. Source Address Rules: Targets the network layer by matching the attacker IP (`match={"src_ip": attacker_ip}`).
2. Tunnel Domain Suffix Rules: Parses command strings for DNS tunneling tools (such as `iodine -f <domain>`) to extract target domains (`match={"qname_suffix": domain}`).

To maintain defensive safety (ADR 0006), synthesized rules default to the `proposed` state. Rules stay inactive until a security analyst inspects and accepts them via the web console. Approved rules become `active` and load into CoverTrace. A matching flow triggers an immediate detection score of 1.0 and bypasses multi-packet observation windows.

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
We benchmarked MimicNet across two execution modes: in-process shell execution (`play()`) and Docker container execution (`engage()`). Table III summarizes latency, memory, and concurrency metrics across 500 benchmark runs.

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

In-process emulation finishes in under 0.04 ms, which provides a fast target for regression test suites. Containerized execution averages 618.40 ms, with most time spent on Docker daemon creation calls and namespace isolation. Peak memory remained low at 18.25 MB, well below the 128 MB limit. If a secondary alert arrives while a container runs, the mutex returns an error in 0.0018 ms to protect host throughput. Fig. 1 details the execution times across both environments.

![Fig. 1. Runtime latency breakdown comparing in-process emulation pipeline stages against full Docker container lifecycle.](eval/results/paper2_fig1_latency_breakdown.png)

### B. ATT&CK Attribution Fidelity and Evidence Verification
Testing the attribution module on 500 runs yielded consistent technique matching with zero false positives. The test script produced six verified technique tags (Table II).

Negative controls confirmed the specificity of the matcher:
- The `/bin/sh` shell path in the `cat /etc/passwd` reply produced zero tags for T1059.004 because the matcher scans input commands only.
- Unregistered inputs (`frobnicate`, `zork --play-game`, `curl evil.com`) generated zero tags.
- System lifecycle events (`connect`, `disconnect`, `timeout`) produced zero tags.
- Keyword matching required an average of 0.0151 ms per session.

Fig. 3 shows technique precision across positive detections and negative control tests.

![Fig. 3. MITRE ATT&CK technique mapping coverage and zero-hallucination verification across positive commands and negative controls.](eval/results/paper2_fig3_mitre_mapping.png)

### C. Closed-Loop Feedback Acceleration: Statistical vs. Rule-Based Detection
Operation Cactus uses honeypot session data to speed up subsequent detections. We compared detection times on replayed PCAP files before and after loading synthesized rules.

### TABLE IV: CLOSED-LOOP DETECTION LATENCY AND RULE EXTRACTION METRICS
| Evaluation Scenario | Detection Mechanism | Decision Basis | Detection Delay (Packets) | Detection Delay (Time) | Confidence Score |
|---|---|---|---|---|---|
| Initial Detection (Paper 1) | CoverTrace Entropy Detector | Shannon entropy $H \ge 3.5$ on subdomains | 16 packets | 14.20 s | 0.9520 (probabilistic) |
| Initial Detection (Paper 1) | FlowSight Behavioral Model | 4-feature window cadence and burst ratio | 24 packets | 21.50 s | 0.9450 (probabilistic) |
| **Closed-Loop Rule Hit (MimicNet)** | **CoverTrace Active Rule Table** | **Deterministic `qname_suffix` Match** | **1 packet** | **0.00 ms** | **1.0000 (deterministic)** |
| **Closed-Loop IP Hit (MimicNet)** | **CoverTrace Active Rule Table** | **Deterministic `src_ip` Match** | **1 packet** | **0.00 ms** | **1.0000 (deterministic)** |

Statistical scoring requires collecting packets over temporal windows: 16 packets for DNS entropy and 24 packets for FlowSight burst tracking. When an analyst promotes an extracted rule to active status, CoverTrace flags matching flows on the very first packet. Delay drops from 14.20 seconds to 0.00 ms. This converts statistical anomaly detection into deterministic rule hits. Fig. 2 illustrates this reduction in detection latency.

![Fig. 2. Closed-loop re-detection delay acceleration comparing multi-packet statistical windows against immediate deterministic rule hits.](eval/results/paper2_fig2_detection_acceleration.png)

### D. Ablation Analysis & Deception Fingerprint Resilience
We evaluated individual deception controls through ablation tests:
1. Watchdog Timer Ablation: Removing the timer let stalled shells run indefinitely. Restoring the 120-second watchdog triggered `SIGKILL` and logged a `timeout` event in every run.
2. Banner Variation: Static service banners allow scanners to identify honeypots quickly. Rotating across three seeded banners varied service fingerprints while keeping command parsing stable.
3. Analyst Gate Ablation: Bypassing analyst approval allowed a test rule with a common web domain to activate automatically and trigger false alarms. Retaining the approval gate stopped rule conflicts while keeping rule generation fast.

### E. Uncertainty Quantification: Repeated Seeds
Across 10 random seeds (seeds 42 to 51) controlling network jitter and timestamps, performance remained stable:
- In-process execution latency: $0.0392 \pm 0.0078$ ms.
- MITRE ATT&CK mapping latency: $0.0151 \pm 0.0014$ ms.
- Candidate rule synthesis latency: $0.0053 \pm 0.0007$ ms.
- Combined pipeline processing time: $0.0544 \pm 0.0085$ ms.
- Container cleanup success rate: 100.0% (500 out of 500 containers destroyed).

### F. Threats to Validity
Three constraints apply to these experimental results:
- Scripted Adversary Sequences: Tests used automated command scripts instead of human adversaries. Real attackers may use alternative shell escapes or subtle timing checks.
- Single-Container Limit: The single-instance lock prevents resource starvation, but distributed attacks across multiple endpoints will see secondary sessions rejected with `EngageBusy`.
- Emulation Boundaries: The shell supports common POSIX and SSH commands. Web shells, database protocols, and SMB sessions are currently outside its scope.

### G. Interpretation and Operational Trade-offs
These benchmarks show that high-interaction deception does not require heavy hypervisor infrastructure. Setting strict 128 MB RAM limits and detaching network namespaces removes host risks while capturing clean command logs.

Diverting suspect traffic into decoys also softens detection trade-offs. Because false alarms do not terminate active sessions, engineering teams can lower detection thresholds without triggering service outages for valid users.

---

## VII. Conclusion and Future Work
This paper evaluates the architecture, containment rules, and telemetry pipeline of MimicNet. Combining strict container restrictions (`network_mode="none"`, 128 MB RAM cap, 0.5 CPU quota, dropped capabilities) with shell emulation captures adversary activity safely. The keyword parser maps commands to MITRE ATT&CK techniques in 0.0151 ms with zero false attribution on negative controls. Analyst-reviewed rule generation turns session data into CoverTrace filters. This cuts re-detection delay from sliding statistical windows down to single-packet matches (0 ms algorithmic delay).

Phase II development will add web and DNS protocol handlers, dynamic banner randomization against automated profiling tools, and telemetry streaming into the central web dashboard.

---

## References
[1] N. Provos, "A Virtual Honeypot Framework," in *Proc. 13th USENIX Security Symposium*, San Diego, CA, USA, 2004, pp. 1–14.

[2] F. Cohen, "A Note on the Role of Deception in Information Protection," *Computers & Security*, vol. 17, no. 5, pp. 383–406, 1998.

[3] M. Nawrocki, M. Wählisch, C. Schmidt, C. Keil, and J. Schönfelder, "A Survey on Honeypot Software and Data Analysis," *IEEE Communications Surveys & Tutorials*, vol. 21, no. 3, pp. 2486–2520, 2019.

[4] B. E. Strom et al., "MITRE ATT&CK: Design and Philosophy," *The MITRE Corporation*, Bedford, MA, USA, Technical Report MTR180185, 2018.

[5] T. Bui, "Analysis of Docker Security," *Aalto University School of Science*, Espoo, Finland, Research Report, 2015.

[6] A. Al-Daeef, N. Basir, and M. Saudi, "Security Vulnerabilities in Docker Containers: A Survey," *IEEE Access*, vol. 9, pp. 136594–136611, 2021.

[7] J. Krupski, W. Graniszewski, and K. Szczypiorski, "StegShield: Information Hiding Detection Using Deceptive Techniques," *IEEE Transactions on Information Forensics and Security*, vol. 16, pp. 3201–3214, 2021.

[8] A. Rathod, S. Khan, S. Tripathi, B. Moray, Gerard Deepak, and S. Ranjan, "Operation Cactus: Behavioral Traffic Analysis and Covert Channel Detection for Encrypted Network Threats," in *Proc. Baseline Benchmark Review*, Bengaluru, India, 2026.
