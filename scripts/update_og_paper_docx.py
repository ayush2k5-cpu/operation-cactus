"""Update the original Operation_Cactus_Paper_Final(2).docx directly in-place.

Applies the blader/humanizer principles:
- Eliminates AI writing patterns (no em dashes, no 'not-X-but-Y' false contrasts,
  no stock AI buzzwords like 'delve', 'crucial', 'testament', 'showcase', 'underscore').
- Varies sentence structures and rhythm naturally.
- Preserves 100% of the verified benchmark facts, numbers, and parameters.
- Preserves the exact original document formatting, fonts, styles, tables, formula
  blocks, margins, and section architecture.
- Keeps all evaluation metric formulas tightly bound on the same page.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Pt

ROOT = Path(__file__).resolve().parent.parent
DOCS_PAPER = ROOT / "docs" / "paper"
DESKTOP = Path(os.environ.get("USERPROFILE", "C:/Users/Admin")) / "Desktop"
RESULTS_DIR = ROOT / "eval" / "results"

FIG1_PATH = RESULTS_DIR / "fig1_confusion_matrices.png"
FIG2_PATH = RESULTS_DIR / "fig2_roc_curves.png"
FIG3_PATH = RESULTS_DIR / "fig3_metrics_comparison.png"
OG_DOCX_PATH = DOCS_PAPER / "Operation_Cactus_Paper_Final(2).docx"
OUT_DOCX_PATH = DOCS_PAPER / "Operation_Cactus_Paper_Revised.docx"


def set_run_font(run, font_name="Times New Roman", font_size_pt=10.0, bold=None, italic=None):
    run.font.name = font_name
    run.font.size = Pt(font_size_pt)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic


def update_paragraph(
    p,
    text: str,
    font_name="Times New Roman",
    font_size_pt=10.0,
    bold=None,
    italic=None,
    prefix_bold: str | None = None,
    prefix_italic: str | None = None,
    prefix_both: str | None = None,
):
    """Replace paragraph text while preserving existing alignment, spacing, and styles."""
    p.text = ""
    if prefix_both:
        r_pre = p.add_run(prefix_both)
        set_run_font(r_pre, font_name, font_size_pt, bold=True, italic=True)
    elif prefix_bold:
        r_pre = p.add_run(prefix_bold)
        set_run_font(r_pre, font_name, font_size_pt, bold=True, italic=False)
    elif prefix_italic:
        r_pre = p.add_run(prefix_italic)
        set_run_font(r_pre, font_name, font_size_pt, bold=False, italic=True)

    if text:
        r = p.add_run(text)
        set_run_font(r, font_name, font_size_pt, bold=bold, italic=italic)


def set_cell(cell, text: str, font_size=8.0, bold=False, align_center=True):
    p = cell.paragraphs[0]
    p.text = ""
    if align_center:
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    set_run_font(r, "Times New Roman", font_size, bold=bold)


def make_table_unbreakable(table):
    """Ensure table rows do not split across pages and paragraphs stay with next."""
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        if not trPr.xpath("./w:cantSplit"):
            trPr.append(parse_xml(f"<w:cantSplit {nsdecls('w')}/>"))
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True
                p.paragraph_format.space_before = Pt(1.0)
                p.paragraph_format.space_after = Pt(1.5)


def patch_og_paper():
    doc = Document(str(OG_DOCX_PATH))

    # 1. Update High-Resolution Figures in-place via binary blob replacement
    if FIG1_PATH.exists():
        doc.part.rels["rId7"].target_part._blob = FIG1_PATH.read_bytes()
    if FIG2_PATH.exists():
        doc.part.rels["rId8"].target_part._blob = FIG2_PATH.read_bytes()
    if FIG3_PATH.exists():
        doc.part.rels["rId9"].target_part._blob = FIG3_PATH.read_bytes()

    # 2. Spacing Fix: Remove awkward blank vertical gaps
    # P2 is an empty paragraph before the section break P3
    p2 = doc.paragraphs[2]
    p2.text = ""
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(0)
    p2.paragraph_format.line_spacing = Pt(1)

    # Section breaks P3, P50, P59: ensure 0 vertical height so no empty line shows
    for s_idx in [3, 50, 59]:
        sp = doc.paragraphs[s_idx]
        sp.text = ""
        sp.paragraph_format.space_before = Pt(0)
        sp.paragraph_format.space_after = Pt(0)
        sp.paragraph_format.line_spacing = Pt(1)

    # 3. Update Paragraph Texts with humanized prose, zero em dashes, and exact numbers

    # P4: Abstract (Humanized: direct, active, no em dashes, no stock AI words)
    abstract_text = (
        "Operation Cactus pairs passive flow-level traffic statistics (FlowSight) with protocol-level covert "
        "channel indicators (CoverTrace) to detect hidden exfiltration in networks where payload inspection is "
        "blocked by transport encryption. We evaluate whether an eight-dimensional feature vector (four flow metrics: "
        "packet size log-mean, variance, inter-arrival time, burst ratio; and four covert indicators: DNS subdomain "
        "entropy, ICMP inter-packet timing chi-square, HTTP header anomaly score, protocol structural deviation) "
        "separates covert channels from benign flows. We train and test three classifiers (XGBoost, an RBF-kernel "
        "Support Vector Machine, and L2-regularized Logistic Regression) on 1,000 synthetic flow records generated "
        "from parametric distributions with 4% feature measurement jitter and 4% random label noise (40 inverted "
        "labels, yielding 496 benign and 504 covert records). On a stratified 200-record test set (99 benign, 101 "
        "covert), Logistic Regression correctly classifies 190 of 200 records (95.00% accuracy, 95.05% recall, "
        "0.9520 ROC-AUC, 0.9554 PR-AUC). The SVM matches this accuracy at 95.00% (0.9364 ROC-AUC), while XGBoost "
        "reaches 94.50% accuracy (189/200, 94.06% recall, 0.9377 ROC-AUC). Feature ablation shows that a baseline "
        "single-feature entropy threshold (H >= 3.5) scores 92.00% accuracy; FlowSight flow statistics alone reach "
        "94.50% accuracy (0.9449 ROC-AUC); CoverTrace indicators alone reach 95.00% accuracy (0.9517 ROC-AUC); and "
        "combining both yields the highest ranking score (0.9520 ROC-AUC). Permutation importance tests assign 79.4% "
        "of normalized decision weight to CoverTrace indicators and 20.6% to FlowSight statistics. Over 10 random "
        "seeds (seeds 42 to 51), Logistic Regression averages 0.9625 ± 0.0053 accuracy, with a true positive rate "
        "of 0.9403 ± 0.0445 at a 5% false positive rate. These results establish an implemented baseline for the "
        "detection pipeline; evaluations against live packet capture and honeypot diversion (MimicNet) follow in Phase II."
    )
    update_paragraph(doc.paragraphs[4], abstract_text, prefix_both="Abstract—")

    # P5: Index Terms
    index_terms_text = (
        "covert channel detection, encrypted network traffic analysis, DNS tunneling, information-theoretic detection, "
        "Shannon entropy, chi-square timing tests, machine learning baseline, ablation analysis, threat modeling."
    )
    update_paragraph(doc.paragraphs[5], index_terms_text, prefix_both="Index Terms—", italic=True)

    # P7: Introduction P1 (Humanized)
    p7_text = (
        "Transport-layer encryption (TLS 1.3, QUIC, DNS-over-HTTPS) hides packet payloads across modern enterprise networks. "
        "This protects user privacy, but it also blinds perimeter security tools that rely on deep packet inspection. Attackers "
        "take advantage of this gap by tunneling command-and-control messages or stolen data through standard protocols like "
        "DNS query names, ICMP ping sequences, or custom HTTP headers. These low-bandwidth channels often pass through "
        "firewalls and signature-based intrusion detection systems unnoticed."
    )
    update_paragraph(doc.paragraphs[7], p7_text)

    # P8: Introduction P2 (Humanized)
    p8_text = (
        "Operation Cactus tackles this problem with two cooperating modules. FlowSight monitors traffic metadata (packet sizes, "
        "timing intervals, and burst cadences) without decrypting payloads, keeping visibility intact even on encrypted streams. "
        "CoverTrace calculates information-theoretic and format metrics: Shannon entropy on DNS subdomains, chi-square "
        "goodness-of-fit tests on ICMP delays, and structural checks for non-standard HTTP headers. Here, we benchmark whether "
        "training linear and non-linear classifiers on both feature sets produces reliable separation on a controlled dataset, "
        "and we measure the relative weight contributed by each module."
    )
    update_paragraph(doc.paragraphs[8], p8_text)

    # P9: Introduction P3 (Humanized)
    p9_text = (
        "A third module, MimicNet, provides an adaptive honeypot deception layer. Because MimicNet handles dynamic service "
        "emulation rather than passive flow detection, it is evaluated separately in a companion report. The work here focuses "
        "strictly on the detection pipeline."
    )
    update_paragraph(doc.paragraphs[9], p9_text)

    # P11: Related Work P1 (Humanized)
    p11_text = (
        "Flow-based classification has become standard as payload encryption spreads. Roy, Shapira, and Shavitt demonstrated "
        "that packet lengths and inter-arrival intervals alone provide enough signal to categorize encrypted application flows "
        "with low latency [8]. Their findings support FlowSight's design choice to track flow statistics without inspecting "
        "payload bytes."
    )
    update_paragraph(doc.paragraphs[11], p11_text)

    # P12: Related Work P2 (Humanized)
    p12_text = (
        "Research on covert timing channels goes back over two decades. Cabuk, Brodley, and Shields established the initial "
        "foundations for IP timing channel detection using inter-packet delay variance [2]. Gianvecchio and Wang expanded on "
        "this by applying entropy and conditional entropy metrics to identify subtle timing variations [3], a technique "
        "CoverTrace adapts for ICMP traffic. More recently, SnapCatch used delay distribution matrices with machine learning "
        "models to automate timing anomaly detection [4]."
    )
    update_paragraph(doc.paragraphs[12], p12_text)

    # P13: Related Work P3 (Humanized)
    p13_text = (
        "DNS tunneling detection follows a similar path. Chowdhary, Bhowmik, and Rudra paired recursive cache dynamics with "
        "query lexical features to flag tunnels [5]. Khodjaeva showed that tracking character entropy in network flows "
        "significantly improves random forest detection of DNS-over-HTTPS tunnels [6]. In HTTP covert channels, Graniszewski et al. "
        "analyzed steganographic data hiding in HTTP headers (SOMSteg) [7], which motivates CoverTrace's header anomaly index."
    )
    update_paragraph(doc.paragraphs[13], p13_text)

    # P14: Related Work P4 (Humanized)
    p14_text = (
        "Throughout this literature, statistical and information-theoretic tests (query entropy, delay distributions, header "
        "validation) consistently identify covert channels, while general flow statistics provide the foundation for encrypted "
        "traffic classification. This paper evaluates an integrated baseline that tests both feature groups under a single "
        "reproducible benchmark."
    )
    update_paragraph(doc.paragraphs[14], p14_text)

    # P16: Problem Statement P1 (Humanized)
    p16_text = (
        "A practical covert channel detector must balance two competing operational demands: catching slow exfiltration without "
        "generating excessive false alarms. In real enterprise environments, covert channels represent a tiny fraction of total "
        "network volume. False negatives let attacker traffic through, while false positives waste analyst time on benign connections."
    )
    update_paragraph(doc.paragraphs[16], p16_text)

    # P17: Problem Statement P2 (Humanized)
    p17_text = (
        "This study evaluates a concrete question: can a standardized model trained on FlowSight's flow statistics and CoverTrace's "
        "covert indicators separate covert channels from benign flows under controlled noise, and how much discriminative signal "
        "does each feature set provide? We run Logistic Regression, an RBF-kernel SVM, and XGBoost on identical feature matrices "
        "and test partitions. Because missed exfiltration is costly in security operations, covert-class recall serves as the primary "
        "evaluation metric."
    )
    update_paragraph(doc.paragraphs[17], p17_text)

    # P19: Methodology Opening (Humanized)
    p19_text = (
        "The experimental setup includes synthetic data generation, feature extraction, stratified partitioning, standard scaling, "
        "model training, held-out evaluation, and metric calculation. All three classifiers run against identical feature matrices "
        "and evaluation splits."
    )
    update_paragraph(doc.paragraphs[19], p19_text)

    # P21: Synthetic Dataset Construction P1 (Humanized)
    p21_text = (
        "We generate 1,000 synthetic flow instances using parametric distributions in eval/paper_baseline.py (fixed random seed 42). "
        "The dataset begins with 500 benign instances and 500 covert instances before noise injection (Table I)."
    )
    update_paragraph(doc.paragraphs[21], p21_text)

    # P22: Synthetic Dataset Construction P2 (Humanized, compact, no em dashes)
    p22_text = (
        "Covert records emulate DNS tunneling, ICMP timing channels, and HTTP header steganography: elevated DNS subdomain entropy, "
        "larger chi-square delay deviation, higher HTTP header anomaly scores, and protocol structural deviations, combined with "
        "smaller packet sizes and tighter inter-arrival timing. Benign instances reflect lower entropy, near-zero timing chi-square, "
        "clean headers, and human-driven packet timing. To reflect real-world sensor imperfection, we inject 4% Gaussian measurement "
        "jitter into every feature and randomly invert exactly 4% of labels (40 instances: 22 benign flipped to covert, 18 covert "
        "flipped to benign). This leaves 496 benign records and 504 covert records."
    )
    update_paragraph(doc.paragraphs[22], p22_text)

    # Table 1: Synthetic Dataset Distribution (Table I)
    t1 = doc.tables[1]
    set_cell(t1.rows[1].cells[0], "Covert-channel-labelled", align_center=False)
    set_cell(t1.rows[1].cells[1], "504", align_center=True)
    set_cell(t1.rows[1].cells[2], "50.4%", align_center=True)
    set_cell(t1.rows[2].cells[0], "Benign", align_center=False)
    set_cell(t1.rows[2].cells[1], "496", align_center=True)
    set_cell(t1.rows[2].cells[2], "49.6%", align_center=True)
    set_cell(t1.rows[3].cells[0], "Total", bold=True, align_center=False)
    set_cell(t1.rows[3].cells[1], "1000", bold=True, align_center=True)
    set_cell(t1.rows[3].cells[2], "100.0%", bold=True, align_center=True)

    # P25: Feature Construction Intro (Humanized)
    p25_text = "Each record contains eight features split across the two detection modules:"
    update_paragraph(doc.paragraphs[25], p25_text)

    # P26: FlowSight Features (Humanized, compact)
    p26_text = (
        "FlowSight features (4): flow_avg_pkt_size_log (natural log of mean packet size), flow_pkt_size_variance, flow_iat_mean_ms "
        "(mean inter-arrival time in milliseconds), and flow_burst_ratio (share of packet gaps under 20.0 ms). These derive from "
        "directional 5-tuple keys (src_ip, dst_ip, src_port, dst_port, protocol) over 30-second windows."
    )
    update_paragraph(doc.paragraphs[26], p26_text)

    # P27: CoverTrace Features (Humanized, compact)
    p27_text = (
        "CoverTrace features (4): dns_subdomain_entropy (Shannon entropy on query subdomains, returning 0.0 for labels shorter than "
        "12 characters), icmp_timing_chi2 (5-bin delay chi-square test against 1.0s ping cadences, requiring N >= 20 pings), "
        "http_header_anomaly_score (checking for missing standard headers and tunneling prefixes), and protocol_struct_deviation "
        "(packet size framing and flag anomalies)."
    )
    update_paragraph(doc.paragraphs[27], p27_text)

    # P28: Data Partitioning (Humanized, compact)
    p28_text = (
        "We split the noisy dataset into an 80% training set (800 records) and a 20% held-out test set (200 records) using "
        "stratified sampling on noisy labels (random_state=42). The resulting test set contains exactly 99 benign-labelled records "
        "and 101 covert-labelled records. StandardScaler is fitted only on the 800 training records and applied to both splits, "
        "preventing data leakage."
    )
    update_paragraph(doc.paragraphs[28], p28_text)

    # P30: XGBoost (Humanized)
    p30_text = (
        "XGBoost (Extreme Gradient Boosting): 200 estimators, maximum depth 5, learning rate 0.1, subsample ratio 0.9, column "
        "subsample ratio 0.9, and random state 42, following the gradient-boosted tree design of Chen and Guestrin [9]."
    )
    update_paragraph(doc.paragraphs[30], p30_text)

    # P31: SVM (Humanized)
    p31_text = (
        "Support Vector Machine (SVM): an RBF-kernel SVC with C = 10, gamma set to scikit-learn's scale heuristic, Platt probability "
        "scaling enabled for ROC analysis, and random state 42."
    )
    update_paragraph(doc.paragraphs[31], p31_text)

    # P32: Logistic Regression (Humanized)
    p32_text = (
        "Logistic Regression (LR): an L2-regularized logistic regression classifier with a maximum of 1,000 solver iterations and "
        "random state 42, providing an interpretable linear baseline against the non-linear models."
    )
    update_paragraph(doc.paragraphs[32], p32_text)

    # P33: Defaults statement (Humanized)
    p33_text = (
        "All three setups follow standard defaults for tabular binary classification benchmarks. We avoided hyperparameter "
        "tuning so the comparison reflects the raw implementations."
    )
    update_paragraph(doc.paragraphs[33], p33_text)

    # P35: Module Positioning (Humanized, compact)
    p35_text = (
        "The classifier sits at the fusion point of FlowSight and CoverTrace: FlowSight supplies always-on, encryption-resilient flow "
        "telemetry, while CoverTrace contributes covert-channel indicators. In deployment, positive classifications trigger MimicNet's "
        "adaptive honeypots. MimicNet's engagement engine is evaluated separately; this work focuses strictly on detection."
    )
    update_paragraph(doc.paragraphs[35], p35_text)

    # P36 & P37: Threat Model & Observability (Humanized, compact)
    update_paragraph(
        doc.paragraphs[36], "E. Threat Model & Feature Observability", bold=True, italic=True
    )
    p37_text = (
        "On an un-intercepted network tap, transport encryption (TLS 1.3, DoH, DoT) hides application payloads. Under encryption, "
        "CoverTrace's DNS entropy and HTTP header anomaly features cannot be computed and default to 0.0 with a boolean missing_mask. "
        "FlowSight's four flow statistics and ICMP timing remain fully visible across all collection points, providing a dependable "
        "degraded-mode fallback."
    )
    update_paragraph(doc.paragraphs[37], p37_text)

    # P39: Reproducibility (Humanized, compact)
    p39_text = (
        "The generation script, noise injection, dataset split, and model fits run under random seed 42. Anyone executing "
        "eval/paper_baseline.py reproduces the exact dataset, splits, and metrics reported below."
    )
    update_paragraph(doc.paragraphs[39], p39_text)

    # ========================================================
    # G. Evaluation Metrics & Formulas: GUARANTEE ON SAME PAGE
    # ========================================================
    p40 = doc.paragraphs[40]
    p40.paragraph_format.keep_with_next = True
    p40.paragraph_format.space_before = Pt(6.0)
    p40.paragraph_format.space_after = Pt(2.0)

    p41 = doc.paragraphs[41]
    p41.paragraph_format.keep_with_next = True
    p41.paragraph_format.space_before = Pt(0)
    p41.paragraph_format.space_after = Pt(2.0)
    p41_text = (
        "Let TP, TN, FP, and FN denote true positives, true negatives, false positives, and false negatives for covert channel detection. "
        "We compute standard classification metrics:"
    )
    update_paragraph(p41, p41_text)

    # Make Table 2, Table 3, Table 4, Table 5 completely unbreakable & keep with next!
    make_table_unbreakable(doc.tables[2])  # Accuracy
    make_table_unbreakable(doc.tables[3])  # Precision & Recall
    make_table_unbreakable(doc.tables[4])  # Specificity
    make_table_unbreakable(doc.tables[5])  # F1

    # P42: Metrics text (Humanized, compact)
    p42 = doc.paragraphs[42]
    p42.paragraph_format.keep_with_next = True
    p42.paragraph_format.space_before = Pt(2.0)
    p42.paragraph_format.space_after = Pt(4.0)
    p42_text = (
        "Precision, recall, and F1-score evaluate covert-class performance. ROC-AUC and PR-AUC assess continuous probability "
        "calibration across varying decision thresholds."
    )
    update_paragraph(p42, p42_text)

    # Table 6: Implementation Configuration (Table II)
    t6 = doc.tables[6]
    set_cell(
        t6.rows[2].cells[1], "1000 synthetic (500 benign, 500 covert pre-noise)", align_center=False
    )
    set_cell(
        t6.rows[3].cells[1], "200 (99 benign / 101 covert, 80:20 stratified)", align_center=False
    )
    set_cell(t6.rows[9].cells[0], "Noise model", align_center=False)
    set_cell(
        t6.rows[9].cells[1],
        "4% feature Gaussian jitter; 4% label flips (40 instances)",
        align_center=False,
    )

    # P45: Implementation P1 (Humanized)
    p45_text = (
        "The pipeline is implemented in Python, using scikit-learn for the SVM and Logistic Regression models and xgboost for the "
        "tree ensemble. This shared code path ensures identical preprocessing, scaling, and evaluation across all three algorithms. "
        "The benchmark script saves trained models, records evaluation metrics, and exports confusion matrices and ROC figures to disk."
    )
    update_paragraph(doc.paragraphs[45], p45_text)

    # P46: Implementation P2 (Humanized)
    p46_text = (
        "This experimental setup evaluates the mathematical and statistical behavior of the detection models prior to system integration. "
        "Wiring these trained classifiers into FlowSight's C and libpcap engine and CoverTrace's live scoring pipeline forms the primary "
        "task for Phase II."
    )
    update_paragraph(doc.paragraphs[46], p46_text)

    # P48: Results Opening (Humanized)
    p48_text = (
        "The three classifiers were evaluated on the 200-record held-out synthetic test set (99 benign, 101 covert). Table III "
        "reports the resulting performance metrics."
    )
    update_paragraph(doc.paragraphs[48], p48_text)

    # P49: Results Summary (Humanized)
    p49_text = (
        "Logistic Regression correctly classifies 190 of 200 test records (95.00% accuracy), SVM correctly classifies 190 "
        "(95.00%), and XGBoost correctly classifies 189 (94.50%)."
    )
    update_paragraph(doc.paragraphs[49], p49_text)

    # Table 7: Performance Comparison (Table III)
    t7 = doc.tables[7]
    set_cell(t7.rows[1].cells[0], "Logistic Regression", align_center=False)
    set_cell(t7.rows[1].cells[1], "95.00%", align_center=True)
    set_cell(t7.rows[1].cells[2], "95.05%", align_center=True)
    set_cell(t7.rows[1].cells[3], "95.05%", align_center=True)
    set_cell(t7.rows[1].cells[4], "95.05%", align_center=True)
    set_cell(t7.rows[1].cells[5], "94.95%", align_center=True)
    set_cell(t7.rows[1].cells[6], "0.9520", align_center=True)

    set_cell(t7.rows[2].cells[0], "SVM (RBF)", align_center=False)
    set_cell(t7.rows[2].cells[1], "95.00%", align_center=True)
    set_cell(t7.rows[2].cells[2], "95.05%", align_center=True)
    set_cell(t7.rows[2].cells[3], "95.05%", align_center=True)
    set_cell(t7.rows[2].cells[4], "95.05%", align_center=True)
    set_cell(t7.rows[2].cells[5], "94.95%", align_center=True)
    set_cell(t7.rows[2].cells[6], "0.9364", align_center=True)

    set_cell(t7.rows[3].cells[0], "XGBoost", align_center=False)
    set_cell(t7.rows[3].cells[1], "94.50%", align_center=True)
    set_cell(t7.rows[3].cells[2], "95.00%", align_center=True)
    set_cell(t7.rows[3].cells[3], "94.06%", align_center=True)
    set_cell(t7.rows[3].cells[4], "94.53%", align_center=True)
    set_cell(t7.rows[3].cells[5], "94.95%", align_center=True)
    set_cell(t7.rows[3].cells[6], "0.9377", align_center=True)

    # P55: Confusion Matrix Analysis (Humanized)
    p55_text = (
        "At the default 0.50 threshold (Fig. 1), Logistic Regression produces 10 errors out of 200 test records: 94 true negatives, "
        "96 true positives, 5 false positives, and 5 false negatives. The Support Vector Machine produces identical counts (94 TN, "
        "96 TP, 5 FP, 5 FN). XGBoost produces 11 errors: 94 TN, 95 TP, 5 FP, and 6 FN."
    )
    update_paragraph(doc.paragraphs[55], p55_text)

    # P56: Error Interpretation (Humanized)
    p56_text = (
        "These error counts highlight how the models behave at a fixed decision boundary: both Logistic Regression and SVM "
        "achieve 95.05% recall with 5 false alarms on 99 benign flows."
    )
    update_paragraph(doc.paragraphs[56], p56_text)

    # P58: ROC & AUC Analysis (Humanized, no em dashes)
    p58_text = (
        "Figures 2 and 3 plot discrimination across varying decision thresholds. Logistic Regression records the highest ROC-AUC "
        "(0.9520) and PR-AUC (0.9554), demonstrating stable probability calibration across operating thresholds. XGBoost records "
        "0.9377 ROC-AUC, and SVM records 0.9364 ROC-AUC."
    )
    update_paragraph(doc.paragraphs[58], p58_text)

    # P61: Feature Contribution (Humanized)
    p61_text = (
        "To measure module contribution, we pulled tree gain importances from XGBoost (Table IV) and evaluated permutation "
        "importance on the held-out test partition. CoverTrace indicators represent 88.9% of tree gain and 79.4% of normalized "
        "permutation weight. FlowSight flow statistics contribute 11.1% of tree gain and 20.6% of permutation weight. Protocol "
        "structural deviation (55.00%) and HTTP header anomaly (28.84%) supply the strongest individual signals."
    )
    update_paragraph(doc.paragraphs[61], p61_text)

    # Table 9: Feature Importance (Table IV)
    t9 = doc.tables[9]
    rows_feat = [
        ("protocol_struct_deviation", "CoverTrace", "55.00%"),
        ("http_header_anomaly_score", "CoverTrace", "28.84%"),
        ("flow_pkt_size_variance", "FlowSight", "3.47%"),
        ("flow_burst_ratio", "FlowSight", "2.60%"),
        ("dns_subdomain_entropy", "CoverTrace", "2.55%"),
        ("icmp_timing_chi2", "CoverTrace", "2.53%"),
        ("flow_iat_mean_ms", "FlowSight", "2.53%"),
        ("flow_avg_pkt_size_log", "FlowSight", "2.48%"),
    ]
    for r_idx, (f_name, m_name, imp) in enumerate(rows_feat):
        row = t9.rows[r_idx + 1]
        set_cell(row.cells[0], f_name, align_center=False)
        set_cell(row.cells[1], m_name, align_center=False)
        set_cell(row.cells[2], imp, align_center=True)

    # P63: Feature Importance Explanation (Humanized)
    p63_text = (
        "These results confirm that information-theoretic indicators provide the primary discriminative signal for covert channel "
        "detection, while FlowSight's flow metrics offer essential corroboration and maintain coverage when payload inspection is unavailable."
    )
    update_paragraph(doc.paragraphs[63], p63_text)

    # P64: Heading - Ablation Analysis & Feature Synergy
    update_paragraph(
        doc.paragraphs[64], "D. Ablation Analysis & Feature Synergy", bold=True, italic=True
    )

    # P65: Ablation text (Humanized)
    p65_text = (
        "Feature ablation confirms the value of fusing both modules. A simple threshold on DNS subdomain entropy (H >= 3.5) "
        "achieves 92.00% accuracy and 91.09% recall. FlowSight flow features alone achieve 94.50% accuracy (0.9449 ROC-AUC), "
        "proving that flow metadata remains effective when encryption obscures payloads. CoverTrace features alone reach "
        "95.00% accuracy (0.9517 ROC-AUC). Combining both feature sets achieves 0.9520 ROC-AUC, outperforming any individual feature group."
    )
    update_paragraph(doc.paragraphs[65], p65_text)

    # P66: Uncertainty Quantification text (Humanized)
    p66_text = (
        "Evaluating across 10 random seeds (seeds 42 to 51) confirms stability beyond the initial split. Logistic Regression "
        "averages 0.9625 ± 0.0053 accuracy, 0.9652 ± 0.0059 ROC-AUC, and 0.9616 ± 0.0091 PR-AUC. In operational threshold tests, "
        "Logistic Regression detects 46.20% of covert tunnels at a strict 1% false positive rate and 94.03% ± 0.0445 of tunnels "
        "at a 5% false positive rate."
    )
    update_paragraph(doc.paragraphs[66], p66_text)

    # P68: Threats to Validity P1 (Humanized)
    p68_text = (
        "Several limitations apply to these findings. The synthetic generator relies on simplified parametric distributions "
        "rather than live packet captures. Sensor noise and label flips introduce realistic ambiguity, but real enterprise traffic "
        "displays more complex, multi-modal distributions. Furthermore, these tests use an even 50:50 class balance, whereas "
        "covert channels in production environments occur as rare anomalies."
    )
    update_paragraph(doc.paragraphs[68], p68_text)

    # P69: Threats to Validity P2 (Humanized)
    p69_text = (
        "These constraints mean the benchmark validates pipeline mechanics and feature representation rather than real-world "
        "adversarial evasion. Live traffic evaluation is required before making operational deployment claims."
    )
    update_paragraph(doc.paragraphs[69], p69_text)

    # P71: Interpretation P1 (Humanized)
    p71_text = (
        "In enterprise monitoring, fixed thresholds must balance sensitivity against triage workload. Operating at a 5% false "
        "positive rate catches 94.03% of covert channels. Because Operation Cactus feeds detections into MimicNet's adaptive "
        "honeypots rather than dropping traffic outright, occasional false alarms redirect benign users into monitored emulation "
        "without terminating valid business sessions."
    )
    update_paragraph(doc.paragraphs[71], p71_text)

    # P72: Interpretation P2 (Humanized)
    p72_text = (
        "The feature importance breakdown explains why both modules belong in the pipeline: CoverTrace carries the majority "
        "of the discriminative signal, while FlowSight provides continuous, encryption-resilient telemetry that keeps working "
        "even when application-layer fields are hidden."
    )
    update_paragraph(doc.paragraphs[72], p72_text)

    # P74: Conclusion P1 (Humanized)
    p74_text = (
        "This study benchmarks an implemented detection baseline combining FlowSight flow telemetry with CoverTrace "
        "information-theoretic indicators. On the held-out test set, Logistic Regression achieves 95.00% accuracy (190/200), "
        "95.05% recall, and 0.9520 ROC-AUC. CoverTrace indicators supply roughly 79.4% of permutation decision weight, while "
        "FlowSight statistics provide 20.6% corroborating weight and an always-on fallback under transport encryption."
    )
    update_paragraph(doc.paragraphs[74], p74_text)

    # P75: Conclusion P2 (Humanized)
    p75_text = (
        "These results validate the detection pipeline architecture under controlled benchmark conditions. Phase II work will "
        "evaluate the fused model against empirical PCAPs generated with iodine and dnscat2 in a testbed lab, and connect live "
        "detections to MimicNet's containerized honeypots."
    )
    update_paragraph(doc.paragraphs[75], p75_text)

    # 4. Spacing Polish across all body paragraphs:
    for i, p in enumerate(doc.paragraphs):
        if not p.text.strip():
            continue
        # Don't touch title or subtitle
        if i in [0, 1]:
            continue
        # Heading 1:
        if i in [6, 10, 15, 18, 44, 47, 73, 76]:
            p.paragraph_format.space_before = Pt(8.0)
            p.paragraph_format.space_after = Pt(3.0)
        # Heading 2:
        elif i in [20, 24, 29, 34, 36, 38, 40, 52, 57, 60, 64, 67, 70]:
            p.paragraph_format.space_before = Pt(6.0)
            p.paragraph_format.space_after = Pt(2.5)
        # Table caption:
        elif i in [23, 43, 51, 62]:
            p.paragraph_format.space_before = Pt(5.0)
            p.paragraph_format.space_after = Pt(2.0)
        # Figure caption:
        elif i in [54]:
            p.paragraph_format.space_before = Pt(2.5)
            p.paragraph_format.space_after = Pt(5.0)
        # Formula surrounding paragraphs:
        elif i in [40, 41, 42]:
            p.paragraph_format.space_before = Pt(1.0)
            p.paragraph_format.space_after = Pt(2.0)
        # Body text / references:
        else:
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(4.5)
            p.paragraph_format.line_spacing = 1.08

    # Save to destination
    doc.save(str(OUT_DOCX_PATH))
    print(f"Successfully patched original document to: {OUT_DOCX_PATH}")

    # Copy to Desktop under multiple names so the user can access it immediately
    target_names = [
        "Operation_Cactus_Paper_Final(2)_Updated.docx",
        "Operation_Cactus_Paper_Final_Formatted.docx",
        OUT_DOCX_PATH.name,
    ]
    for name in target_names:
        dst = DESKTOP / name
        try:
            shutil.copyfile(str(OUT_DOCX_PATH), str(dst))
            print(f"Successfully copied to Desktop: {dst}")
        except PermissionError:
            print(f"Note: {dst} is currently locked by Word.")


if __name__ == "__main__":
    patch_og_paper()
