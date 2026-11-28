"""Build the definitive, publication-grade IEEE two-column Paper 1 document and Response Table.

Preserves the exact IEEE 4-section layout:
- Section 0: Title, Subtitle, Author Block (1-column full page width)
- Section 1: Abstract, Index Terms, Sections I-V, Section VI Opening (2-column IEEE format)
- Section 2: Table IV, Subsection A, Fig 1, Subsection B, Table with Figs 2 & 3 (1-column full page width)
- Section 3: Subsections C-G, Section VII Conclusion, References (2-column IEEE format)

Ensures flawless typography, professional table borders, clean cell padding, exact spacing,
and completely eliminates duplicated paragraphs.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
DOCS_PAPER = ROOT / "docs" / "paper"
DESKTOP = Path(os.environ.get("USERPROFILE", "C:/Users/Admin")) / "Desktop"
RESULTS_DIR = ROOT / "eval" / "results"

FIG1_PATH = RESULTS_DIR / "fig1_confusion_matrices.png"
FIG2_PATH = RESULTS_DIR / "fig2_roc_curves.png"
FIG3_PATH = RESULTS_DIR / "fig3_metrics_comparison.png"


def set_cell_margins(cell, top=50, bottom=50, left=70, right=70):
    """Set explicit padding inside a table cell (in dxa: 20 dxa = 1 pt)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_shading(cell, color_hex: str):
    """Set background color for a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    tcPr.append(shd)


def set_table_ieee_borders(table):
    """Apply IEEE standard table borders: solid top & bottom rules, light horizontal, no vertical lines."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f"<w:tblBorders {nsdecls('w')}>"
        '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
        '<w:insideV w:val="none"/>'
        '<w:left w:val="none"/>'
        '<w:right w:val="none"/>'
        "</w:tblBorders>"
    )
    tblPr.append(borders)


def set_cols(section, num_cols: int, space_dxa: int = 432):
    """Configure column count on a section cleanly without duplicate w:cols tags."""
    sectPr = section._sectPr
    cols = sectPr.xpath("./w:cols")
    if cols:
        for c in cols[1:]:
            sectPr.remove(c)
        cols[0].set(qn("w:num"), str(num_cols))
        if num_cols == 2:
            cols[0].set(qn("w:space"), str(space_dxa))
        elif qn("w:space") in cols[0].attrib:
            del cols[0].attrib[qn("w:space")]
    else:
        if num_cols == 2:
            sectPr.append(parse_xml(f'<w:cols {nsdecls("w")} w:num="2" w:space="{space_dxa}"/>'))
        else:
            sectPr.append(parse_xml(f'<w:cols {nsdecls("w")} w:num="1"/>'))


def apply_section_page_setup(section, is_continuous: bool = False):
    """Set uniform page geometry across sections."""
    if is_continuous:
        section.start_type = WD_SECTION_START.CONTINUOUS
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)


def add_p(
    doc,
    text: str = "",
    font_size: float = 9.5,
    bold: bool = False,
    italic: bool = False,
    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    space_before: float = 0.0,
    space_after: float = 3.5,
    line_spacing: float = 1.05,
    prefix_bold: str | None = None,
    prefix_italic: str | None = None,
):
    """Add a beautifully styled paragraph with explicit Times New Roman typography."""
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing

    if prefix_bold:
        r_pre = p.add_run(prefix_bold)
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(font_size)
        r_pre.font.bold = True
    if prefix_italic:
        r_pre = p.add_run(prefix_italic)
        r_pre.font.name = "Times New Roman"
        r_pre.font.size = Pt(font_size)
        r_pre.font.italic = True

    if text:
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(font_size)
        r.font.bold = bold
        r.font.italic = italic
    return p


def add_heading_1(doc, text: str):
    """Add Level-1 IEEE heading (e.g., I. INTRODUCTION)."""
    return add_p(
        doc,
        text=text,
        font_size=10.0,
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_before=9.0,
        space_after=3.0,
    )


def add_heading_2(doc, text: str):
    """Add Level-2 IEEE heading (e.g., A. Synthetic Dataset Construction)."""
    return add_p(
        doc,
        text=text,
        font_size=9.5,
        bold=True,
        italic=True,
        align=WD_ALIGN_PARAGRAPH.LEFT,
        space_before=6.0,
        space_after=2.0,
    )


def add_table_caption(doc, text: str):
    """Add standard IEEE table caption."""
    return add_p(
        doc,
        text=text,
        font_size=8.5,
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_before=6.0,
        space_after=2.5,
    )


def format_table_header(row, titles, widths=None, bg="F4F6F8"):
    """Format table header row with bold font, centered alignment, and padding."""
    for idx, cell in enumerate(row.cells):
        if widths and idx < len(widths):
            cell.width = widths[idx]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2.0)
        p.paragraph_format.space_after = Pt(2.0)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(titles[idx])
        r.font.name = "Times New Roman"
        r.font.size = Pt(8.5)
        r.font.bold = True
        set_cell_margins(cell, top=55, bottom=55, left=65, right=65)
        if bg:
            set_cell_shading(cell, bg)


def format_table_row(row, values, widths=None, align_center=True, font_size=8.0, bold_col0=False):
    """Format table data row with consistent spacing and typography."""
    for idx, cell in enumerate(row.cells):
        if widths and idx < len(widths):
            cell.width = widths[idx]
        p = cell.paragraphs[0]
        p.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER if (align_center or idx > 0) else WD_ALIGN_PARAGRAPH.LEFT
        )
        p.paragraph_format.space_before = Pt(1.5)
        p.paragraph_format.space_after = Pt(1.5)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(values[idx])
        r.font.name = "Times New Roman"
        r.font.size = Pt(font_size)
        if bold_col0 and idx == 0:
            r.font.bold = True
        set_cell_margins(cell, top=40, bottom=40, left=65, right=65)


