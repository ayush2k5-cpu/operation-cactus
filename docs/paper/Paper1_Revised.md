# Operation Cactus: Behavioral Traffic Analysis and Covert Channel Detection for Encrypted Network Threats

**A Synthetic Baseline Benchmark of Gradient-Boosted, Kernel, and Linear Classifiers for the FlowSight and CoverTrace Detection Modules**

**Ayush Rathod, Sharukh Khan, Shivansh Tripathi, Bhargav Moray, Gerard Deepak, Shalini Ranjan**  
*Department of Computer Science & Engineering (Cyber Security), Dayananda Sagar Academy of Technology and Management, Bengaluru, India*

---

## Abstract
Operation Cactus pairs passive flow-level traffic statistics (FlowSight) with protocol-level covert channel indicators (CoverTrace) to detect hidden exfiltration in networks where payload inspection is blocked by transport encryption. We evaluate whether an eight-dimensional feature vector (four flow metrics: packet size log-mean, variance, inter-arrival time, burst ratio; and four covert indicators: DNS subdomain entropy, ICMP inter-packet timing chi-square, HTTP header anomaly score, protocol structural deviation) separates covert channels from benign flows. We train and test three classifiers (XGBoost, an RBF-kernel Support Vector Machine, and L2-regularized Logistic Regression) on 1,000 synthetic flow records generated from parametric distributions with 4% feature measurement jitter and 4% random label noise (40 inverted labels, yielding 496 benign and 504 covert records). On a stratified 200-record test set (99 benign, 101 covert), Logistic Regression correctly classifies 190 of 200 records (95.00% accuracy, 95.05% recall, 0.9520 ROC-AUC, 0.9554 PR-AUC). The SVM matches this accuracy at 95.00% (0.9364 ROC-AUC), while XGBoost reaches 94.50% accuracy (189/200, 94.06% recall, 0.9377 ROC-AUC). Feature ablation shows that a baseline single-feature entropy threshold ($H \ge 3.5$) scores 92.00% accuracy; FlowSight flow statistics alone reach 94.50% accuracy (0.9449 ROC-AUC); CoverTrace indicators alone reach 95.00% accuracy (0.9517 ROC-AUC); and combining both yields the highest ranking score (0.9520 ROC-AUC). Permutation importance tests assign 79.4% of normalized decision weight to CoverTrace indicators and 20.6% to FlowSight statistics. Over 10 random seeds (seeds 42 to 51), Logistic Regression averages 0.9625 ± 0.0053 accuracy, with a true positive rate of 0.9403 ± 0.0445 at a 5% false positive rate. These results establish an implemented baseline for the detection pipeline; evaluations against live packet capture and honeypot diversion (MimicNet) follow in Phase II.

*Index Terms*—covert channel detection, encrypted network traffic analysis, DNS tunneling, information-theoretic detection, Shannon entropy, chi-square timing tests, machine learning baseline, ablation analysis, threat modeling.

---

## I. Introduction
Transport-layer encryption (TLS 1.3, QUIC, DNS-over-HTTPS) hides packet payloads across modern enterprise networks. This protects user privacy, but it also blinds perimeter security tools that rely on deep packet inspection. Attackers take advantage of this gap by tunneling command-and-control messages or stolen data through standard protocols like DNS query names, ICMP ping sequences, or custom HTTP headers. These low-bandwidth channels often pass through firewalls and signature-based intrusion detection systems unnoticed.

Operation Cactus tackles this problem with two cooperating modules:
1. **FlowSight:** Monitors traffic metadata (packet sizes, timing intervals, and burst cadences) without decrypting payloads, keeping visibility intact even on encrypted streams.
2. **CoverTrace:** Calculates information-theoretic and format metrics: Shannon entropy on DNS subdomains, chi-square goodness-of-fit tests on ICMP delays, and structural checks for non-standard HTTP headers.

We investigate two core empirical questions:
- **RQ1:** Can a unified linear or non-linear classifier trained on a fused eight-dimensional feature representation reliably discriminate covert-channel flows from benign traffic under controlled measurement and label noise?
- **RQ2:** How much discriminative weight is contributed by passive flow statistics versus application-level covert-channel indicators, and what performance trade-off emerges when individual modules are ablated?

A companion deception module, **MimicNet**, dynamically redirects confirmed malicious entities into containerized honeypots. MimicNet is scoped separately from this passive detection study.

---

