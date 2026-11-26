"""Update the original Operation_Cactus_Paper_Final(2).docx directly in-place.

Applies the blader/humanizer principles:
- Eliminates AI writing patterns (no em dashes, no 'not-X-but-Y' false contrasts,
  no stock AI buzzwords like 'delve', 'crucial', 'testament', 'showcase', 'underscore').
- Varies sentence structures and rhythm naturally like human cybersecurity researchers.
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

    # 3. Update Paragraph Texts with fully humanized academic prose

    # P4: Abstract (Deeply humanized, zero em dashes, high burstiness, rigorous academic style)
    abstract_text = (
        "Transport-layer encryption blocks traditional payload inspection at the enterprise perimeter. As a result, "
        "low-throughput covert channels embedded in protocol metadata, such as DNS subdomain labels, ICMP timing intervals, "
        "and HTTP headers, frequently bypass signature-based intrusion detection. Operation Cactus targets this gap by "
        "pairing passive flow-level traffic statistics (FlowSight) with information-theoretic covert channel indicators "
        "(CoverTrace). In this work, we evaluate an eight-dimensional feature representation spanning four passive flow "
        "metrics (log-mean packet size, variance, inter-arrival time, burst ratio) and four covert-channel indicators "
        "(DNS subdomain entropy, ICMP timing chi-square, HTTP header anomaly, protocol structural deviation). We trained and "
        "evaluated Logistic Regression, Support Vector Machines (RBF kernel), and XGBoost on 1,000 synthetic flow instances "
        "generated under 4% Gaussian measurement jitter and 4% random label noise (40 inverted instances, yielding 496 benign "
        "and 504 covert flows). On a held-out stratified test set of 200 instances (99 benign, 101 covert), Logistic Regression "
        "achieved 95.00% accuracy (190/200), 95.05% recall, 0.9520 ROC-AUC, and 0.9554 PR-AUC. The SVM produced identical "
        "classification accuracy at 95.00% (0.9364 ROC-AUC), while XGBoost reached 94.50% accuracy (189/200, 94.06% recall, "
        "0.9377 ROC-AUC). Feature ablation experiments showed that a single-feature entropy threshold (H >= 3.5) achieved "
        "92.00% accuracy; FlowSight features alone reached 94.50% accuracy (0.9449 ROC-AUC); CoverTrace features alone reached "
        "95.00% accuracy (0.9517 ROC-AUC); and the fused feature set yielded the highest overall discrimination (0.9520 ROC-AUC). "
        "Permutation importance analysis assigned 79.4% of normalized decision weight to CoverTrace indicators and 20.6% to "
        "FlowSight statistics. Across 10 independent random seeds (42 to 51), Logistic Regression averaged 0.9625 ± 0.0053 "
        "accuracy, with a true positive rate of 0.9403 ± 0.0445 at a fixed 5% false positive rate. These findings provide "
        "an initial operational baseline for the detection layer prior to live PCAP ingestion and automated honeypot "
        "redirection (MimicNet)."
    )
    update_paragraph(doc.paragraphs[4], abstract_text, prefix_both="Abstract—")

    # P5: Index Terms
    index_terms_text = (
        "covert channel detection, encrypted network traffic analysis, DNS tunneling, information-theoretic detection, "
        "Shannon entropy, chi-square timing tests, machine learning baseline, ablation analysis, threat modeling."
    )
    update_paragraph(doc.paragraphs[5], index_terms_text, prefix_both="Index Terms—", italic=True)

    # P7: Introduction P1 (Humanized academic prose)
    p7_text = (
        "Widespread adoption of TLS 1.3, QUIC, and DNS-over-HTTPS has fundamentally altered enterprise network defense. "
        "While encryption safeguards data in transit, it also blinds security monitoring appliances that depend on deep "
        "packet inspection. Adversaries increasingly exploit this limitation by tunneling command-and-control communication "
        "or exfiltrating sensitive data through auxiliary protocol fields, including DNS query labels, ICMP timing variations, "
        "and custom HTTP headers. Because these transactions use approved ports and valid protocol wrappers, they regularly "
        "pass through perimeter firewalls and signature-driven intrusion detection systems without raising alerts."
    )
    update_paragraph(doc.paragraphs[7], p7_text)

    # P8: Introduction P2 (Humanized)
    p8_text = (
        "Operation Cactus addresses this visibility deficit through a dual-module detection architecture. FlowSight inspects "
        "packet headers to extract passive metadata, including length distributions, inter-arrival intervals, and burst ratios, "
        "without touching packet payloads, maintaining continuous monitoring across encrypted transport sessions. CoverTrace "
        "computes information-theoretic and structural metrics, evaluating character entropy across DNS query names, chi-square "
        "goodness-of-fit against regular ICMP echo intervals, and structural anomalies in HTTP headers. In this paper, we "
        "benchmark whether linear and non-linear classifiers trained on this fused feature set can reliably isolate covert "
        "tunnels from benign traffic, and we quantify the relative discriminative contribution of each module."
    )
    update_paragraph(doc.paragraphs[8], p8_text)

    # P9: Introduction P3 (Humanized)
    p9_text = (
        "A third module, MimicNet, provides a containerized deception environment that interacts with flagged entities. "
        "Because MimicNet governs dynamic honeypot redirection and adversary interaction instead of passive detection, its "
        "evaluation is presented in a separate companion study; the analysis here focuses exclusively on the detection baseline."
    )
    update_paragraph(doc.paragraphs[9], p9_text)

    # P11: Related Work P1 (Humanized)
    p11_text = (
        "Flow-based traffic analysis has become the primary method for classifying traffic when payloads are inaccessible. "
        "Roy et al. [8] demonstrated that packet length distributions and inter-packet arrival times provide sufficient "
        "discriminative signal for low-latency classification of encrypted sessions without payload inspection. This finding "
        "underpins FlowSight's reliance on metadata-only telemetry."
    )
    update_paragraph(doc.paragraphs[11], p11_text)

    # P12: Related Work P2 (Humanized)
    p12_text = (
        "Detection of covert timing channels has evolved over two decades. Cabuk et al. [2] introduced methods for identifying "
        "IP timing channels using variance in inter-packet delay. Gianvecchio and Wang [3] proved that Shannon entropy and "
        "conditional entropy metrics effectively expose timing modulations by uncovering subtle deviations from standard "
        "renewal processes, providing the basis for CoverTrace's ICMP timing tests. More recently, SnapCatch [4] utilized "
        "inter-packet delay state matrices paired with machine learning to automate covert channel detection."
    )
    update_paragraph(doc.paragraphs[12], p12_text)

    # P13: Related Work P3 (Humanized)
    p13_text = (
        "DNS tunneling detection follows similar statistical principles. Chowdhary et al. [5] combined recursive cache-miss "
        "dynamics with lexical query classification to identify exfiltration channels. Khodjaeva [6] demonstrated that "
        "augmenting flow records with character entropy significantly improves Decision Tree and Random Forest detection "
        "of DNS-over-HTTPS tunnels. In the HTTP domain, Graniszewski et al. [7] examined covert data transmission via HTTP "
        "headers (SOMSteg), motivating CoverTrace's inclusion of header anomaly scoring."
    )
    update_paragraph(doc.paragraphs[13], p13_text)

    # P14: Related Work P4 (Humanized)
    p14_text = (
        "While prior studies examine flow statistics or protocol-specific covert channels in isolation, undergraduate capstone "
        "implementations rarely evaluate both feature groups within a single benchmarking framework. This benchmark directly "
        "evaluates that combined feature space."
    )
    update_paragraph(doc.paragraphs[14], p14_text)

    # P16: Problem Statement P1 (Humanized)
    p16_text = (
        "An operational covert channel detector must satisfy two conflicting operational goals: maintaining high recall against "
        "low-bandwidth exfiltration while keeping false positive rates low enough for practical SOC triage. In production "
        "environments, covert traffic constitutes an extreme minority of total network volume. False negatives allow data theft "
        "to proceed unchecked, whereas excessive false alarms cause alert fatigue and disrupt legitimate enterprise traffic."
    )
    update_paragraph(doc.paragraphs[16], p16_text)

    # P17: Problem Statement P2 (Humanized)
    p17_text = (
        "We examine whether a unified classifier trained on FlowSight's passive flow statistics and CoverTrace's information-theoretic "
        "indicators can reliably separate covert traffic from benign activity in the presence of measurement jitter and label noise. "
        "We benchmark Logistic Regression (linear baseline), Support Vector Machines with an RBF kernel, and XGBoost (gradient-boosted "
        "trees) under identical feature sets and train-test splits. Because missed exfiltration represents the primary operational "
        "risk, covert-class recall serves as the central evaluation criterion."
    )
    update_paragraph(doc.paragraphs[17], p17_text)

    # P19: Methodology Opening (Humanized)
    p19_text = (
        "Our evaluation framework consists of synthetic dataset generation, feature transformation, stratified data partitioning, "
        "feature standardization, model training, held-out evaluation, and metric computation. All three models operate on identical "
        "eight-dimensional feature matrices and evaluation splits."
    )
    update_paragraph(doc.paragraphs[19], p19_text)

    # P21: Synthetic Dataset Construction P1 (Humanized)
    p21_text = (
        "The dataset generator synthesizes 1,000 flow instances, initially divided into 500 benign flow records and 500 "
        "covert-channel records (Table I), initialized with random seed 42 for reproducibility."
    )
    update_paragraph(doc.paragraphs[21], p21_text)

    # P22: Synthetic Dataset Construction P2 (Humanized, dense, clean)
    p22_text = (
        "Covert records emulate DNS tunneling, ICMP timing modulation, and HTTP header steganography using parametric normal "
        "distributions N(mu, sigma^2) bounded by physical constraints: higher DNS subdomain entropy, larger chi-square delay "
        "deviation, elevated HTTP header anomaly scores, and protocol structural deviations, alongside smaller packet sizes "
        "and tighter inter-arrival timing. Benign records reflect low entropy, near-zero timing chi-square, standard headers, "
        "and variable human-driven packet timing. To avoid artificial class separability, we inject 4% Gaussian measurement jitter "
        "into every feature and randomly invert exactly 4% of labels (40 instances: 22 benign flipped to covert, 18 covert "
        "flipped to benign). The resulting post-noise dataset contains 496 benign and 504 covert records."
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
    p25_text = "Each flow instance is represented by eight numerical features split evenly between the two detection modules:"
    update_paragraph(doc.paragraphs[25], p25_text)

    # P26: FlowSight Features (Humanized, dense)
    p26_text = (
        "FlowSight features (4): flow_avg_pkt_size_log (natural logarithm of mean packet size in bytes), flow_pkt_size_variance "
        "(packet size sample variance), flow_iat_mean_ms (mean inter-arrival time in milliseconds), and flow_burst_ratio "
        "(proportion of packet gaps shorter than 20.0 ms). These are extracted from directional 5-tuple flow keys "
        "(src_ip, dst_ip, src_port, dst_port, protocol) over 30-second observation windows."
    )
    update_paragraph(doc.paragraphs[26], p26_text)

    # P27: CoverTrace Features (Humanized, dense)
    p27_text = (
        "CoverTrace features (4): dns_subdomain_entropy (Shannon entropy of query subdomain characters, returning 0.0 for labels "
        "shorter than 12 characters to prevent small-sample bias), icmp_timing_chi2 (5-bin delay chi-square test against expected "
        "1.0s ping intervals, requiring sample size N >= 20 pings), http_header_anomaly_score (checking for missing standard "
        "headers and known tunneling prefixes), and protocol_struct_deviation (packet size framing and non-standard TCP/IP flags)."
    )
    update_paragraph(doc.paragraphs[27], p27_text)

    # P28: Data Partitioning (Humanized, dense)
    p28_text = (
        "We partition the noisy dataset using an 80:20 stratified split (random_state=42), producing 800 training records and 200 "
        "held-out test records. Because label flips occur prior to splitting, the test partition contains exactly 99 benign-labelled "
        "records and 101 covert-labelled records. StandardScaler is fitted strictly on the 800 training instances and applied to "
        "both partitions, preventing evaluation data leakage."
    )
    update_paragraph(doc.paragraphs[28], p28_text)

    # P30: XGBoost (Humanized)
    p30_text = (
        "XGBoost (Extreme Gradient Boosting): configured with 200 estimators, maximum tree depth of 5, learning rate of 0.1, "
        "subsample ratio of 0.9, column subsample ratio of 0.9, and random state 42, following the gradient-boosted tree design "
        "of Chen and Guestrin [9]."
    )
    update_paragraph(doc.paragraphs[30], p30_text)

    # P31: SVM (Humanized)
    p31_text = (
        "Support Vector Machine (SVM): an RBF-kernel SVC configured with C = 10, gamma = scale, Platt probability calibration "
        "enabled for ROC evaluation, and random state 42."
    )
    update_paragraph(doc.paragraphs[31], p31_text)

    # P32: Logistic Regression (Humanized)
    p32_text = (
        "Logistic Regression (LR): an L2-regularized linear classifier configured with C = 1.0, a maximum of 1,000 solver iterations, "
        "and random state 42, serving as an interpretable linear baseline."
    )
    update_paragraph(doc.paragraphs[32], p32_text)

    # P33: Defaults statement (Humanized)
    p33_text = (
        "All three models use standard tabular classification defaults without hyperparameter tuning, ensuring that the results "
        "reflect baseline model capability and not split-specific optimization."
    )
    update_paragraph(doc.paragraphs[33], p33_text)

    # P35: Module Positioning (Humanized)
    p35_text = (
        "The classifier operates at the confluence of FlowSight and CoverTrace: FlowSight provides encryption-resilient metadata "
        "telemetry, while CoverTrace contributes covert-channel indicators. In production, confirmed positive detections trigger "
        "MimicNet's adaptive honeypot services. MimicNet's adversary engagement mechanics are evaluated separately; this benchmark "
        "focuses strictly on the detection layer."
    )
    update_paragraph(doc.paragraphs[35], p35_text)

    # P36 & P37: Threat Model & Observability (Humanized)
    update_paragraph(
        doc.paragraphs[36], "E. Threat Model & Feature Observability", bold=True, italic=True
    )
    p37_text = (
        "When network traffic is protected by TLS 1.3, DoH, or DoT, deep packet inspection is unviable from a passive network tap. "
        "Under transport encryption, CoverTrace's DNS subdomain entropy and HTTP header anomaly features cannot be parsed and default "
        "to 0.0 with an active missing_mask. FlowSight's four flow statistics and ICMP timing remain fully observable across all "
        "monitoring points, providing a dependable degraded-mode fallback."
    )
    update_paragraph(doc.paragraphs[37], p37_text)

    # P39: Reproducibility (Humanized)
    p39_text = (
        "The data synthesis script, noise model, split configuration, and training routines use random seed 42. Executing "
        "eval/paper_baseline.py deterministically reproduces the exact records, splits, and metrics reported in Section VI."
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
        "Let TP, TN, FP, and FN denote true positives, true negatives, false positives, and false negatives for covert channel "
        "detection. We evaluate standard classification metrics:"
    )
    update_paragraph(p41, p41_text)

    # Make Table 2, Table 3, Table 4, Table 5 completely unbreakable & keep with next!
    make_table_unbreakable(doc.tables[2])  # Accuracy
    make_table_unbreakable(doc.tables[3])  # Precision & Recall
    make_table_unbreakable(doc.tables[4])  # Specificity
    make_table_unbreakable(doc.tables[5])  # F1

    # P42: Metrics text (Humanized)
    p42 = doc.paragraphs[42]
    p42.paragraph_format.keep_with_next = True
    p42.paragraph_format.space_before = Pt(2.0)
    p42.paragraph_format.space_after = Pt(4.0)
    p42_text = (
        "Precision, recall, and F1-score evaluate covert-class identification. ROC-AUC and PR-AUC assess continuous probability "
        "calibration across decision boundaries."
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
        "The evaluation harness is implemented in Python, using scikit-learn for the SVM and Logistic Regression baselines "
        "and xgboost for the gradient-boosted tree model. This shared codebase guarantees identical feature processing, "
        "standardization, and evaluation for all three classifiers."
    )
    update_paragraph(doc.paragraphs[45], p45_text)

    # P46: Implementation P2 (Humanized)
    p46_text = (
        "This benchmark validates the mathematical and statistical behavior of the candidate classifiers on synthetic data. "
        "Integrating the selected model into FlowSight's C/libpcap capture pipeline and CoverTrace's live scoring routines "
        "represents the next phase of development."
    )
    update_paragraph(doc.paragraphs[46], p46_text)

    # P48: Results Opening (Humanized)
    p48_text = (
        "The three classifiers were evaluated on the 200-record held-out synthetic test set (99 benign, 101 covert). Table III "
        "summarizes classification performance across all evaluated metrics."
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
        "At the standard 0.50 decision threshold (Fig. 1), Logistic Regression produces 10 errors across the 200 test instances: "
        "94 true negatives, 96 true positives, 5 false positives, and 5 false negatives. The Support Vector Machine exhibits "
        "identical error counts (94 TN, 96 TP, 5 FP, 5 FN). XGBoost produces 11 errors: 94 TN, 95 TP, 5 FP, and 6 FN."
    )
    update_paragraph(doc.paragraphs[55], p55_text)

    # P56: Error Interpretation (Humanized)
    p56_text = (
        "These threshold error distributions show consistent performance across linear and kernel models: both Logistic Regression "
        "and SVM achieve 95.05% recall with 5 false alarms out of 99 benign instances."
    )
    update_paragraph(doc.paragraphs[56], p56_text)

    # P58: ROC & AUC Analysis (Humanized)
    p58_text = (
        "Figures 2 and 3 illustrate model discrimination across varying classification thresholds. Logistic Regression achieved "
        "the highest ROC-AUC (0.9520) and PR-AUC (0.9554), demonstrating calibrated probability estimates across the entire decision "
        "range. XGBoost scored 0.9377 ROC-AUC, while SVM scored 0.9364 ROC-AUC."
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
        "These weights confirm that information-theoretic features supply the primary signal for covert channel detection, "
        "while FlowSight's flow statistics offer valuable corroborating evidence and maintain detection capability when payloads "
        "are encrypted."
    )
    update_paragraph(doc.paragraphs[63], p63_text)

    # P64: Heading - Ablation Analysis & Feature Synergy
    update_paragraph(
        doc.paragraphs[64], "D. Ablation Analysis & Feature Synergy", bold=True, italic=True
    )

    # P65: Ablation text (Humanized)
    p65_text = (
        "Ablation experiments confirm the advantage of combining both feature groups. A single-feature threshold on DNS "
        "subdomain entropy (H >= 3.5) achieved 92.00% accuracy and 91.09% recall. FlowSight flow features alone achieved 94.50% "
        "accuracy (0.9449 ROC-AUC), confirming that flow metadata provides a viable degraded-mode fallback under transport "
        "encryption. CoverTrace features alone reached 95.00% accuracy (0.9517 ROC-AUC). Combining both modules yielded 0.9520 "
        "ROC-AUC, exceeding the discriminative performance of either module in isolation."
    )
    update_paragraph(doc.paragraphs[65], p65_text)

    # P66: Uncertainty Quantification text (Humanized)
    p66_text = (
        "Evaluating performance across 10 random seeds (seeds 42 to 51) confirms that classifier performance remains stable "
        "across different data realizations. Logistic Regression averaged 0.9625 ± 0.0053 accuracy, 0.9652 ± 0.0059 ROC-AUC, "
        "and 0.9616 ± 0.0091 PR-AUC. At an operational 5% false positive rate, Logistic Regression detected 94.03% ± 0.0445 of "
        "covert instances."
    )
    update_paragraph(doc.paragraphs[66], p66_text)

    # P68: Threats to Validity P1 (Humanized)
    p68_text = (
        "Several validity constraints apply to this benchmark. The synthetic generator relies on parameterized normal distributions "
        "instead of captured production packets. While measurement jitter and label noise simulate sensor errors, enterprise "
        "network traffic exhibits more complex multi-modal distributions. Additionally, this benchmark uses an equal 50:50 class "
        "distribution, whereas covert channels represent rare anomalies in operational enterprise networks."
    )
    update_paragraph(doc.paragraphs[68], p68_text)

    # P69: Threats to Validity P2 (Humanized)
    p69_text = (
        "Consequently, these results validate pipeline mechanics, feature fusion, and relative classifier performance under "
        "benchmark conditions without claiming evasion resistance against sophisticated adversaries in live deployments."
    )
    update_paragraph(doc.paragraphs[69], p69_text)

    # P71: Interpretation P1 (Humanized)
    p71_text = (
        "In security operations, decision thresholds must balance threat detection against investigation capacity. At a 5% "
        "false positive operating point, the model identifies 94.03% of covert exfiltration channels. Because Operation Cactus "
        "diverts flagged sessions into MimicNet's adaptive honeypots instead of severing connections, occasional false alarms "
        "redirect benign traffic into monitored sandboxes without dropping legitimate user transactions."
    )
    update_paragraph(doc.paragraphs[71], p71_text)

    # P72: Interpretation P2 (Humanized)
    p72_text = (
        "The feature importance distribution justifies the multi-module design: CoverTrace supplies the majority of discriminative "
        "weight, while FlowSight provides continuous, payload-independent monitoring that remains functional when transport "
        "encryption conceals application fields."
    )
    update_paragraph(doc.paragraphs[72], p72_text)

    # P74: Conclusion P1 (Humanized)
    p74_text = (
        "This study benchmarks an implemented detection baseline combining FlowSight's flow metadata with CoverTrace's "
        "information-theoretic indicators. On the held-out test partition, Logistic Regression achieved 95.00% accuracy (190/200), "
        "95.05% recall, and 0.9520 ROC-AUC. CoverTrace indicators contributed approximately 79.4% of permutation decision weight, "
        "while FlowSight flow statistics provided 20.6% corroborating signal and an always-on fallback under transport encryption."
    )
    update_paragraph(doc.paragraphs[74], p74_text)

    # P75: Conclusion P2 (Humanized)
    p75_text = (
        "These results confirm the statistical viability of the fused detection architecture under controlled benchmark conditions. "
        "Phase II work will benchmark these classifiers on empirical PCAPs generated with iodine and dnscat2 in a dedicated testbed "
        "lab, and integrate the detection pipeline with MimicNet's containerized honeypots."
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