def build_paper_document(out_path: Path):
    doc = Document()

    # ========================================================
    # SECTION 0: Title, Subtitle, Author Block (1-column full page width)
    # ========================================================
    s0 = doc.sections[0]
    apply_section_page_setup(s0, is_continuous=False)
    set_cols(s0, num_cols=1)

    # Title
    add_p(
        doc,
        "Operation Cactus: Behavioral Traffic Analysis and Covert Channel Detection for Encrypted Network Threats",
        font_size=16.0,
        bold=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_before=0,
        space_after=3.0,
    )

    # Subtitle
    add_p(
        doc,
        "A Synthetic Baseline Benchmark of Gradient-Boosted, Kernel, and Linear Classifiers for the FlowSight and CoverTrace Detection Modules",
        font_size=10.5,
        italic=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_before=0,
        space_after=10.0,
    )

    # Author Table (2 rows x 3 cols, borderless)
    tbl_auth = doc.add_table(rows=2, cols=3)
    tbl_auth.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_auth.autofit = False

    authors = [
        (
            "Ayush Rathod",
            "Dept. of Computer Science & Engineering\n(Cyber Security)\nDSATM, Bengaluru, India",
        ),
        (
            "Sharukh Khan",
            "Dept. of Computer Science & Engineering\n(Cyber Security)\nDSATM, Bengaluru, India",
        ),
        (
            "Shivansh Tripathi",
            "Dept. of Computer Science & Engineering\n(Cyber Security)\nDSATM, Bengaluru, India",
        ),
        (
            "Bhargav Moray",
            "Dept. of Computer Science & Engineering\n(Cyber Security)\nDSATM, Bengaluru, India",
        ),
        (
            "Gerard Deepak",
            "Dept. of Computer Science & Engineering\n(Cyber Security)\nDSATM, Bengaluru, India",
        ),
        (
            "Shalini Ranjan",
            "Dept. of Computer Science & Engineering\n(Cyber Security)\nDSATM, Bengaluru, India",
        ),
    ]

    col_w_auth = Inches(2.25)
    for idx, (name, affil) in enumerate(authors):
        r_idx = idx // 3
        c_idx = idx % 3
        cell = tbl_auth.rows[r_idx].cells[c_idx]
        cell.width = col_w_auth
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(1.0)
        p.paragraph_format.space_after = Pt(4.0)
        p.paragraph_format.line_spacing = 1.05

        rn = p.add_run(name + "\n")
        rn.font.name = "Times New Roman"
        rn.font.size = Pt(9.5)
        rn.font.bold = True

        ra = p.add_run(affil)
        ra.font.name = "Times New Roman"
        ra.font.size = Pt(8.0)
        set_cell_margins(cell, 15, 15, 30, 30)

    # ========================================================
    # SECTION 1: Body (2-column IEEE format)
    # ========================================================
    s1 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    apply_section_page_setup(s1, is_continuous=True)
    set_cols(s1, num_cols=2, space_dxa=432)

    # Abstract
    add_p(
        doc,
        "This paper presents an implemented detection baseline for Operation Cactus, a network threat detection "
        "middleware combining flow-level behavioral traffic analysis (FlowSight) with information-theoretic covert channel "
        "detection (CoverTrace). Because deep packet inspection (DPI) fails against encrypted transport protocols and standard "
        "intrusion detection systems do not reliably surface low-throughput covert exfiltration channels, this work evaluates "
        "whether an eight-dimensional fused representation—four passive flow-level statistics and four application/structural "
        "covert-channel indicators—can separate benign network traffic from covert-channel flows. Three classification "
        "algorithms—XGBoost (Extreme Gradient Boosting), Support Vector Machines (SVM) with an RBF kernel, and L2-regularized "
        "Logistic Regression (LR)—are evaluated on a controlled, synthetic dataset of 1,000 instances. The dataset is generated "
        "with 500 benign and 500 covert-channel instances before being subjected to 4% Gaussian measurement jitter per feature "
        "and 4% random label flips (resulting in 496 benign and 504 covert instances). Under an 80:20 stratified split, the "
        "held-out test partition comprises exactly 200 instances (99 benign and 101 covert). On this partition, Logistic Regression "
        "achieves 95.00% accuracy (190/200), 95.05% recall, 0.9520 ROC-AUC, and 0.9554 PR-AUC; SVM achieves 95.00% accuracy, "
        "95.05% recall, and 0.9364 ROC-AUC; and XGBoost achieves 94.50% accuracy, 94.06% recall, and 0.9377 ROC-AUC. An ablation "
        "study reveals that a simple single-feature entropy threshold achieves 92.00% accuracy, FlowSight-only features achieve "
        "94.50% accuracy (0.9449 ROC-AUC), CoverTrace-only features achieve 95.00% accuracy (0.9517 ROC-AUC), and the fused "
        "representation delivers the highest overall discrimination (0.9520 ROC-AUC). Permutation feature importance establishes "
        "that CoverTrace indicators account for 79.4% of decision importance while FlowSight flow statistics account for 20.6%. "
        "Across a 10-seed repeated evaluation, Logistic Regression achieves a mean accuracy of 0.9625 ± 0.0053 and a true positive "
        "rate of 0.9403 ± 0.0445 at a 5% false-positive rate. This study establishes an implemented detection-layer baseline; live "
        "packet capture, honeypot emulation (MimicNet), and empirical evaluation on lab-captured tunneling tools are addressed "
        "in subsequent project phases.",
        font_size=9.0,
        prefix_bold="Abstract—",
        prefix_italic="",
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=4.0,
        space_after=4.0,
    )

    # Index Terms
    add_p(
        doc,
        "covert channel detection, encrypted network traffic analysis, DNS tunneling, information-theoretic detection, "
        "Shannon entropy, chi-square timing tests, machine learning baseline, ablation analysis, threat modeling.",
        font_size=9.0,
        prefix_bold="Index Terms—",
        prefix_italic="",
        italic=True,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        space_before=0.0,
        space_after=8.0,
    )

    # I. Introduction
    add_heading_1(doc, "I. INTRODUCTION")
    add_p(
        doc,
        "Security operations teams face diminishing visibility into enterprise network perimeters as transport-layer "
        "encryption (TLS 1.3, QUIC, DoH, DoT) becomes pervasive. Traditional perimeter defenses relying on payload inspection "
        "cannot examine encrypted packet contents. Attackers exploit this blind spot by establishing low-throughput covert timing "
        "and storage channels—such as DNS subdomain encapsulation, ICMP echo timing modulation, and HTTP header steganography—to "
        "exfiltrate intellectual property or conduct command-and-control (C2) communication without tripping signature-based "
        "intrusion detection systems.",
    )
    add_p(
        doc,
        "Operation Cactus addresses this visibility gap through two complementary detection modules:\n"
        "1) FlowSight: A metadata-only module that observes packet sizes, inter-arrival times, and burst cadences without "
        "decrypting payloads, preserving visibility across encrypted sessions.\n"
        "2) CoverTrace: An information-theoretic and structural analysis module that quantifies character entropy in DNS queries, "
        "evaluates goodness-of-fit deviations in ICMP inter-ping timings, and identifies non-standard HTTP headers and protocol format anomalies.",
    )
    add_p(
        doc,
        "The objective of this paper is to benchmark an implemented baseline classifier combining FlowSight's flow-level telemetry "
        "with CoverTrace's covert-channel indicators on a controlled synthetic dataset. We investigate two core research questions:\n"
        "• RQ1: Can a unified linear or non-linear classifier trained on a fused eight-dimensional feature representation reliably "
        "discriminate covert-channel flows from benign traffic under controlled measurement and label noise?\n"
        "• RQ2: How much discriminative weight is contributed by passive flow statistics versus application-level covert-channel indicators, "
        "and what performance trade-off emerges when individual modules are ablated?",
    )
    add_p(
        doc,
        "A companion deception module, MimicNet, dynamically redirects confirmed malicious entities into containerized honeypots. "
        "MimicNet is scoped separately from this passive detection study.",
    )

    # II. Related Work
    add_heading_1(doc, "II. RELATED WORK")
    add_p(
        doc,
        "Encrypted traffic classification primarily relies on flow statistical attributes. Roy et al. [8] demonstrated that packet "
        "length distributions and inter-arrival timing provide sufficient signal for low-latency classification of encrypted flows "
        "without payload inspection, providing theoretical justification for FlowSight's metadata-driven architecture.",
    )
    add_p(
        doc,
        "Covert channel detection has progressed from ad-hoc thresholding to statistical and information-theoretic tests. Cabuk et al. [2] "
        "introduced IP covert timing channel detection using inter-packet delay variance. Gianvecchio and Wang [3] proved that Shannon "
        "entropy and conditional entropy measures generalize across varied timing modulation schemes by detecting subtle deviations "
        "from natural renewal processes. SnapCatch [4] demonstrated machine-learning-based classification of covert channels by "
        "transforming inter-packet delays into visual state matrices.",
    )
    add_p(
        doc,
        "For DNS tunneling, Chowdhary et al. [5] combined recursive cache-miss dynamics with lexical query classification to detect "
        "exfiltration channels. Khodjaeva [6] established that augmenting NetFlow records with flow-level character entropy significantly "
        "improves Decision Tree and Random Forest detection of DNS-over-HTTPS (DoH) tunnels. Graniszewski et al. [7] evaluated covert "
        "communication via HTTP headers (SOMSteg), motivating CoverTrace's inclusion of header anomaly scoring.",
    )
    add_p(
        doc,
        "Existing literature either benchmarks flow metadata on general encrypted traffic or analyzes single covert protocols in isolation. "
        "This study provides an integrated baseline evaluating both feature families within a unified, reproducible benchmarking protocol.",
    )

    # III. Problem Statement
    add_heading_1(doc, "III. PROBLEM STATEMENT")
    add_p(
        doc,
        "In covert channel detection, false negatives allow unmonitored data exfiltration, while false alarms impose operational triage "
        "overhead on security analysts. In real-world enterprise networks, covert traffic represents an extreme minority class relative "
        "to benign volume. A practical detector must maintain high covert recall while minimizing false alarms at low false-positive "
        "operating points.",
    )
    add_p(
        doc,
        "This work benchmarks three candidate classifiers—Logistic Regression (linear baseline), Support Vector Machines (kernel method), "
        "and XGBoost (gradient-boosted tree ensemble)—under identical preprocessing, scaling, and feature subsets to measure baseline "
        "separability, module importance, and error trade-offs before deployment on live network telemetry.",
    )

    # IV. Methodology
    add_heading_1(doc, "IV. METHODOLOGY")
    add_p(
        doc,
        "The experimental framework encompasses synthetic dataset generation, feature transformation, stratified data partitioning, "
        "feature scaling, model training, held-out inference, and metric computation. All three classifiers operate on the identical "
        "eight-dimensional feature matrix and evaluation split.",
    )

    add_heading_2(doc, "A. Synthetic Dataset Construction & Noise Model")
    add_p(
        doc,
        "The synthetic data generator produces 1,000 total instances, balanced initially between 500 benign flow records and 500 "
        "covert-channel-labelled records (Table I), using a fixed random seed (42) for full reproducibility.",
    )
    add_p(
        doc,
        "Each feature is drawn from independent normal distributions N(mu, sigma^2) parameterized to reflect empirical network behavior, "
        "followed by physical boundary clipping: flow_avg_pkt_size_log (benign mu=6.20, covert mu=4.80, clipped to [2.0, 9.0]); "
        "flow_pkt_size_variance (benign mu=65000, covert mu=15000); flow_iat_mean_ms (benign mu=320.0, covert mu=100.0); "
        "flow_burst_ratio (benign mu=0.25, covert mu=0.62, clipped to [0.0, 1.0]); dns_subdomain_entropy (benign mu=2.15, covert mu=4.20, "
        "clipped to [0.0, 5.0]); icmp_timing_chi2 (benign mu=3.2, covert mu=16.5); http_header_anomaly_score (benign mu=0.08, covert mu=0.78, "
        "clipped to [0.0, 1.0]); and protocol_struct_deviation (benign mu=0.06, covert mu=0.70, clipped to [0.0, 1.0]).",
    )
    add_p(
        doc,
        "To avoid unrealistically perfect class separability, 4% Gaussian measurement jitter is injected into every feature, followed "
        "by physical boundary re-clipping. Furthermore, exactly 4% of labels (40 of 1,000) are randomly inverted prior to data splitting "
        "(flipping 22 benign labels to covert and 18 covert labels to benign), yielding a post-noise distribution of 496 benign and 504 covert instances.",
    )

    # Table I: Dataset Distribution (in 2-col section, width ~3.25")
    add_table_caption(doc, "TABLE I: SYNTHETIC DATASET DISTRIBUTION")
    t1 = doc.add_table(rows=4, cols=4)
    t1.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_ieee_borders(t1)
    format_table_header(
        t1.rows[0],
        ["Class", "Pre-Noise", "Post-Noise", "Percentage"],
        [Inches(1.2), Inches(0.65), Inches(0.65), Inches(0.75)],
    )
    format_table_row(t1.rows[1], ["Benign", "500", "496", "49.6%"], align_center=False)
    format_table_row(t1.rows[2], ["Covert-channel", "500", "504", "50.4%"], align_center=False)
    format_table_row(
        t1.rows[3], ["Total", "1000", "1000", "100.0%"], align_center=False, bold_col0=True
    )

    add_heading_2(doc, "B. Data Partitioning and Preprocessing")
    add_p(
        doc,
        "Data partitioning applies an 80:20 stratified split with random_state=42 on the noisy labels. The resulting held-out partition "
        "contains exactly 200 records: because label noise is applied prior to splitting, the realized test-set composition is exactly "
        "99 benign-labelled and 101 covert-labelled records rather than an exact 100/100 split. StandardScaler is fitted strictly on the "
        "training partition and then applied to both training and test features, preventing data leakage.",
    )

    add_heading_2(doc, "C. Feature Extraction Specification")
    add_p(
        doc,
        "The feature extraction pipeline operates over directional 5-tuple flow keys (src_ip, dst_ip, src_port, dst_port, protocol) "
        "within 30-second windows. The burst threshold is defined at tau_burst = 20.0 ms. Subdomain entropy computes Shannon entropy "
        "with a length cutoff condition: subdomains shorter than 12 characters return 0.0 bits to avoid small-sample bias. ICMP timing chi2 "
        "tests delay distribution across 5 bins and enforces a sample size threshold of N >= 20 pings. HTTP header anomaly score evaluates "
        "missing standard headers (+0.30) and covert tunneling prefixes (+0.60).",
    )

    add_heading_2(doc, "D. Threat Model & Feature Observability")
    add_p(
        doc,
        "When traffic is encrypted under TLS 1.3, DoH, or DoT, deep application fields are unobservable to an on-path passive tap. "
        "Table II defines visibility across operational observation points. Under encryption, unobservable CoverTrace features default to 0.0 "
        "with a missing_mask, allowing degraded-mode operation with FlowSight flow statistics.",
    )

    # Table II: Feature Observability
    add_table_caption(doc, "TABLE II: COVERTRACE FEATURE OBSERVABILITY")
    t_obs = doc.add_table(rows=5, cols=4)
    t_obs.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_ieee_borders(t_obs)
    format_table_header(
        t_obs.rows[0],
        ["Feature Category", "Passive Tap (Clear)", "Passive Tap (TLS/DoH)", "Resolver / Proxy"],
        [Inches(1.15), Inches(0.7), Inches(0.7), Inches(0.7)],
    )
    format_table_row(
        t_obs.rows[1],
        ["FlowSight (4 feats)", "Observable", "Observable", "Observable"],
        align_center=False,
    )
    format_table_row(
        t_obs.rows[2],
        ["DNS Entropy", "Observable", "Unobservable", "Observable"],
        align_center=False,
    )
    format_table_row(
        t_obs.rows[3],
        ["ICMP Chi2 Timing", "Observable", "Observable", "Observable"],
        align_center=False,
    )
    format_table_row(
        t_obs.rows[4],
        ["HTTP Header Anomaly", "Observable", "Unobservable", "Observable"],
        align_center=False,
    )

    add_heading_2(doc, "E. Evaluation Metrics")
    add_p(
        doc,
        "Let TP, TN, FP, and FN denote true positives, true negatives, false positives, and false negatives for covert channel detection. "
        "Evaluation relies on standard mathematical formulations:",
    )
    # Centered equations
    add_p(
        doc,
        "Accuracy = (TP + TN) / (TP + TN + FP + FN)\n"
        "Precision = TP / (TP + FP),    Recall = TP / (TP + FN)\n"
        "Specificity = TN / (TN + FP)\n"
        "F1 = 2 × (Precision × Recall) / (Precision + Recall)",
        font_size=8.5,
        italic=True,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_before=2.0,
        space_after=4.0,
    )
    add_p(
        doc,
        "In addition, Receiver Operating Characteristic (ROC-AUC) and Precision-Recall (PR-AUC) areas are calculated from continuous "
        "calibrated class probability estimates.",
    )

    # V. Implementation Config
    add_heading_1(doc, "V. EXPERIMENTAL CONFIGURATION")
    add_p(
        doc,
        "All candidate models are evaluated using identical scikit-learn and XGBoost pipelines under fixed seed controls. "
        "Table III specifies experimental hyperparameters.",
    )

    # Table III: Implementation Config
    add_table_caption(doc, "TABLE III: IMPLEMENTATION CONFIGURATION")
    t_cfg = doc.add_table(rows=6, cols=2)
    t_cfg.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_ieee_borders(t_cfg)
    format_table_header(
        t_cfg.rows[0],
        ["Component", "Specification"],
        [Inches(1.1), Inches(2.15)],
    )
    format_table_row(
        t_cfg.rows[1],
        ["Total records", "1,000 synthetic (500 benign, 500 covert pre-noise)"],
        align_center=False,
    )
    format_table_row(
        t_cfg.rows[2],
        ["Held-out test", "200 records (99 benign / 101 covert, 80:20 stratified)"],
        align_center=False,
    )
    format_table_row(
        t_cfg.rows[3],
        ["Noise model", "4% feature Gaussian jitter; 4% label flips (40 instances)"],
        align_center=False,
    )
    format_table_row(
        t_cfg.rows[4],
        ["Scaling", "StandardScaler fitted strictly on training partition"],
        align_center=False,
    )
    format_table_row(
        t_cfg.rows[5],
        ["Models", "XGBoost (depth 5, lr 0.1), SVM (RBF, C=10), Logistic Regression"],
        align_center=False,
    )

    # VI. Results opening
    add_heading_1(doc, "VI. RESULTS AND PERFORMANCE EVALUATION")
    add_p(
        doc,
        "The three classifiers were evaluated on the 200-record held-out synthetic test set (99 benign, 101 covert). "
        "The full comparative results, confusion matrices, and ROC curves are detailed across the following sections.",
    )

    # ========================================================
    # SECTION 2: Wide Figures & Performance Table (1-column full page width)
    # ========================================================
    s2 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    apply_section_page_setup(s2, is_continuous=True)
    set_cols(s2, num_cols=1)

    # Table IV: Performance Comparison (Full Width 6.77")
    add_table_caption(doc, "TABLE IV: PERFORMANCE COMPARISON ON HELD-OUT SYNTHETIC TEST SET")
    t_perf = doc.add_table(rows=4, cols=8)
    t_perf.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_ieee_borders(t_perf)
    format_table_header(
        t_perf.rows[0],
        [
            "Model",
            "Accuracy",
            "Precision",
            "Recall",
            "F1-Score",
            "Specificity",
            "ROC-AUC",
            "PR-AUC",
        ],
        [
            Inches(1.5),
            Inches(0.75),
            Inches(0.75),
            Inches(0.75),
            Inches(0.75),
            Inches(0.75),
            Inches(0.75),
            Inches(0.75),
        ],
    )
    format_table_row(
        t_perf.rows[1],
        [
            "Logistic Regression",
            "95.00% (190/200)",
            "95.05%",
            "95.05%",
            "95.05%",
            "94.95%",
            "0.9520",
            "0.9554",
        ],
        align_center=False,
        bold_col0=True,
    )
    format_table_row(
        t_perf.rows[2],
        [
            "SVM (RBF)",
            "95.00% (190/200)",
            "95.05%",
            "95.05%",
            "95.05%",
            "94.95%",
            "0.9364",
            "0.9318",
        ],
        align_center=False,
        bold_col0=True,
    )
    format_table_row(
        t_perf.rows[3],
        ["XGBoost", "94.50% (189/200)", "95.00%", "94.06%", "94.53%", "94.95%", "0.9377", "0.9004"],
        align_center=False,
        bold_col0=True,
    )

    # Subsection A: Confusion Matrix Analysis
    add_heading_2(doc, "A. Confusion Matrix Analysis")
    add_p(
        doc,
        "The confusion matrices in Fig. 1 illustrate threshold-level classification errors at the default decision boundary (threshold = 0.50). "
        "Logistic Regression correctly classifies 190 of 200 test records, producing exactly 10 errors (94 true negatives, 96 true positives, "
        "5 false positives, and 5 false negatives). The Support Vector Machine exhibits identical threshold error counts (94 TN, 96 TP, 5 FP, 5 FN). "
        "XGBoost correctly classifies 189 of 200 records, producing 11 errors (94 TN, 95 TP, 5 FP, and 6 FN).",
        space_after=4.0,
    )

    # Fig 1 (Full width confusion matrix image)
    if FIG1_PATH.exists():
        p_f1 = doc.add_paragraph()
        p_f1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_f1.paragraph_format.space_before = Pt(4.0)
        p_f1.paragraph_format.space_after = Pt(2.0)
        p_f1.add_run().add_picture(str(FIG1_PATH), width=Inches(6.3))

        add_p(
            doc,
            "Fig. 1. Confusion matrices for XGBoost, Support Vector Machine (SVM), and Logistic Regression on the 200-instance held-out synthetic test set.",
            font_size=8.5,
            italic=True,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            space_before=1.0,
            space_after=6.0,
        )

    # Subsection B: ROC and AUC Analysis
    add_heading_2(doc, "B. ROC and AUC Analysis")
    add_p(
        doc,
        "The continuous discrimination performance across varying decision thresholds is illustrated in Fig. 2 (ROC curves) and Fig. 3 "
        "(overall performance metrics). Logistic Regression achieves the highest ROC-AUC of 0.9520 and PR-AUC of 0.9554, reflecting superior "
        "probability calibration across the full threshold spectrum. SVM achieves 0.9364 ROC-AUC, while XGBoost achieves 0.9377 ROC-AUC.",
        space_after=4.0,
    )

    # Fig 2 & Fig 3 Side by Side Table
    if FIG2_PATH.exists() and FIG3_PATH.exists():
        t_figs = doc.add_table(rows=1, cols=2)
        t_figs.alignment = WD_TABLE_ALIGNMENT.CENTER
        t_figs.autofit = False

        c0 = t_figs.rows[0].cells[0]
        c1 = t_figs.rows[0].cells[1]
        c0.width = Inches(3.35)
        c1.width = Inches(3.35)

        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.space_before = Pt(2.0)
        p0.paragraph_format.space_after = Pt(2.0)
        p0.add_run().add_picture(str(FIG2_PATH), width=Inches(3.2))
        p0_cap = c0.add_paragraph()
        p0_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0_cap.paragraph_format.space_before = Pt(1.0)
        p0_cap.paragraph_format.space_after = Pt(4.0)
        r0 = p0_cap.add_run("Fig. 2. ROC curve comparison on held-out synthetic test set.")
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(8.0)
        r0.font.italic = True

        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(2.0)
        p1.paragraph_format.space_after = Pt(2.0)
        p1.add_run().add_picture(str(FIG3_PATH), width=Inches(3.2))
        p1_cap = c1.add_paragraph()
        p1_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1_cap.paragraph_format.space_before = Pt(1.0)
        p1_cap.paragraph_format.space_after = Pt(4.0)
        r1 = p1_cap.add_run("Fig. 3. Performance metric comparison across evaluated classifiers.")
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(8.0)
        r1.font.italic = True

        set_cell_margins(c0, 20, 20, 20, 20)
        set_cell_margins(c1, 20, 20, 20, 20)

    # ========================================================
    # SECTION 3: Deep Dives, Conclusion & References (2-column IEEE format)
    # ========================================================
    s3 = doc.add_section(WD_SECTION_START.CONTINUOUS)
    apply_section_page_setup(s3, is_continuous=True)
    set_cols(s3, num_cols=2, space_dxa=432)

    # Subsection C: Feature Contribution & Importance
    add_heading_2(doc, "C. Feature Contribution: FlowSight vs. CoverTrace")
    add_p(
        doc,
        "To characterize which of the two detection modules drives classification performance, we extracted tree gain importance from "
        "XGBoost and computed model-agnostic permutation importance on the held-out test partition over 10 random shuffles (Table V).",
    )

    # Table V: Feature Importance
    add_table_caption(doc, "TABLE V: FEATURE IMPORTANCE ANALYSIS (XGBOOST)")
    t_imp = doc.add_table(rows=10, cols=4)
    t_imp.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_ieee_borders(t_imp)
    format_table_header(
        t_imp.rows[0],
        ["Feature", "Module", "Tree Gain", "Permutation Mean"],
        [Inches(1.3), Inches(0.65), Inches(0.6), Inches(0.7)],
    )
    rows_imp = [
        ("protocol_struct_deviation", "CoverTrace", "55.00%", "1.25% ± 0.46%"),
        ("http_header_anomaly_score", "CoverTrace", "28.84%", "1.05% ± 0.57%"),
        ("flow_pkt_size_variance", "FlowSight", "3.47%", "0.55% ± 0.72%"),
        ("icmp_timing_chi2", "CoverTrace", "2.53%", "0.35% ± 0.23%"),
        ("flow_avg_pkt_size_log", "FlowSight", "2.48%", "0.20% ± 0.46%"),
        ("flow_iat_mean_ms", "FlowSight", "2.53%", "0.10% ± 0.44%"),
        ("dns_subdomain_entropy", "CoverTrace", "2.55%", "0.05% ± 0.15%"),
        ("flow_burst_ratio", "FlowSight", "2.60%", "-0.15% ± 0.32%"),
        ("CoverTrace Subtotal", "Grouped", "88.9%", "79.4% (norm)"),
    ]
    for r_i, r_data in enumerate(rows_imp):
        is_bold = r_data[0].startswith("CoverTrace Subtotal")
        format_table_row(t_imp.rows[r_i + 1], r_data, align_center=False, bold_col0=is_bold)

    add_p(
        doc,
        "CoverTrace features account for 88.9% of tree gain importance and 79.4% of held-out permutation decision weight. "
        "Protocol structural deviation and HTTP header anomaly scoring are the primary discriminators, while FlowSight features "
        "provide 20.6% corroborating weight and establish an essential fallback during encryption blind spots.",
    )

    # Subsection D: Ablation Analysis
    add_heading_2(doc, "D. Ablation Study & Feature Subset Analysis")
    add_p(
        doc,
        "Table VI isolates individual module contributions across identical splits. A single-feature entropy threshold (H >= 3.5) "
        "achieves 92.00% accuracy. FlowSight-only achieves 94.50% accuracy (0.9449 AUC). CoverTrace-only achieves 95.00% accuracy (0.9517 AUC). "
        "The fused model achieves the highest overall discrimination (0.9520 AUC), proving that metadata and covert indicators corroborate.",
    )

    # Table VI: Ablations
    add_table_caption(doc, "TABLE VI: ABLATION STUDY & MODEL COMPARISON")
    t_abl = doc.add_table(rows=5, cols=5)
    t_abl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_ieee_borders(t_abl)
    format_table_header(
        t_abl.rows[0],
        ["Configuration", "Accuracy", "Recall", "ROC-AUC", "PR-AUC"],
        [Inches(1.25), Inches(0.5), Inches(0.5), Inches(0.5), Inches(0.5)],
    )
    format_table_row(
        t_abl.rows[1],
        ["FlowSight-only (LR)", "94.50%", "95.05%", "0.9449", "0.9363"],
        align_center=False,
    )
    format_table_row(
        t_abl.rows[2],
        ["CoverTrace-only (LR)", "95.00%", "95.05%", "0.9517", "0.9572"],
        align_center=False,
    )
    format_table_row(
        t_abl.rows[3],
        ["Fused Model (LR)", "95.00%", "95.05%", "0.9520", "0.9554"],
        align_center=False,
        bold_col0=True,
    )
    format_table_row(
        t_abl.rows[4],
        ["Entropy Threshold", "92.00%", "91.09%", "0.9336", "0.9332"],
        align_center=False,
    )

    # Subsection E: Uncertainty Quantification
    add_heading_2(doc, "E. Uncertainty Quantification & Repeated Seeds")
    add_p(
        doc,
        "To evaluate stability beyond a single fixed split, data generation, label flipping, and model training were repeated across "
        "10 independent random seeds (seeds 42 through 51). Table VII reports mean performance and 95% confidence intervals.",
    )

    # Table VII: Uncertainty Quantification
    add_table_caption(doc, "TABLE VII: 10-SEED UNCERTAINTY QUANTIFICATION")
    t_unc = doc.add_table(rows=6, cols=4)
    t_unc.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_ieee_borders(t_unc)
    format_table_header(
        t_unc.rows[0],
        ["Model & Metric", "Mean Value", "Std Dev", "95% Conf. Interval"],
        [Inches(1.2), Inches(0.65), Inches(0.6), Inches(0.8)],
    )
    format_table_row(
        t_unc.rows[1], ["LR Accuracy", "0.9625", "0.0086", "± 0.0053"], align_center=False
    )
    format_table_row(
        t_unc.rows[2], ["LR ROC-AUC", "0.9652", "0.0095", "± 0.0059"], align_center=False
    )
    format_table_row(
        t_unc.rows[3], ["LR PR-AUC", "0.9616", "0.0147", "± 0.0091"], align_center=False
    )
    format_table_row(
        t_unc.rows[4], ["LR TPR @ 1% FPR", "0.4620", "0.1752", "± 0.1086"], align_center=False
    )
    format_table_row(
        t_unc.rows[5], ["LR TPR @ 5% FPR", "0.9403", "0.0717", "± 0.0445"], align_center=False
    )

    # Subsection F: Operational Threshold Selection
    add_heading_2(doc, "F. Operational Threshold Selection & Error Trade-offs")
    add_p(
        doc,
        "In enterprise threat monitoring, decision thresholds must balance false-alarm suppression with detection sensitivity. "
        "At a strict operating point of 1% False Positive Rate (FPR), Logistic Regression detects 46.2% of covert tunnels. "
        "Relaxing the threshold to a 5% False Positive Rate raises recall to 94.03%, capturing the vast majority of exfiltration attempts. "
        "Because Operation Cactus incorporates an adaptive honeypot (MimicNet) downstream of detection, a modest false-alarm rate is "
        "operationally acceptable: suspect entities are diverted into isolated honeypots rather than outright blocked, allowing interactive "
        "confirmation without disrupting benign user sessions.",
    )

    # Subsection G: Scope and Threats to Validity
    add_heading_2(doc, "G. Threats to Validity and Scope Boundaries")
    add_p(
        doc,
        "These results reflect controlled synthetic benchmark conditions designed to validate pipeline architecture and feature representations. "
        "Construct validity is bounded by the parametric assumptions of the synthetic generator. While measurement jitter and label noise "
        "emulate real-world sensor imperfection, empirical enterprise traffic exhibits more complex multi-modal distributions. "
        "These findings establish an implemented detection-layer baseline; empirical validation against lab-captured tunneling tools is addressed in Phase II.",
    )

    # VII. Conclusion
    add_heading_1(doc, "VII. CONCLUSION AND FUTURE WORK")
    add_p(
        doc,
        "This paper established an implemented baseline benchmark for the detection layer of Operation Cactus. By evaluating Logistic "
        "Regression, Support Vector Machines, and XGBoost on an eight-dimensional fused representation combining FlowSight's flow statistics "
        "with CoverTrace's information-theoretic indicators, we demonstrated:\n"
        "1) Logistic Regression provides the most reliable linear baseline, achieving 0.9625 ± 0.0053 mean accuracy and 0.9652 ± 0.0059 ROC-AUC "
        "over 10 repeated seeds.\n"
        "2) CoverTrace features supply approximately 79.4% of permutation decision weight, while FlowSight features provide 20.6% corroborating "
        "signal and offer a 94.50% accurate fallback when encryption blinds application-layer inspection.\n"
        "3) Feature extraction rules, sample-size thresholds (N >= 20 for ICMP chi2, length >= 12 for DNS entropy), and observability limitations "
        "under DoH/TLS were formally defined and tested on controlled traffic.\n"
        "Ongoing Phase-II work integrates these classifiers into FlowSight's live libpcap capture engine and evaluates them against empirical "
        "tunnels generated with iodine and dnscat2 alongside containerized MimicNet deception honeypots.",
    )

    # References
    add_heading_1(doc, "REFERENCES")
    refs = [
        '[1] S. Zander, G. Armitage, and P. Branch, "A survey of covert channels and countermeasures in computer network protocols," IEEE Communications Surveys & Tutorials, vol. 9, no. 3, pp. 44–57, 2007.',
        '[2] S. Cabuk, C. E. Brodley, and C. Shields, "IP covert timing channels: design and detection," in Proc. 11th ACM Conf. on Computer and Communications Security (CCS), 2004, pp. 178–187.',
        '[3] S. Gianvecchio and H. Wang, "Detecting covert timing channels: an entropy-based approach," in Proc. 14th ACM Conf. on Computer and Communications Security (CCS), 2007, pp. 307–316.',
        '[4] S. Al-Eidi, O. Darwish, Y. Chen, and G. Husari, "SnapCatch: Automatic detection of covert timing channels using image processing and machine learning," IEEE Access, vol. 9, 2021.',
        '[5] A. Chowdhary, M. Bhowmik, and B. Rudra, "DNS tunneling detection using machine learning and cache miss properties," in Proc. 5th Int. Conf. on Intelligent Computing and Control Systems (ICICCS), 2021, pp. 1225–1229.',
        '[6] Y. Khodjaeva, "Detecting malicious DNS tunnels via network flow entropy," M.S. thesis, Faculty of Computer Science, Dalhousie University, 2021.',
        '[7] W. Graniszewski, J. Krupski, and K. Szczypiorski, "SOMSteg — Framework for covert channel, and its detection, within HTTP," Journal of Universal Computer Science, vol. 24, no. 7, pp. 864–891, 2018.',
        '[8] S. Roy, T. Shapira, and Y. Shavitt, "Fast and lean encrypted Internet traffic classification," Computer Communications, vol. 186, pp. 166–173, 2022.',
        '[9] T. Chen and C. Guestrin, "XGBoost: A scalable tree boosting system," in Proc. 22nd ACM SIGKDD Int. Conf. on Knowledge Discovery and Data Mining (KDD), 2016, pp. 785–794.',
    ]
    for r in refs:
        p_ref = add_p(
            doc,
            r,
            font_size=8.0,
            space_before=1.0,
            space_after=2.0,
            align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        )
        p_ref.paragraph_format.left_indent = Inches(0.2)
        p_ref.paragraph_format.first_line_indent = Inches(-0.2)

    doc.save(str(out_path))
    print(f"Successfully generated clean paper docx: {out_path}")