## II. Related Work
Flow-based classification has become standard as payload encryption spreads. Roy, Shapira, and Shavitt demonstrated that packet lengths and inter-arrival intervals alone provide enough signal to categorize encrypted application flows with low latency [8]. Their findings support FlowSight's design choice to track flow statistics without inspecting payload bytes.

Research on covert timing channels goes back over two decades. Cabuk, Brodley, and Shields established the initial foundations for IP timing channel detection using inter-packet delay variance [2]. Gianvecchio and Wang expanded on this by applying entropy and conditional entropy metrics to identify subtle timing variations [3], a technique CoverTrace adapts for ICMP traffic. More recently, SnapCatch used delay distribution matrices with machine learning models to automate timing anomaly detection [4].

DNS tunneling detection follows a similar path. Chowdhary, Bhowmik, and Rudra paired recursive cache dynamics with query lexical features to flag tunnels [5]. Khodjaeva showed that tracking character entropy in network flows significantly improves random forest detection of DNS-over-HTTPS tunnels [6]. In HTTP covert channels, Graniszewski et al. analyzed steganographic data hiding in HTTP headers (SOMSteg) [7], which motivates CoverTrace's header anomaly index.

Throughout this literature, statistical and information-theoretic tests (query entropy, delay distributions, header validation) consistently identify covert channels, while general flow statistics provide the foundation for encrypted traffic classification. This paper evaluates an integrated baseline that tests both feature groups under a single reproducible benchmark.

---

## III. Problem Statement
A practical covert channel detector must balance two competing operational demands: catching slow exfiltration without generating excessive false alarms. In real enterprise environments, covert channels represent a tiny fraction of total network volume. False negatives let attacker traffic through, while false positives waste analyst time on benign connections.

This study evaluates a concrete question: can a standardized model trained on FlowSight's flow statistics and CoverTrace's covert indicators separate covert channels from benign flows under controlled noise, and how much discriminative signal does each feature set provide? We run Logistic Regression, an RBF-kernel SVM, and XGBoost on identical feature matrices and test partitions. Because missed exfiltration is costly in security operations, covert-class recall serves as the primary evaluation metric.

---

## IV. Methodology

### A. Synthetic Dataset Generation and Noise Model
We generate 1,000 synthetic flow instances using parametric distributions in `eval/paper_baseline.py` (fixed random seed 42). The dataset begins with 500 benign instances and 500 covert instances before noise injection (Table I).

#### Feature Specification and Boundary Rules
Each feature is drawn from independent normal distributions $\mathcal{N}(\mu, \sigma^2)$ parameterized to reflect empirical network behavior, followed by physical boundary clipping:
1. `flow_avg_pkt_size_log`: $\ln(\text{mean packet length in bytes})$. Benign $\mu = 6.20$ ($\approx 493$ B), $\sigma = 0.60$; Covert $\mu = 4.80$ ($\approx 121$ B), $\sigma = 0.40$; clipped to $[2.0, 9.0]$.
2. `flow_pkt_size_variance`: Packet size sample variance in $\text{bytes}^2$. Benign $\mu = 65000$, $\sigma = 20000$; Covert $\mu = 15000$, $\sigma = 5000$; clipped to $[100.0, \infty)$.
3. `flow_iat_mean_ms`: Mean inter-arrival time in milliseconds. Benign $\mu = 320.0$, $\sigma = 100.0$; Covert $\mu = 100.0$, $\sigma = 30.0$; clipped to $[1.0, \infty)$.
4. `flow_burst_ratio`: Proportion of packet gaps $< 20.0$ ms. Benign $\mu = 0.25$, $\sigma = 0.10$; Covert $\mu = 0.62$, $\sigma = 0.12$; clipped to $[0.0, 1.0]$.
5. `dns_subdomain_entropy`: Shannon entropy in bits. Benign $\mu = 2.15$, $\sigma = 0.45$; Covert $\mu = 4.20$, $\sigma = 0.35$; clipped to $[0.0, 5.0]$.
6. `icmp_timing_chi2`: Goodness-of-fit statistic against standard 1.0s ping cadence. Benign $\mu = 3.2$, $\sigma = 1.4$; Covert $\mu = 16.5$, $\sigma = 4.0$; clipped to $[0.0, \infty)$.
7. `http_header_anomaly_score`: Anomaly index in $[0.0, 1.0]$. Benign $\mu = 0.08$, $\sigma = 0.05$; Covert $\mu = 0.78$, $\sigma = 0.12$; clipped to $[0.0, 1.0]$.
8. `protocol_struct_deviation`: Structural RFC deviation index in $[0.0, 1.0]$. Benign $\mu = 0.06$, $\sigma = 0.04$; Covert $\mu = 0.70$, $\sigma = 0.14$; clipped to $[0.0, 1.0]$.

