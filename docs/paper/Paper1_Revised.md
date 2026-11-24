# Operation Cactus: Behavioral Traffic Analysis and Covert Channel Detection for Encrypted Network Threats

**A Synthetic Baseline Benchmark of Gradient-Boosted, Kernel, and Linear Classifiers for the FlowSight and CoverTrace Detection Modules**

**Ayush Rathod, Sharukh Khan, Shivansh Tripathi, Bhargav Moray, Gerard Deepak, Shalini Ranjan**  
*Department of Computer Science & Engineering (Cyber Security), Dayananda Sagar Academy of Technology and Management, Bengaluru, India*

---

## Abstract
This paper presents an implemented detection baseline for Operation Cactus, a network threat detection middleware combining flow-level behavioral traffic analysis (FlowSight) with information-theoretic covert channel detection (CoverTrace). Because deep packet inspection (DPI) fails against encrypted transport protocols and standard intrusion detection systems do not reliably surface low-throughput covert exfiltration channels, this work evaluates whether an eight-dimensional fused representation—four passive flow-level statistics and four application/structural covert-channel indicators—can separate benign network traffic from covert-channel flows. Three classification algorithms—XGBoost (Extreme Gradient Boosting), Support Vector Machines (SVM) with an RBF kernel, and L2-regularized Logistic Regression (LR)—are evaluated on a controlled, synthetic dataset of 1,000 instances. The dataset is generated with 500 benign and 500 covert-channel instances before being subjected to 4% Gaussian measurement jitter per feature and 4% random label flips (resulting in 496 benign and 504 covert instances). Under an 80:20 stratified split, the held-out test partition comprises exactly 200 instances (99 benign and 101 covert). On this partition, Logistic Regression achieves 95.00% accuracy (190/200), 95.05% recall, 0.9520 ROC-AUC, and 0.9554 PR-AUC; SVM achieves 95.00% accuracy, 95.05% recall, and 0.9364 ROC-AUC; and XGBoost achieves 94.50% accuracy, 94.06% recall, and 0.9377 ROC-AUC. An ablation study reveals that a simple single-feature entropy threshold achieves 92.00% accuracy, FlowSight-only features achieve 94.50% accuracy (0.9449 ROC-AUC), CoverTrace-only features achieve 95.00% accuracy (0.9517 ROC-AUC), and the fused representation delivers the highest overall discrimination (0.9520 ROC-AUC). Permutation feature importance establishes that CoverTrace indicators account for 79.4% of decision importance while FlowSight flow statistics account for 20.6%. Across a 10-seed repeated evaluation, Logistic Regression achieves a mean accuracy of $0.9625 \pm 0.0053$ and a true positive rate of $0.9403 \pm 0.0445$ at a 5% false-positive rate. This study establishes an implemented detection-layer baseline; live packet capture, honeypot emulation (MimicNet), and empirical evaluation on lab-captured tunneling tools are addressed in subsequent project phases.

*Index Terms*—covert channel detection, encrypted network traffic analysis, DNS tunneling, information-theoretic detection, Shannon entropy, chi-square timing tests, machine learning baseline, ablation analysis, threat modeling.

---

## I. Introduction
Security operations teams face diminishing visibility into enterprise network perimeters as transport-layer encryption (TLS 1.3, QUIC, DoH, DoT) becomes pervasive. Traditional perimeter defenses relying on payload inspection cannot examine encrypted packet contents. Attackers exploit this blind spot by establishing low-throughput covert timing and storage channels—such as DNS subdomain encapsulation, ICMP echo timing modulation, and HTTP header steganography—to exfiltrate intellectual property or conduct command-and-control (C2) communication without tripping signature-based intrusion detection systems.

Operation Cactus addresses this visibility gap through two complementary detection modules:
1. **FlowSight:** A metadata-only module that observes packet sizes, inter-arrival times, and burst cadences without decrypting payloads, preserving visibility across encrypted sessions.
2. **CoverTrace:** An information-theoretic and structural analysis module that quantifies character entropy in DNS queries, evaluates goodness-of-fit deviations in ICMP inter-ping timings, and identifies non-standard HTTP headers and protocol format anomalies.

The objective of this paper is to benchmark an implemented baseline classifier combining FlowSight's flow-level telemetry with CoverTrace's covert-channel indicators on a controlled synthetic dataset. We investigate two core research questions:
- **RQ1:** Can a unified linear or non-linear classifier trained on a fused eight-dimensional feature representation reliably discriminate covert-channel flows from benign traffic under controlled measurement and label noise?
- **RQ2:** How much discriminative weight is contributed by passive flow statistics versus application-level covert-channel indicators, and what performance trade-off emerges when individual modules are ablated?