def build_reviewer_response_docx(out_path: Path):
    doc = Document()

    for sec in doc.sections:
        apply_section_page_setup(sec, is_continuous=False)

    # Title
    p_title = doc.add_paragraph()
    r_title = p_title.add_run("Reviewer Response Table — Paper 1 Revision")
    r_title.font.name = "Arial"
    r_title.font.size = Pt(15)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0, 51, 102)
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(2)

    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run(
        "Operation Cactus: Behavioral Traffic Analysis and Covert Channel Detection for Encrypted Network Threats\n"
        "Date: November 24, 2026 | Capstone Phase-II Revision | DSATM Bengaluru"
    )
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(9.5)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(90, 90, 90)
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(12)

    # Read markdown reply table rows
    reply_md_path = DOCS_PAPER / "REPLY_TABLE.md"
    reply_lines = reply_md_path.read_text(encoding="utf-8").splitlines()

    table_data = []
    in_table = False
    for line in reply_lines:
        line = line.strip()
        if line.startswith("| # | Reviewer Comment"):
            in_table = True
            continue
        if in_table and line.startswith("|---|"):
            continue
        if in_table and line.startswith("| **"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4:
                num = parts[0].replace("**", "")
                comment = parts[1].replace("**", "")
                action = parts[2].replace("<br>", "\n").replace("`", "")
                loc = (
                    parts[3]
                    .replace("<br>", "\n")
                    .replace("[", "")
                    .replace("]", "")
                    .replace("`", "")
                )
                import re

                loc = re.sub(r"\(file:[^\)]+\)", "", loc)
                table_data.append((num, comment, action, loc))

    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    hdr_cells = table.rows[0].cells
    hdr_titles = [
        "#",
        "Reviewer Comment",
        "Action Taken & Changes Made",
        "Section & Artifact Location",
    ]
    col_widths = [Inches(0.35), Inches(1.9), Inches(3.3), Inches(1.2)]

    for i, title in enumerate(hdr_titles):
        cell = hdr_cells[i]
        cell.width = col_widths[i]
        p = cell.paragraphs[0]
        r = p.add_run(title)
        r.font.name = "Arial"
        r.font.size = Pt(9.0)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_shading(cell, "003366")
        set_cell_margins(cell, 80, 80, 90, 90)

    for row_idx, (num, comment, action, loc) in enumerate(table_data):
        row = table.add_row()
        cells = row.cells
        bg_color = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"

        for i, text in enumerate([num, comment, action, loc]):
            cell = cells[i]
            cell.width = col_widths[i]
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(1.5)
            p.paragraph_format.space_after = Pt(1.5)
            p.paragraph_format.line_spacing = 1.05
            r = p.add_run(text)
            r.font.name = "Arial"
            r.font.size = Pt(8.0)
            if i == 0 or i == 1:
                r.font.bold = True
            set_cell_shading(cell, bg_color)
            set_cell_margins(cell, 60, 60, 80, 80)

    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f"<w:tblBorders {nsdecls('w')}>"
        '<w:top w:val="single" w:sz="6" w:space="0" w:color="003366"/>'
        '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="003366"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
        '<w:insideV w:val="none"/>'
        '<w:left w:val="none"/>'
        '<w:right w:val="none"/>'
        "</w:tblBorders>"
    )
    tblPr.append(borders)

    doc.save(str(out_path))
    print(f"Successfully generated clean response docx: {out_path}")


if __name__ == "__main__":
    revised_paper = DOCS_PAPER / "Operation_Cactus_Paper_Revised.docx"
    response_table = DOCS_PAPER / "Reviewer_Response_Table.docx"

    build_paper_document(revised_paper)
    build_reviewer_response_docx(response_table)

    shutil.copyfile(str(revised_paper), str(DESKTOP / revised_paper.name))
    shutil.copyfile(str(response_table), str(DESKTOP / response_table.name))
    print(f"Copied both documents to Desktop: {DESKTOP}")