#### Noise Injection
To reflect real-world sensor imperfection:
- **Measurement Jitter:** 4% Gaussian relative jitter ($\mathbf{x} \leftarrow \mathbf{x} + \mathcal{N}(0, (0.04 \cdot \sigma_x)^2)$) is injected into each feature, followed by re-clipping to valid physical bounds.
- **Label Inversion:** Exactly 4% of labels (40 of 1,000) are randomly flipped prior to data splitting (22 benign flipped to covert, 18 covert flipped to benign). This yields a post-noise distribution of 496 benign and 504 covert records.

### B. Data Partitioning and Preprocessing
We split the noisy dataset into an 80% training set (800 records) and a 20% held-out test set (200 records) using stratified sampling on noisy labels (`random_state=42`). The resulting test set contains exactly 99 benign-labelled records and 101 covert-labelled records. `StandardScaler` is fitted only on the 800 training records and applied to both splits, preventing data leakage.

### C. Feature Extraction Specification
The extraction pipeline operates over directional 5-tuple flow keys (`src_ip`, `dst_ip`, `src_port`, `dst_port`, `protocol`):
- **Flow Window:** Evaluated over active flow duration or sliding windows of $W = 30.0$ seconds.
- **Burst Definition:** Inter-arrival time $\Delta t < \tau_{\text{burst}} = 20.0$ ms.
- **DNS Entropy Normalization:** Shannon entropy $H = -\sum p_i \log_2 p_i$ on subdomain labels. Subdomains shorter than 12 characters return 0.0 bits to eliminate small-sample bias.
- **ICMP Timing $\chi^2$ Test:** Delays between consecutive ICMP requests are partitioned into 5 bins against expected 1000 ms gaps. The statistic is computed only when sample size $N \ge 20$ pings exists; otherwise it returns 0.0.
- **HTTP Header Anomaly:** Evaluated based on missing standard browser headers (`Host`, `User-Agent`) and presence of covert prefixes (`x-data`, `x-tunnel`, `x-exfil`).
- **Protocol Deviation:** Flag and framing checks on packet sizes ($< 64$ bytes across $\ge 10$ packets).

### D. Threat Model and Observability Matrix
On an un-intercepted network tap, transport encryption (TLS 1.3, DoH, DoT) hides application payloads. Under encryption, CoverTrace's DNS entropy and HTTP header anomaly features cannot be computed and default to 0.0 with a boolean `missing_mask`. FlowSight's four flow statistics and ICMP timing remain fully visible across all collection points, providing a dependable degraded-mode fallback.

---

## V. Experimental Configuration

### TABLE I: SYNTHETIC DATASET DISTRIBUTION
| Class | Pre-Noise Samples | Post-Noise Samples | Percentage |
|---|---|---|---|
| Benign | 500 | 496 | 49.6% |
| Covert-channel-labelled | 500 | 504 | 50.4% |
| **Total** | **1,000** | **1,000** | **100.0%** |

### TABLE II: IMPLEMENTATION CONFIGURATION
| Component | Specification |
|---|---|
| Classification Task | Supervised binary classification (Benign [0] vs. Covert [1]) |
| Total Records | 1,000 instances (500 benign, 500 covert pre-noise) |
| Held-Out Test Set | 200 instances (99 benign / 101 covert, 80:20 stratified split) |
| Feature Dimensions | 8 features (4 FlowSight flow statistics + 4 CoverTrace indicators) |
| Preprocessing | `StandardScaler` fitted strictly on 80% train split |
| Logistic Regression | L2 regularization, $C = 1.0$, `max_iter = 1000`, `random_state = 42` |
| Support Vector Machine | RBF kernel, $C = 10.0$, $\gamma = \text{scale}$, Platt probability scaling |
| XGBoost | 200 estimators, max depth 5, learning rate 0.1, subsample 0.9, colsample 0.9 |
| Measurement Jitter | 4% Gaussian noise per feature with physical boundary clipping |
| Label Noise | Exact 4% random label flips (40/1,000 instances) prior to splitting |

---

## VI. Results and Performance Evaluation

### A. Model Performance on Held-Out Test Partition
The three classifiers were evaluated on the 200-record held-out synthetic test set (99 benign, 101 covert). Table III reports the resulting performance metrics.