A companion deception module, **MimicNet**, dynamically redirects confirmed malicious entities into containerized honeypots. MimicNet is scoped separately from this passive detection study.

---

## II. Related Work
Encrypted traffic classification primarily relies on flow statistical attributes. Roy et al. [8] demonstrated that packet length distributions and inter-arrival timing provide sufficient signal for low-latency classification of encrypted flows without payload inspection, providing theoretical justification for FlowSight's metadata-driven architecture.

Covert channel detection has progressed from ad-hoc thresholding to statistical and information-theoretic tests. Cabuk et al. [2] introduced IP covert timing channel detection using inter-packet delay variance. Gianvecchio and Wang [3] proved that Shannon entropy and conditional entropy measures generalize across varied timing modulation schemes by detecting subtle deviations from natural renewal processes. SnapCatch [4] demonstrated machine-learning-based classification of covert channels by transforming inter-packet delays into visual state matrices.

For DNS tunneling, Chowdhary et al. [5] combined recursive cache-miss dynamics with lexical query classification to detect exfiltration channels. Khodjaeva [6] established that augmenting NetFlow records with flow-level character entropy significantly improves Decision Tree and Random Forest detection of DNS-over-HTTPS (DoH) tunnels. Graniszewski et al. [7] evaluated covert communication via HTTP headers (SOMSteg), motivating CoverTrace's inclusion of header anomaly scoring.

Existing literature either benchmarks flow metadata on general encrypted traffic or analyzes single covert protocols in isolation. This study provides an integrated baseline evaluating both feature families within a unified, reproducible benchmarking protocol.

---

## III. Problem Statement
In covert channel detection, false negatives allow unmonitored data exfiltration, while false alarms impose operational triage overhead on security analysts. In real-world enterprise networks, covert traffic represents an extreme minority class relative to benign volume. A practical detector must maintain high covert recall while minimizing false alarms at low false-positive operating points.

This work benchmarks three candidate classifiers—Logistic Regression (linear baseline), Support Vector Machines (kernel method), and XGBoost (gradient-boosted tree ensemble)—under identical preprocessing, scaling, and feature subsets to measure baseline separability, module importance, and error trade-offs before deployment on live network telemetry.

---

## IV. Methodology

### A. Synthetic Dataset Generation and Noise Model
To ensure complete reproducibility, the dataset is synthesized using a deterministic script (`eval/paper_baseline.py`, seed 42) implementing explicit parametric distributions. The generator synthesizes 1,000 total instances, balanced initially between 500 benign instances and 500 covert-channel instances (Table I).

#### Feature Specification and Parameter Distributions
Each feature is drawn from independent normal distributions $\mathcal{N}(\mu, \sigma^2)$ parameterized to reflect empirical network behavior, followed by physical boundary clipping:
1. `flow_avg_pkt_size_log`: $\ln(\text{mean packet length in bytes})$. Benign $\mu = 6.20$ ($\approx 493$ B), $\sigma = 0.60$; Covert $\mu = 4.80$ ($\approx 121$ B), $\sigma = 0.40$; clipped to $[2.0, 9.0]$.
2. `flow_pkt_size_variance`: Packet size sample variance in $\text{bytes}^2$. Benign $\mu = 65000$, $\sigma = 20000$; Covert $\mu = 15000$, $\sigma = 5000$; clipped to $[100.0, \infty)$.
3. `flow_iat_mean_ms`: Mean inter-arrival time in milliseconds. Benign $\mu = 320.0$, $\sigma = 100.0$; Covert $\mu = 100.0$, $\sigma = 30.0$; clipped to $[1.0, \infty)$.
4. `flow_burst_ratio`: Proportion of packet gaps $< 20.0$ ms. Benign $\mu = 0.25$, $\sigma = 0.10$; Covert $\mu = 0.62$, $\sigma = 0.12$; clipped to $[0.0, 1.0]$.
5. `dns_subdomain_entropy`: Shannon entropy in bits. Benign $\mu = 2.15$, $\sigma = 0.45$; Covert $\mu = 4.20$, $\sigma = 0.35$; clipped to $[0.0, 5.0]$.
6. `icmp_timing_chi2`: Goodness-of-fit statistic against standard 1.0s ping cadence. Benign $\mu = 3.2$, $\sigma = 1.4$; Covert $\mu = 16.5$, $\sigma = 4.0$; clipped to $[0.0, \infty)$.
7. `http_header_anomaly_score`: Anomaly index in $[0.0, 1.0]$. Benign $\mu = 0.08$, $\sigma = 0.05$; Covert $\mu = 0.78$, $\sigma = 0.12$; clipped to $[0.0, 1.0]$.
8. `protocol_struct_deviation`: Structural RFC deviation index in $[0.0, 1.0]$. Benign $\mu = 0.06$, $\sigma = 0.04$; Covert $\mu = 0.70$, $\sigma = 0.14$; clipped to $[0.0, 1.0]$.

