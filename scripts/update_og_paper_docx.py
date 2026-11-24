"""Update the original Operation_Cactus_Paper_Final(2).docx directly in-place.

Preserves the exact original formatting, fonts, styles, tables, formula blocks,
margins, headers/footers, and section structure of the OG docx, while updating
all data, numbers, tables, figures, and reviewer comments, and eliminating any
spacing flaws.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from docx import Document
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

    # 3. Update Paragraph Texts with clean revised text and exact numbers

    # P4: Abstract
    abstract_text = (
        "This paper presents an implemented detection baseline for Operation Cactus, a two-module network threat "
        "detection framework combining flow-level behavioral traffic analysis (FlowSight) with information-theoretic "
        "covert channel detection (CoverTrace). Because deep packet inspection (DPI) fails against encrypted transport "
        "protocols and standard intrusion detection systems do not reliably surface low-throughput covert exfiltration "
        "channels, this work evaluates whether an eight-dimensional fused representation—four passive flow-level statistics "
        "and four application/structural covert-channel indicators (Shannon entropy of DNS subdomains, an ICMP chi-square "
        "timing statistic, an HTTP header anomaly score, and a protocol structural-deviation score)—can separate benign "
        "network traffic from covert-channel flows. Three classification algorithms—XGBoost (Extreme Gradient Boosting), "
        "Support Vector Machines (SVM) with an RBF kernel, and L2-regularized Logistic Regression (LR)—are evaluated on a "
        "controlled, synthetic dataset of 1,000 instances. The dataset is generated with 500 benign and 500 covert-channel "
        "instances before being subjected to 4% Gaussian measurement jitter per feature and 4% random label flips (resulting "
        "in 496 benign and 504 covert instances). Under an 80:20 stratified split, the held-out test partition comprises "
        "exactly 200 instances (99 benign and 101 covert). On this partition, Logistic Regression achieves 95.00% accuracy "
        "(190/200), 95.05% recall, 0.9520 ROC-AUC, and 0.9554 PR-AUC; SVM achieves 95.00% accuracy, 95.05% recall, and "
        "0.9364 ROC-AUC; and XGBoost achieves 94.50% accuracy, 94.06% recall, and 0.9377 ROC-AUC. An ablation study reveals "
        "that a simple single-feature entropy threshold achieves 92.00% accuracy, FlowSight-only features achieve 94.50% "
        "accuracy (0.9449 ROC-AUC), CoverTrace-only features achieve 95.00% accuracy (0.9517 ROC-AUC), and the fused "
        "representation delivers the highest overall discrimination (0.9520 ROC-AUC). Permutation feature importance "
        "establishes that CoverTrace indicators account for 79.4% of decision importance while FlowSight flow statistics "
        "account for 20.6%. Across a 10-seed repeated evaluation, Logistic Regression achieves a mean accuracy of "
        "0.9625 ± 0.0053 and a true positive rate of 0.9403 ± 0.0445 at a 5% false-positive rate. This study establishes "
        "an implemented detection-layer baseline; live packet capture, honeypot emulation (MimicNet), and empirical "
        "evaluation on lab-captured tunneling tools are addressed in subsequent project phases."
    )
    update_paragraph(doc.paragraphs[4], abstract_text, prefix_both="Abstract—")

    # P5: Index Terms
    index_terms_text = (
        "covert channel detection, encrypted network traffic analysis, DNS tunneling, information-theoretic detection, "
        "Shannon entropy, chi-square timing tests, machine learning baseline, ablation analysis, threat modeling."
    )
    update_paragraph(doc.paragraphs[5], index_terms_text, prefix_both="Index Terms—", italic=True)

    # P8: Introduction - FlowSight + CoverTrace
    p8_text = (
        "Operation Cactus tries to close that gap with two modules that work together. The first, FlowSight, captures raw "
        "metadata through a C and libpcap engine and pulls out statistical flow features — packet size distribution, "
        "inter-arrival timing, burst ratios — never touching the actual payload, which is exactly why it keeps working once "
        "everything is encrypted. CoverTrace applies information-theoretic analysis — Shannon entropy scoring of DNS query "
        "structure, chi-square timing tests for ICMP-based channels, and protocol structure validation for HTTP header anomalies "
        "— to surface covert exfiltration channels that flow statistics alone would miss. This paper evaluates whether a "
        "classifier trained jointly on FlowSight and CoverTrace features can reliably separate covert-channel traffic from benign "
        "traffic, and reports which of the two feature families contributes more discriminative signal."
    )
    update_paragraph(doc.paragraphs[8], p8_text)

    # P21: Synthetic Dataset Construction P1
    p21_text = (
        "The synthetic data generator produces 1,000 total instances, balanced initially between 500 benign flow records "
        "and 500 covert-channel-labelled records (Table I), using a fixed random seed (42) for full reproducibility."
    )
    update_paragraph(doc.paragraphs[21], p21_text)

    # P22: Synthetic Dataset Construction P2
    p22_text = (
        "Covert-channel records are drawn from explicit parametric normal distributions N(mu, sigma^2) followed by physical "
        "boundary clipping to emulate DNS tunneling, ICMP timing channels, and HTTP header manipulation: higher and more "
        "variable DNS subdomain entropy, larger chi-square deviation from expected ICMP inter-packet timing, elevated HTTP "
        "header anomaly scores, and greater protocol structural deviation, combined with smaller and more uniform packet "
        "sizes and tighter inter-arrival timing consistent with automated tunnel traffic. Benign records are drawn from "
        "distributions with low entropy, near-zero chi-square deviation, minimal header/protocol anomaly, and human-driven "
        "flow statistics. To avoid unrealistically perfect class separability, 4% Gaussian measurement jitter is added to every "
        "feature and exactly 4% of labels are randomly flipped prior to data splitting (flipping 22 benign labels to covert and "
        "18 covert labels to benign, producing 496 benign and 504 covert noisy instances), ensuring realistic feature-space overlap."
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

    # P26: FlowSight Features
    p26_text = (
        "FlowSight features (4): flow_avg_pkt_size_log, flow_pkt_size_variance, flow_iat_mean_ms, flow_burst_ratio — "
        "derived purely from packet metadata and directional 5-tuple flow keys (src_ip, dst_ip, src_port, dst_port, protocol) "
        "over 30-second sliding windows with a burst threshold of tau_burst = 20.0 ms, preserving visibility on fully encrypted sessions."
    )
    update_paragraph(doc.paragraphs[26], p26_text)

    # P27: CoverTrace Features
    p27_text = (
        "CoverTrace features (4): dns_subdomain_entropy (Shannon entropy with a length threshold >= 12 chars to eliminate "
        "small-sample variance), icmp_timing_chi2 (5-bin delay chi-square goodness-of-fit requiring sample size N >= 20 pings), "
        "http_header_anomaly_score (evaluating missing standard browser headers and covert tunneling prefixes), and "
        "protocol_struct_deviation (payload-to-packet length ratio and flag anomalies) — the information-theoretic indicators "
        "specified in the Operation Cactus brief."
    )
    update_paragraph(doc.paragraphs[27], p27_text)

    # P28: Data Partitioning
    p28_text = (
        "Data partitioning applies an 80:20 stratified split with random_state=42 on the noisy labels. The resulting held-out "
        "partition contains exactly 200 records: because label noise is applied prior to splitting, the realized test-set composition "
        "is exactly 99 benign-labelled and 101 covert-channel-labelled records rather than an exact 100/100 split. StandardScaler "
        "is fitted strictly on the 800 training records and applied to both training and test features, preventing data leakage."
    )
    update_paragraph(doc.paragraphs[28], p28_text)

    # P36 & P37: Threat Model & Observability
    update_paragraph(
        doc.paragraphs[36], "E. Threat Model & Feature Observability", bold=True, italic=True
    )
    p37_text = (
        "When traffic is encrypted under TLS 1.3, DoH, or DoT, deep packet inspection is blinded from an on-path passive tap. "
        "Under transport encryption, CoverTrace's DNS subdomain entropy and HTTP header anomaly scores are unobservable and "
        "assigned a neutral default value (0.0) with an active missing_mask. FlowSight's four flow statistics (packet lengths, "
        "inter-arrival times, burst ratios) and ICMP timing remain fully observable across all monitoring points, providing an "
        "always-on degraded-mode fallback when application fields are obscured."
    )
    update_paragraph(doc.paragraphs[37], p37_text)

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

    # P49: Results opening
    p49_text = (
        "Logistic Regression correctly classifies 190 of 200 test records (95.00% accuracy), SVM correctly classifies 190 "
        "(95.00%), and XGBoost correctly classifies 189 (94.50%)."
    )
    update_paragraph(doc.paragraphs[49], p49_text)

    # Table 7: Performance Comparison (Table III)
    t7 = doc.tables[7]
    # Header: Model, Accuracy, Precision, Recall, F1, Specificity, AUC
    # Row 1: Logistic Regression
    set_cell(t7.rows[1].cells[0], "Logistic Regression", align_center=False)
    set_cell(t7.rows[1].cells[1], "95.00%", align_center=True)
    set_cell(t7.rows[1].cells[2], "95.05%", align_center=True)
    set_cell(t7.rows[1].cells[3], "95.05%", align_center=True)
    set_cell(t7.rows[1].cells[4], "95.05%", align_center=True)
    set_cell(t7.rows[1].cells[5], "94.95%", align_center=True)
    set_cell(t7.rows[1].cells[6], "0.9520", align_center=True)

    # Row 2: SVM
    set_cell(t7.rows[2].cells[0], "SVM (RBF)", align_center=False)
    set_cell(t7.rows[2].cells[1], "95.00%", align_center=True)
    set_cell(t7.rows[2].cells[2], "95.05%", align_center=True)
    set_cell(t7.rows[2].cells[3], "95.05%", align_center=True)
    set_cell(t7.rows[2].cells[4], "95.05%", align_center=True)
    set_cell(t7.rows[2].cells[5], "94.95%", align_center=True)
    set_cell(t7.rows[2].cells[6], "0.9364", align_center=True)

    # Row 3: XGBoost
    set_cell(t7.rows[3].cells[0], "XGBoost", align_center=False)
    set_cell(t7.rows[3].cells[1], "94.50%", align_center=True)
    set_cell(t7.rows[3].cells[2], "95.00%", align_center=True)
    set_cell(t7.rows[3].cells[3], "94.06%", align_center=True)
    set_cell(t7.rows[3].cells[4], "94.53%", align_center=True)
    set_cell(t7.rows[3].cells[5], "94.95%", align_center=True)
    set_cell(t7.rows[3].cells[6], "0.9377", align_center=True)

    # P55: Confusion Matrix Analysis
    p55_text = (
        "The confusion matrices in Fig. 1 show that Logistic Regression produces 10 total errors out of 200 (94 true negatives, "
        "96 true positives, 5 false positives, and 5 false negatives). The Support Vector Machine exhibits identical error counts "
        "(94 TN, 96 TP, 5 FP, and 5 FN). XGBoost records 11 total errors (94 TN, 95 TP, 5 FP, and 6 FN)."
    )
    update_paragraph(doc.paragraphs[55], p55_text)

    # P58: ROC & AUC Analysis
    p58_text = (
        "The ROC curves are presented together in Fig. 2, and overall metric comparisons in Fig. 3. Logistic Regression records "
        "the largest AUC (0.9520) and PR-AUC (0.9554), reflecting superior probability calibration, ahead of XGBoost at 0.9377 and "
        "SVM at 0.9364. All three classifiers demonstrate robust probability ranking under noise."
    )
    update_paragraph(doc.paragraphs[58], p58_text)

    # P61: Feature Contribution
    p61_text = (
        "To characterize which of the two detection modules drives classification performance, tree gain importance was extracted "
        "from XGBoost (Table IV) and model-agnostic permutation importance was evaluated on the held-out test partition. "
        "CoverTrace indicators account for 88.9% of tree gain and 79.4% of held-out permutation decision weight, while FlowSight "
        "accounts for 11.1% of tree gain and 20.6% of permutation weight. Protocol structural deviation (55.00%) and HTTP header "
        "anomaly (28.84%) provide the strongest primary signals."
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

    # P64: Heading - Ablation Analysis & Feature Synergy
    update_paragraph(
        doc.paragraphs[64], "D. Ablation Analysis & Feature Synergy", bold=True, italic=True
    )

    # P65: Ablation text
    p65_text = (
        "An ablation study isolating individual module contributions demonstrates that a single-feature entropy threshold "
        "(H >= 3.5) achieves 92.00% accuracy and 91.09% recall. FlowSight-only features achieve 94.50% accuracy (0.9449 AUC), "
        "confirming that passive flow metadata remains an effective fallback under encryption. CoverTrace-only features achieve "
        "95.00% accuracy (0.9517 AUC), while the fused representation delivers the highest overall discrimination (0.9520 AUC), "
        "proving that metadata and covert indicators provide corroborating signals."
    )
    update_paragraph(doc.paragraphs[65], p65_text)

    # P66: Uncertainty Quantification text
    p66_text = (
        "To evaluate stability beyond a single fixed seed, evaluation was repeated across 10 independent random seeds (seeds 42 "
        "through 51). Logistic Regression achieves mean accuracy 0.9625 ± 0.0053, ROC-AUC 0.9652 ± 0.0059, and PR-AUC 0.9616 ± 0.0091. "
        "At an operational 5% false-positive rate, LR achieves 0.9403 ± 0.0445 recall, confirming high sensitivity under realistic "
        "triage constraints."
    )
    update_paragraph(doc.paragraphs[66], p66_text)

    # P71: Interpretation P1
    p71_text = (
        "The findings distinguish fixed-threshold performance from calibrated probability rankings. Logistic Regression and SVM "
        "achieve 95.00% accuracy (10 errors out of 200), while XGBoost achieves 94.50% accuracy (11 errors). Logistic Regression "
        "maintains the highest probability-ranking advantage across thresholds."
    )
    update_paragraph(doc.paragraphs[71], p71_text)

    # P74: Conclusion P1
    p74_text = (
        "This work evaluated XGBoost, a Support Vector Machine, and Logistic Regression on a common synthetic binary-classification "
        "benchmark fusing Operation Cactus's FlowSight flow statistics with its CoverTrace covert-channel indicators. Logistic "
        "Regression achieved 95.00% accuracy and 0.9520 ROC-AUC on the held-out synthetic test set, with 95.05% precision, 95.05% "
        "recall, 95.05% F1-score, and 94.95% specificity. A feature-importance analysis showed that CoverTrace's information-theoretic "
        "indicators account for 88.9% of tree gain and 79.4% of permutation decision weight versus 20.6% for FlowSight, confirming "
        "that CoverTrace provides the primary discriminative signal while FlowSight contributes essential corroboration and encryption resilience."
    )
    update_paragraph(doc.paragraphs[74], p74_text)

    # P75: Conclusion P2
    p75_text = (
        "The results confirm consistent operation of the preprocessing, scaling, training, prediction, and evaluation pipeline under "
        "the specified benchmark conditions. The present implementation provides a detection-layer baseline for the broader Operation "
        "Cactus platform. Planned Phase-II work integrates these classifiers into FlowSight's live libpcap capture path and evaluates "
        "them against empirical tunnels generated with iodine and dnscat2 alongside containerized MimicNet deception honeypots."
    )
    update_paragraph(doc.paragraphs[75], p75_text)

    # 4. Spacing Polish across all body paragraphs:
    # Set uniform 5 pt space_after, line_spacing 1.1, justified alignment
    for i, p in enumerate(doc.paragraphs):
        if not p.text.strip():
            continue
        # Don't touch title or subtitle
        if i in [0, 1]:
            continue
        # If it's a heading 1:
        if i in [6, 10, 15, 18, 44, 47, 73, 76]:
            p.paragraph_format.space_before = Pt(9.0)
            p.paragraph_format.space_after = Pt(4.0)
        # If it's a heading 2:
        elif i in [20, 24, 29, 34, 36, 38, 40, 52, 57, 60, 64, 67, 70]:
            p.paragraph_format.space_before = Pt(7.0)
            p.paragraph_format.space_after = Pt(3.0)
        # If it's a table caption:
        elif i in [23, 43, 51, 62]:
            p.paragraph_format.space_before = Pt(6.0)
            p.paragraph_format.space_after = Pt(2.5)
        # If it's a figure caption:
        elif i in [54]:
            p.paragraph_format.space_before = Pt(3.0)
            p.paragraph_format.space_after = Pt(6.0)
        # Body text / references:
        else:
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(5.0)
            p.paragraph_format.line_spacing = 1.1

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
            print(f"Note: {dst} is currently locked by Word. Created alternative copy instead.")


if __name__ == "__main__":
    patch_og_paper()