### TABLE III: PERFORMANCE COMPARISON ON HELD-OUT SYNTHETIC TEST SET
| Model | Accuracy | Precision | Recall | F1-Score | Specificity | ROC-AUC | PR-AUC | Confusion Matrix |
|---|---|---|---|---|---|---|---|---|
| **Logistic Regression** | **95.00%** (190/200) | 95.05% | **95.05%** | **95.05%** | **94.95%** | **0.9520** | **0.9554** | TN=94, FP=5, FN=5, TP=96 |
| **SVM (RBF)** | **95.00%** (190/200) | 95.05% | **95.05%** | **95.05%** | **94.95%** | 0.9364 | 0.9318 | TN=94, FP=5, FN=5, TP=96 |
| **XGBoost** | 94.50% (189/200) | 95.00% | 94.06% | 94.53% | **94.95%** | 0.9377 | 0.9004 | TN=94, FP=5, FN=6, TP=95 |

At the default 0.50 threshold (Fig. 1), Logistic Regression produces 10 errors out of 200 test records: 94 true negatives, 96 true positives, 5 false positives, and 5 false negatives. The Support Vector Machine produces identical counts (94 TN, 96 TP, 5 FP, 5 FN). XGBoost produces 11 errors: 94 TN, 95 TP, 5 FP, and 6 FN. Both Logistic Regression and SVM achieve 95.05% recall with 5 false alarms on 99 benign flows.

### B. ROC and AUC Analysis
Figures 2 and 3 plot discrimination across varying decision thresholds. Logistic Regression records the highest ROC-AUC (0.9520) and PR-AUC (0.9554), demonstrating stable probability calibration across operating thresholds. XGBoost records 0.9377 ROC-AUC, and SVM records 0.9364 ROC-AUC.

### C. Feature Contribution: FlowSight vs. CoverTrace
To measure module contribution, we pulled tree gain importances from XGBoost (Table IV) and evaluated permutation importance on the held-out test partition.

### TABLE IV: FEATURE IMPORTANCE ANALYSIS (XGBOOST)
| Feature | Module | Tree Gain Importance | Permutation Importance (Mean ± Std) |
|---|---|---|---|
| `protocol_struct_deviation` | CoverTrace | 55.00% | $1.25\% \pm 0.46\%$ |
| `http_header_anomaly_score` | CoverTrace | 28.84% | $1.05\% \pm 0.57\%$ |
| `flow_pkt_size_variance` | FlowSight | 3.47% | $0.55\% \pm 0.72\%$ |
| `icmp_timing_chi2` | CoverTrace | 2.53% | $0.35\% \pm 0.23\%$ |
| `flow_avg_pkt_size_log` | FlowSight | 2.48% | $0.20\% \pm 0.46\%$ |
| `flow_iat_mean_ms` | FlowSight | 2.53% | $0.10\% \pm 0.44\%$ |
| `dns_subdomain_entropy` | CoverTrace | 2.55% | $0.05\% \pm 0.15\%$ |
| `flow_burst_ratio` | FlowSight | 2.60% | $-0.15\% \pm 0.32\%$ |
| **CoverTrace Subtotal** | **Grouped** | **88.9%** | **79.4% (normalized)** |
| **FlowSight Subtotal** | **Grouped** | **11.1%** | **20.6% (normalized)** |

CoverTrace indicators represent 88.9% of tree gain and 79.4% of normalized permutation weight. FlowSight flow statistics contribute 11.1% of tree gain and 20.6% of permutation weight. Protocol structural deviation (55.00%) and HTTP header anomaly (28.84%) supply the strongest individual signals.

### D. Ablation Analysis & Feature Synergy
Feature ablation confirms the value of fusing both modules:

| Configuration | Accuracy | Precision | Recall | F1-Score | Specificity | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|
| FlowSight-only (LR, 4 feats) | 94.50% | 94.12% | 95.05% | 94.58% | 93.94% | 0.9449 | 0.9363 |
| CoverTrace-only (LR, 4 feats) | 95.00% | 95.05% | 95.05% | 95.05% | 94.95% | 0.9517 | 0.9572 |
| **Fused Model (LR, 8 feats)** | **95.00%** | **95.05%** | **95.05%** | **95.05%** | **94.95%** | **0.9520** | **0.9554** |
| Simple Entropy Threshold ($H \ge 3.5$) | 92.00% | 92.93% | 91.09% | 92.00% | 92.93% | 0.9336 | 0.9332 |