#### Noise Procedure
To emulate real-world sensor noise and labeling imperfection:
- **Measurement Jitter:** 4% Gaussian relative jitter ($\mathbf{x} \leftarrow \mathbf{x} + \mathcal{N}(0, (0.04 \cdot \sigma_x)^2)$) is injected into each feature, followed by re-clipping to valid physical bounds.
- **Label Flips:** Exactly 4% of instances (40 of 1,000) have their binary labels inverted prior to data splitting. Random assignment under seed 42 flips 22 benign labels to covert and 18 covert labels to benign, producing a post-noise distribution of 496 benign and 504 covert records.

### B. Data Partitioning and Preprocessing
The dataset is split into an 80% training partition (800 records) and a 20% held-out test partition (200 records) using stratified sampling on the noisy ground truth. This yields a test set of **exactly 99 benign-labelled instances and 101 covert-channel-labelled instances**.

Feature scaling is performed using `StandardScaler`. The mean and standard deviation are fitted strictly on the 800 training instances and applied to both training and test sets, preventing data leakage. All instance IDs, split assignments, and predictions are persisted to CSV format.

### C. Feature Extraction Specification
To resolve ambiguities in feature calculation on raw network traffic, the feature extraction pipeline is formally specified as follows:
- **Flow Key:** Traffic is grouped by directional 5-tuple: $(\text{src\_ip}, \text{dst\_ip}, \text{src\_port}, \text{dst\_port}, \text{protocol})$.
- **Flow Window:** Evaluated over active flow duration or sliding windows of $W = 30.0$ seconds.
- **Burst Definition:** An inter-arrival time $\Delta t < \tau_{\text{burst}} = 20.0$ ms.
- **DNS Entropy Normalization:** Shannon entropy $H = -\sum_{i=1}^k p_i \log_2 p_i$ computed on character frequencies of subdomain labels (excluding domain and TLD). A length threshold condition is enforced: subdomains with length $< 12$ characters return $H = 0.0$ to eliminate small-sample variance from standard hostnames (e.g., `mail`, `api`).
- **ICMP Timing $\chi^2$ Test:** Delays between consecutive ICMP echo requests are partitioned into 5 bins ($[0, 0.7e), [0.7e, 0.95e), [0.95e, 1.05e), [1.05e, 1.3e), [1.3e, \infty)$) where $e = 1000$ ms. The test statistic $\chi^2 = \sum \frac{(O_i - E_i)^2}{E_i}$ is computed only when sample size $N \ge 20$ pings exist within the window; otherwise, it returns 0.0.
- **HTTP Header Anomaly Scoring:** Evaluated as $S_{\text{http}} = \min(1.0, \Delta_{\text{covert}} + \Delta_{\text{missing}} + \Delta_{\text{custom}})$, where presence of covert tunneling prefixes (`x-data`, `x-tunnel`, `x-exfil`) adds $+0.60$, absence of standard browser headers (`Host`, `User-Agent`) adds $+0.30$, and excessive custom headers add $+0.10$. Non-HTTP traffic returns 0.0.
- **Protocol Structural Deviation:** Evaluated based on payload-to-packet length ratio (average packet size $< 64$ bytes across $\ge 10$ packets adds $+0.40$) and non-standard TCP/IP flag combinations.

### D. Threat Model and Observability Matrix
A critical limitation of deep application inspection is transport encryption. CoverTrace features are not universally observable from an un-intercepted network tap when traffic is encrypted under TLS 1.3, DNS-over-HTTPS (DoH), or DNS-over-TLS (DoT). Table VII defines the observability matrix across operational collection points.

When monitoring an encrypted flow on a passive network tap, unobservable CoverTrace features are assigned a neutral default value (0.0) and flagged in a boolean `missing_mask`. FlowSight features remain 100% observable across all monitoring points.

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
All three classifiers were evaluated on the identical 200-record test set (99 benign, 101 covert). Table III summarizes classification performance.