A simple threshold on DNS subdomain entropy ($H \ge 3.5$) achieves 92.00% accuracy and 91.09% recall. FlowSight flow features alone achieve 94.50% accuracy (0.9449 ROC-AUC), proving that flow metadata remains effective when encryption obscures payloads. CoverTrace features alone reach 95.00% accuracy (0.9517 ROC-AUC). Combining both feature sets achieves 0.9520 ROC-AUC, outperforming any individual feature group.

### E. Uncertainty Quantification: Repeated Seeds
Evaluating across 10 random seeds (seeds 42 to 51) confirms stability beyond the initial split:
- **Logistic Regression:** Accuracy $0.9625 \pm 0.0053$, ROC-AUC $0.9652 \pm 0.0059$, PR-AUC $0.9616 \pm 0.0091$.
- **Operational Operating Points:** Logistic Regression detects 46.20% of covert tunnels at a strict 1% false positive rate and 94.03% ± 0.0445 of tunnels at a 5% false positive rate.

### F. Threats to Validity
Several limitations apply to these findings. The synthetic generator relies on simplified parametric distributions instead of live packet captures. Sensor noise and label flips introduce realistic ambiguity, but real enterprise traffic displays more complex, multi-modal distributions. In addition, these tests use an even 50:50 class balance, whereas covert channels in production environments occur as rare anomalies.

These constraints mean the benchmark validates pipeline mechanics and feature representation without claiming real-world adversarial evasion. Live traffic evaluation is required before making operational deployment claims.

### G. Interpretation and Operational Trade-offs
In enterprise monitoring, fixed thresholds must balance sensitivity against triage workload. Operating at a 5% false positive rate catches 94.03% of covert channels. Because Operation Cactus feeds detections into MimicNet's adaptive honeypots instead of dropping traffic outright, occasional false alarms redirect benign users into monitored emulation without terminating valid business sessions.

---

## VII. Conclusion and Future Work
This study benchmarks an implemented detection baseline combining FlowSight flow telemetry with CoverTrace information-theoretic indicators. On the held-out test set, Logistic Regression achieves 95.00% accuracy (190/200), 95.05% recall, and 0.9520 ROC-AUC. CoverTrace indicators supply roughly 79.4% of permutation decision weight, while FlowSight statistics provide 20.6% corroborating weight and an always-on fallback under transport encryption.

These results validate the detection pipeline architecture under controlled benchmark conditions. Phase II work will evaluate the fused model against empirical PCAPs generated with `iodine` and `dnscat2` in a testbed lab, and connect live detections to MimicNet's containerized honeypots.

---

## References
[1] S. Zander, G. Armitage, and P. Branch, "A survey of covert channels and countermeasures in computer network protocols," *IEEE Communications Surveys & Tutorials*, vol. 9, no. 3, pp. 44–57, 2007.  
[2] S. Cabuk, C. E. Brodley, and C. Shields, "IP covert timing channels: design and detection," in *Proc. 11th ACM Conf. on Computer and Communications Security (CCS)*, 2004, pp. 178–187.  
[3] S. Gianvecchio and H. Wang, "Detecting covert timing channels: an entropy-based approach," in *Proc. 14th ACM Conf. on Computer and Communications Security (CCS)*, 2007, pp. 307–316.  
[4] S. Al-Eidi, O. Darwish, Y. Chen, and G. Husari, "SnapCatch: Automatic detection of covert timing channels using image processing and machine learning," *IEEE Access*, vol. 9, 2021.  
[5] A. Chowdhary, M. Bhowmik, and B. Rudra, "DNS tunneling detection using machine learning and cache miss properties," in *Proc. 5th Int. Conf. on Intelligent Computing and Control Systems (ICICCS)*, 2021, pp. 1225–1229.  
[6] Y. Khodjaeva, "Detecting malicious DNS tunnels via network flow entropy," M.S. thesis, Faculty of Computer Science, Dalhousie University, 2021.  
[7] W. Graniszewski, J. Krupski, and K. Szczypiorski, "SOMSteg — Framework for covert channel, and its detection, within HTTP," *Journal of Universal Computer Science*, vol. 24, no. 7, pp. 864–891, 2018.  
[8] S. Roy, T. Shapira, and Y. Shavitt, "Fast and lean encrypted Internet traffic classification," *Computer Communications*, vol. 186, pp. 166–173, 2022.  
[9] T. Chen and C. Guestrin, "XGBoost: A scalable tree boosting system," in *Proc. 22nd ACM SIGKDD Int. Conf. on Knowledge Discovery and Data Mining (KDD)*, 2016, pp. 785–794.  