### TABLE III: PERFORMANCE COMPARISON ON HELD-OUT SYNTHETIC TEST SET
| Model | Accuracy | Precision | Recall | F1-Score | Specificity | ROC-AUC | PR-AUC | Confusion Matrix |
|---|---|---|---|---|---|---|---|---|
| **Logistic Regression** | **95.00%** (190/200) | 95.05% | **95.05%** | **95.05%** | **94.95%** | **0.9520** | **0.9554** | TN=94, FP=5, FN=5, TP=96 |
| **SVM (RBF)** | **95.00%** (190/200) | 95.05% | **95.05%** | **95.05%** | **94.95%** | 0.9364 | 0.9318 | TN=94, FP=5, FN=5, TP=96 |
| **XGBoost** | 94.50% (189/200) | 95.00% | 94.06% | 94.53% | **94.95%** | 0.9377 | 0.9004 | TN=94, FP=5, FN=6, TP=95 |

Logistic Regression and SVM achieve identical accuracy (95.00%) with 10 total classification errors (5 false positives, 5 false negatives). Logistic Regression exhibits superior probability calibration, recording the highest ROC-AUC (0.9520) and PR-AUC (0.9554). XGBoost records 11 total errors (5 false positives, 6 false negatives).

### B. Ablation Analysis: Isolating Module Contributions
To evaluate whether multi-module fusion provides measurable benefit over individual modules or simple thresholding, we conducted an ablation study across identical train/test splits (Table IV).

### TABLE IV: ABLATION STUDY & MODEL COMPARISON
| Configuration | Accuracy | Precision | Recall | F1-Score | Specificity | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|
| FlowSight-only (LR, 4 feats) | 94.50% | 94.12% | 95.05% | 94.58% | 93.94% | 0.9449 | 0.9363 |
| CoverTrace-only (LR, 4 feats) | 95.00% | 95.05% | 95.05% | 95.05% | 94.95% | 0.9517 | 0.9572 |
| **Fused Model (LR, 8 feats)** | **95.00%** | **95.05%** | **95.05%** | **95.05%** | **94.95%** | **0.9520** | 0.9554 |
| Simple Entropy Threshold ($H \ge 3.5$) | 92.00% | 92.93% | 91.09% | 92.00% | 92.93% | 0.9336 | 0.9332 |

#### Observations from Ablation
1. **Fusion vs. Single Threshold:** The fused model outperforms the simple entropy threshold by $+3.00\%$ accuracy and $+3.96\%$ recall, demonstrating that flow statistics and multi-protocol indicators capture tunneling behavior that single-feature thresholding misses.
2. **FlowSight vs. CoverTrace:** CoverTrace features provide higher standalone discrimination (0.9517 AUC vs 0.9449 AUC for FlowSight). However, FlowSight provides a viable degraded-mode fallback (94.50% accuracy) when CoverTrace indicators are unobservable due to end-to-end encryption.
3. **Synergy:** The fused model achieves the highest overall ROC-AUC (0.9520).

### C. Feature Importance Analysis
We extracted tree-based gain importance from XGBoost and computed model-agnostic permutation importance on the held-out test partition over 10 random shuffles (Table V).

### TABLE V: FEATURE IMPORTANCE ANALYSIS (XGBOOST)
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

CoverTrace features account for 88.9% of tree gain importance and 79.4% of held-out permutation importance, confirming that application structural and information-theoretic indicators provide the primary discriminative signal, while FlowSight features contribute secondary corroboration.

### D. Uncertainty Quantification: Multi-Seed Evaluation
To evaluate stability beyond a single fixed seed, we repeated data generation, label flipping, and model training across 10 independent random seeds (seeds 42 through 51). Table VI reports mean performance and 95% confidence intervals ($1.96 \cdot \frac{\sigma}{\sqrt{N}}$).

### TABLE VI: REPEATED-TRIAL CONFIDENCE INTERVALS (10 SEEDS: 42–51)
| Model | Metric | Mean ± 95% Confidence Interval | Standard Deviation |
|---|---|---|---|
| **Logistic Regression** | Accuracy | $0.9625 \pm 0.0053$ | 0.0086 |
| | Recall | $0.9621 \pm 0.0118$ | 0.0190 |
| | F1-Score | $0.9625 \pm 0.0054$ | 0.0087 |
| | ROC-AUC | $0.9652 \pm 0.0059$ | 0.0095 |
| | PR-AUC | $0.9616 \pm 0.0091$ | 0.0147 |
| | TPR @ 1% FPR | $0.4620 \pm 0.1086$ | 0.1752 |
| | TPR @ 5% FPR | $0.9403 \pm 0.0445$ | 0.0717 |
| **SVM (RBF)** | Accuracy | $0.9625 \pm 0.0053$ | 0.0086 |
| | Recall | $0.9621 \pm 0.0118$ | 0.0190 |
| | F1-Score | $0.9625 \pm 0.0054$ | 0.0087 |
| | ROC-AUC | $0.9608 \pm 0.0090$ | 0.0146 |
| | PR-AUC | $0.9573 \pm 0.0112$ | 0.0181 |
| | TPR @ 1% FPR | $0.4122 \pm 0.1687$ | 0.2722 |
| | TPR @ 5% FPR | $0.9135 \pm 0.0827$ | 0.1334 |
| **XGBoost** | Accuracy | $0.9605 \pm 0.0054$ | 0.0086 |
| | Recall | $0.9601 \pm 0.0118$ | 0.0191 |
| | F1-Score | $0.9605 \pm 0.0055$ | 0.0088 |
| | ROC-AUC | $0.9636 \pm 0.0082$ | 0.0132 |
| | PR-AUC | $0.9571 \pm 0.0138$ | 0.0222 |
| | TPR @ 1% FPR | $0.4967 \pm 0.1747$ | 0.2818 |
| | TPR @ 5% FPR | $0.9136 \pm 0.0899$ | 0.1451 |

### E. Error Trade-offs and Operational Threshold Selection
In enterprise threat monitoring, decision thresholds must balance false-alarm suppression with detection sensitivity:
- At a strict operating point of **1% False Positive Rate (FPR)**, Logistic Regression detects $46.2\%$ of covert tunnels, while XGBoost detects $49.7\%$.
- Relaxing the threshold to a **5% False Positive Rate (FPR)** raises Logistic Regression recall to **$94.03\%$**, capturing the vast majority of exfiltration attempts.
- Because Operation Cactus incorporates an adaptive honeypot (MimicNet) downstream of detection, a modest false-alarm rate at the detector layer is acceptable: suspect entities are diverted into isolated honeypots rather than outright blocked, allowing interactive confirmation without disrupting benign user sessions.

---

## VII. Threat Model & Observability Matrix

### TABLE VII: COVERTRACE FEATURE OBSERVABILITY BY COLLECTION POINT
| Feature | Passive Tap (Cleartext) | Passive Tap (TLS / DoH) | DNS Resolver Tap | Decrypting TLS Proxy / Endpoint | Missing Handling on Passive Tap |
|---|---|---|---|---|---|
| `flow_avg_pkt_size_log` | Observable | Observable | Observable | Observable | n/a (Always observable) |
| `flow_pkt_size_variance` | Observable | Observable | Observable | Observable | n/a (Always observable) |
| `flow_iat_mean_ms` | Observable | Observable | Observable | Observable | n/a (Always observable) |
| `flow_burst_ratio` | Observable | Observable | Observable | Observable | n/a (Always observable) |
| `dns_subdomain_entropy` | Observable | **Unobservable** | Observable | Observable | Impute 0.0, set `missing_mask` |
| `icmp_timing_chi2` | Observable | Observable (Cleartext ICMP) | Unobservable | Observable | Impute 0.0, require $N \ge 20$ |
| `http_header_anomaly_score` | Observable | **Unobservable** | Unobservable | Observable | Impute 0.0, set `missing_mask` |
| `protocol_struct_deviation` | Observable | Observable (L3/L4 framing) | Observable | Observable | Degraded calculation on L3/L4 |

---

## VIII. Conclusion and Future Work
This paper established an implemented baseline benchmark for the detection layer of Operation Cactus. By evaluating Logistic Regression, Support Vector Machines, and XGBoost on an eight-dimensional fused representation combining FlowSight's flow statistics with CoverTrace's information-theoretic indicators, we demonstrated:
1. Logistic Regression provides the most reliable linear baseline, achieving $0.9625 \pm 0.0053$ mean accuracy and $0.9652 \pm 0.0059$ ROC-AUC over 10 repeated seeds.
2. CoverTrace features supply approximately 79.4% of permutation decision weight, while FlowSight features provide 20.6% corroborating signal and offer a 94.50% accurate fallback when encryption blinds application-layer inspection.
3. Feature extraction rules, sample-size thresholds ($N \ge 20$ for ICMP $\chi^2$, length $\ge 12$ for DNS entropy), and observability limitations under DoH/TLS were formally defined and tested on controlled traffic.

### Scope and Boundaries
These results reflect controlled synthetic benchmark conditions designed to validate pipeline architecture and feature representations. They do not claim field validation against advanced evasive adversaries. Ongoing and planned Phase-II work includes:
- Evaluating the fused model against empirical lab captures generated with `iodine` and `dnscat2` alongside hard-benign enterprise captures.
- Retraining the baseline on real network flow records within the Phase-II evaluation harness.
- Linking the detection pipeline to MimicNet's automated honeypot engagement engine.

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
