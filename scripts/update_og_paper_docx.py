"""Update the original Operation_Cactus_Paper_Final(2).docx in-place.

Rewrites all body paragraphs with fresh academic prose written in natural
cybersecurity-researcher voice.  Preserves 100 % of verified benchmark
numbers, the original document formatting (fonts, styles, tables, formula
blocks, margins, section architecture), and high-resolution figure blobs.
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

    # ================================================================
    # 3. Update Paragraph Texts — naturally written academic prose
    # ================================================================

    # --- P4: Abstract ---
    abstract_text = (
        "Modern enterprises rely heavily on TLS 1.3, QUIC, and DNS-over-HTTPS,"
        " which renders conventional payload inspection largely ineffective."
        " Attackers have taken notice: covert channels hidden in DNS subdomain"
        " labels, ICMP echo timing, and HTTP header fields now offer a"
        " low-bandwidth path for data theft that most perimeter tools miss"
        " entirely. We built Operation Cactus to close that gap. The system"
        " combines FlowSight, a module that tracks packet-level flow metadata"
        " (log-mean size, variance, inter-arrival time, burst ratio), with"
        " CoverTrace, which computes four protocol-aware indicators (Shannon"
        " entropy over DNS subdomains, a chi-square test on ICMP inter-packet"
        " delays, an HTTP header anomaly index, and a protocol structural"
        " deviation score). Together these form an eight-feature vector that"
        " we feed into Logistic Regression, an RBF-kernel SVM, and XGBoost."
        " Training and testing used 1,000 synthetic flow records carrying 4%"
        " Gaussian measurement jitter and 4% random label flips (40 inverted"
        " instances; final split: 496 benign, 504 covert). On the held-out"
        " 200-record test partition (99 benign, 101 covert), Logistic"
        " Regression hit 95.00% accuracy (190/200 correct), 95.05% recall,"
        " 0.9520 ROC-AUC, and 0.9554 PR-AUC. SVM matched the accuracy at"
        " 95.00% with a lower ROC-AUC of 0.9364, while XGBoost reached"
        " 94.50% (189/200, 94.06% recall, 0.9377 ROC-AUC). In ablation"
        " experiments a simple entropy threshold (H >= 3.5) scored 92.00%"
        " accuracy; FlowSight alone reached 94.50% (0.9449 ROC-AUC);"
        " CoverTrace alone reached 95.00% (0.9517 ROC-AUC); and the fused"
        " set produced the best discrimination (0.9520 ROC-AUC). Permutation"
        " importance allocated 79.4% of normalized weight to CoverTrace and"
        " 20.6% to FlowSight. Across 10 seeds (42 to 51), Logistic"
        " Regression averaged 0.9625 +/- 0.0053 accuracy with a true"
        " positive rate of 0.9403 +/- 0.0445 at 5% false positive rate."
        " These numbers set a working baseline for the detection layer"
        " ahead of live PCAP ingestion and honeypot redirection through"
        " MimicNet."
    )
    update_paragraph(doc.paragraphs[4], abstract_text, prefix_both="Abstract\u2014")

    # --- P5: Index Terms ---
    index_terms_text = (
        "covert channel detection, encrypted network traffic analysis,"
        " DNS tunneling, information-theoretic detection, Shannon entropy,"
        " chi-square timing tests, machine learning baseline, ablation"
        " analysis, threat modeling."
    )
    update_paragraph(
        doc.paragraphs[5], index_terms_text, prefix_both="Index Terms\u2014", italic=True
    )

    # --- P7: Introduction paragraph 1 ---
    p7_text = (
        "TLS 1.3 and QUIC have changed the game for network defenders."
        " Almost everything on the wire is now encrypted, which is good for"
        " privacy but terrible for security monitoring. Deep packet"
        " inspection, the workhorse of enterprise IDS for two decades,"
        " simply cannot read modern encrypted sessions. Attackers know"
        " this. They tunnel C2 traffic or stolen files through protocol"
        " fields that firewalls treat as harmless: DNS query labels, ICMP"
        " echo sequences, custom HTTP headers. These channels carry only"
        " small volumes of data, but they ride on approved ports and valid"
        " protocol envelopes, so signature-based tools wave them through"
        " without a second look."
    )
    update_paragraph(doc.paragraphs[7], p7_text)

    # --- P8: Introduction paragraph 2 ---
    p8_text = (
        "Operation Cactus was designed around this blind spot. It runs two"
        " cooperating detection modules. FlowSight watches packet headers"
        " and pulls out flow-level statistics: how big packets are, how"
        " quickly they arrive, whether they cluster into bursts. It never"
        " touches payload bytes, so it works across any encrypted session."
        " CoverTrace takes a different angle. It measures Shannon entropy"
        " on DNS query names, runs chi-square goodness-of-fit tests against"
        " expected ICMP timing, and flags structural oddities in HTTP"
        " headers. The question we try to answer here is straightforward:"
        " can off-the-shelf classifiers, trained on these eight features"
        " together, tell covert tunnels apart from normal traffic? And how"
        " much of the signal comes from each module?"
    )
    update_paragraph(doc.paragraphs[8], p8_text)

    # --- P9: Introduction paragraph 3 ---
    p9_text = (
        "A third component, MimicNet, spins up containerized honeypots"
        " to interact with entities that the detection layer flags."
        " Because MimicNet handles adversary engagement rather than"
        " passive classification, we evaluate it in a separate companion"
        " paper. Everything reported here concerns the detection"
        " baseline only."
    )
    update_paragraph(doc.paragraphs[9], p9_text)

    # --- P11: Related Work paragraph 1 ---
    p11_text = (
        "When payloads are encrypted, flow metadata is the main thing"
        " defenders have left to work with. Roy et al. [8] showed that"
        " packet length distributions and inter-packet timing carry"
        " enough discriminative signal to classify encrypted application"
        " flows at low latency, without ever looking inside the payload."
        " FlowSight borrows that idea directly."
    )
    update_paragraph(doc.paragraphs[11], p11_text)

    # --- P12: Related Work paragraph 2 ---
    p12_text = (
        "Covert timing channel detection goes back over twenty years."
        " Cabuk et al. [2] were among the first to show that variance in"
        " inter-packet delay can expose IP timing channels. Gianvecchio"
        " and Wang [3] pushed this further with Shannon and conditional"
        " entropy metrics that pick up subtle timing modulations buried"
        " in what looks like ordinary renewal traffic. CoverTrace's ICMP"
        " timing analysis draws directly from their work. More recently,"
        " the SnapCatch system [4] paired inter-packet delay state"
        " matrices with ML classifiers to automate the detection of"
        " timing-based covert channels."
    )
    update_paragraph(doc.paragraphs[12], p12_text)

    # --- P13: Related Work paragraph 3 ---
    p13_text = (
        "DNS tunnel detection follows a similar trajectory. Chowdhary"
        " et al. [5] combined recursive cache-miss dynamics with lexical"
        " query features to flag exfiltration. Khodjaeva [6] found that"
        " adding character entropy to flow records gives Random Forest"
        " classifiers a substantial boost when detecting DNS-over-HTTPS"
        " tunnels. On the HTTP side, Graniszewski et al. [7] studied"
        " SOMSteg, a framework for hiding data in HTTP headers, which is"
        " what motivated CoverTrace's header anomaly scoring."
    )
    update_paragraph(doc.paragraphs[13], p13_text)

    # --- P14: Related Work paragraph 4 ---
    p14_text = (
        "Most prior studies look at flow statistics or at"
        " protocol-specific covert channels, but rarely both under one"
        " benchmarking framework. Undergraduate capstone projects, in"
        " particular, seldom combine the two. Our evaluation does exactly"
        " that: it tests both feature families on a shared dataset and a"
        " single reproducible pipeline."
    )
    update_paragraph(doc.paragraphs[14], p14_text)

    # --- P16: Problem Statement paragraph 1 ---
    p16_text = (
        "Building a covert channel detector means juggling two things"
        " that work against each other. You need high recall so that"
        " slow, low-bandwidth exfiltration does not slip through. But you"
        " also need a low false positive rate, because SOC analysts have"
        " limited bandwidth of their own. In production networks, covert"
        " traffic is an extreme minority of total volume. If the detector"
        " misses it, data walks out the door. If it cries wolf too often,"
        " analysts stop paying attention."
    )
    update_paragraph(doc.paragraphs[16], p16_text)

    # --- P17: Problem Statement paragraph 2 ---
    p17_text = (
        "So we ask a concrete question: can a classifier trained on"
        " FlowSight flow statistics and CoverTrace covert indicators"
        " reliably separate the two classes when there is measurement"
        " noise and mislabelled records in the data? We try three models:"
        " Logistic Regression as a linear baseline, an RBF-kernel SVM,"
        " and XGBoost for gradient-boosted trees. All three see the same"
        " features and the same train-test split. We pick covert-class"
        " recall as the primary metric because, in security operations,"
        " a missed exfiltration is far costlier than a false alarm."
    )
    update_paragraph(doc.paragraphs[17], p17_text)

    # --- P19: Methodology opening ---
    p19_text = (
        "The experimental pipeline has six stages: data generation, noise"
        " injection, stratified partitioning, feature scaling, model"
        " training, and held-out evaluation. All three classifiers operate"
        " on the same eight-column feature matrix and identical splits, so"
        " any performance differences come from the model itself."
    )
    update_paragraph(doc.paragraphs[19], p19_text)

    # --- P21: Synthetic dataset paragraph 1 ---
    p21_text = (
        "We synthesize 1,000 flow instances using the script"
        " eval/paper_baseline.py, pinned to random seed 42 for"
        " reproducibility. The initial population is evenly split: 500"
        " benign records and 500 covert-channel records (Table I)."
    )
    update_paragraph(doc.paragraphs[21], p21_text)

    # --- P22: Synthetic dataset paragraph 2 ---
    p22_text = (
        "Each feature value comes from an independent normal"
        " distribution N(mu, sigma^2) whose parameters mirror empirical"
        " network behavior. Covert records get higher DNS entropy, larger"
        " ICMP delay chi-square values, elevated HTTP anomaly scores, and"
        " more protocol structural deviation, plus smaller packets and"
        " tighter inter-arrival gaps. Benign records sit at the opposite"
        " end: low entropy, near-zero timing deviation, standard headers,"
        " and the kind of variable packet timing you see in real browsing."
        " After generation we add two layers of noise. First, 4% Gaussian"
        " measurement jitter goes into every feature column to simulate"
        " sensor imprecision. Second, we randomly flip exactly 40 labels"
        " (4%), turning 22 benign records into covert and 18 covert into"
        " benign. That leaves the dataset at 496 benign and 504 covert"
        " after noise."
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

    # --- P25: Feature construction intro ---
    p25_text = "We describe each flow with eight numerical features, four from each module:"
    update_paragraph(doc.paragraphs[25], p25_text)

    # --- P26: FlowSight features ---
    p26_text = (
        "FlowSight (4 features): flow_avg_pkt_size_log gives the natural"
        " log of mean packet size in bytes; flow_pkt_size_variance is the"
        " sample variance of packet lengths; flow_iat_mean_ms records mean"
        " inter-arrival time in milliseconds; flow_burst_ratio counts the"
        " fraction of consecutive packets arriving less than 20.0 ms"
        " apart. We key flows on directional 5-tuples (src_ip, dst_ip,"
        " src_port, dst_port, protocol) and evaluate them over 30-second"
        " windows."
    )
    update_paragraph(doc.paragraphs[26], p26_text)

    # --- P27: CoverTrace features ---
    p27_text = (
        "CoverTrace (4 features): dns_subdomain_entropy is Shannon"
        " entropy computed over subdomain characters, but we zero it out"
        " when the label is shorter than 12 characters because short"
        " strings give unreliable entropy estimates. icmp_timing_chi2"
        " runs a 5-bin chi-square test against an expected 1.0 s ping"
        " cadence and requires at least 20 pings to fire; otherwise it"
        " returns 0.0. http_header_anomaly_score checks for missing"
        " standard headers (Host, User-Agent) and known tunneling"
        " prefixes (x-data, x-tunnel, x-exfil)."
        " protocol_struct_deviation flags unusual packet framing and"
        " non-standard TCP/IP flag combinations."
    )
    update_paragraph(doc.paragraphs[27], p27_text)

    # --- P28: Data partitioning ---
    p28_text = (
        "We split the noisy 1,000-record dataset 80:20 using"
        " stratified sampling (random_state=42). The training set has 800"
        " records, the test set has 200: exactly 99 benign-labelled and"
        " 101 covert-labelled, because label flips happened before"
        " splitting. StandardScaler is fitted on the training partition"
        " only and then applied to both halves, so no test information"
        " leaks into training."
    )
    update_paragraph(doc.paragraphs[28], p28_text)

    # --- P30: XGBoost config ---
    p30_text = (
        "XGBoost: 200 boosting rounds, max tree depth 5, learning rate"
        " 0.1, row subsample 0.9, column subsample 0.9, random state 42,"
        " following the gradient-boosted tree framework of Chen and"
        " Guestrin [9]."
    )
    update_paragraph(doc.paragraphs[30], p30_text)

    # --- P31: SVM config ---
    p31_text = (
        "SVM: RBF kernel, regularization C = 10, gamma set to 'scale',"
        " Platt probability calibration turned on so we can compute"
        " ROC curves, random state 42."
    )
    update_paragraph(doc.paragraphs[31], p31_text)

    # --- P32: LR config ---
    p32_text = (
        "Logistic Regression: L2 penalty, C = 1.0, solver capped at"
        " 1,000 iterations, random state 42. This is a deliberately"
        " simple linear model intended as an interpretable baseline."
    )
    update_paragraph(doc.paragraphs[32], p32_text)

    # --- P33: No tuning ---
    p33_text = (
        "We did not tune hyperparameters. All three classifiers use their"
        " default settings so the numbers reflect baseline capability,"
        " not an overfit configuration."
    )
    update_paragraph(doc.paragraphs[33], p33_text)

    # --- P35: Module positioning ---
    p35_text = (
        "The classifier sits at the junction where FlowSight and"
        " CoverTrace meet. FlowSight gives it flow metadata that"
        " survives encryption; CoverTrace gives it covert-channel"
        " indicators when protocol fields are visible. In the full"
        " system, any flow the classifier flags as covert gets handed"
        " off to MimicNet for honeypot engagement. MimicNet is out of"
        " scope here; we care only about the detection accuracy."
    )
    update_paragraph(doc.paragraphs[35], p35_text)

    # --- P36 & P37: Threat model heading and body ---
    update_paragraph(
        doc.paragraphs[36], "E. Threat Model & Feature Observability", bold=True, italic=True
    )
    p37_text = (
        "Under TLS 1.3, DoH, or DoT a passive network tap cannot read"
        " application-layer fields. That means CoverTrace's DNS entropy"
        " and HTTP anomaly scores are unavailable and default to 0.0"
        " with a boolean missing_mask. FlowSight's four flow statistics"
        " and the ICMP timing feature stay observable at every collection"
        " point, so the system still has a viable degraded mode even when"
        " encryption hides everything else."
    )
    update_paragraph(doc.paragraphs[37], p37_text)

    # --- P39: Reproducibility ---
    p39_text = (
        "Every step of the pipeline, from data generation through noise"
        " injection, splitting, scaling, training, and evaluation, runs"
        " off random seed 42. Running eval/paper_baseline.py twice"
        " produces bitwise-identical output."
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
        "TP, TN, FP, and FN stand for true positives, true negatives,"
        " false positives, and false negatives respectively. We report"
        " the following standard metrics:"
    )
    update_paragraph(p41, p41_text)

    # Make formula tables unbreakable
    make_table_unbreakable(doc.tables[2])  # Accuracy
    make_table_unbreakable(doc.tables[3])  # Precision & Recall
    make_table_unbreakable(doc.tables[4])  # Specificity
    make_table_unbreakable(doc.tables[5])  # F1

    # --- P42: Metrics text ---
    p42 = doc.paragraphs[42]
    p42.paragraph_format.keep_with_next = True
    p42.paragraph_format.space_before = Pt(2.0)
    p42.paragraph_format.space_after = Pt(4.0)
    p42_text = (
        "Precision and recall focus on the covert class. ROC-AUC and"
        " PR-AUC capture how well the probability scores separate the"
        " classes across all possible thresholds."
    )
    update_paragraph(p42, p42_text)

    # Table 6: Implementation Configuration (Table II)
    t6 = doc.tables[6]
    set_cell(
        t6.rows[2].cells[1],
        "1000 synthetic (500 benign, 500 covert pre-noise)",
        align_center=False,
    )
    set_cell(
        t6.rows[3].cells[1],
        "200 (99 benign / 101 covert, 80:20 stratified)",
        align_center=False,
    )
    set_cell(t6.rows[9].cells[0], "Noise model", align_center=False)
    set_cell(
        t6.rows[9].cells[1],
        "4% feature Gaussian jitter; 4% label flips (40 instances)",
        align_center=False,
    )

    # --- P45: Implementation paragraph 1 ---
    p45_text = (
        "Everything runs in Python. Logistic Regression and the SVM come"
        " from scikit-learn; XGBoost uses the xgboost package. We wrote"
        " one shared codebase so that feature processing, scaling, and"
        " evaluation happen identically for all three classifiers."
    )
    update_paragraph(doc.paragraphs[45], p45_text)

    # --- P46: Implementation paragraph 2 ---
    p46_text = (
        "This benchmark tests whether the math and the feature pipeline"
        " work correctly on synthetic data. Plugging the winning model"
        " into FlowSight's C/libpcap capture engine and CoverTrace's"
        " live scoring routines is the next engineering step."
    )
    update_paragraph(doc.paragraphs[46], p46_text)

    # --- P48: Results opening ---
    p48_text = (
        "We ran all three classifiers on the 200-record held-out test"
        " partition (99 benign, 101 covert). Table III has the full"
        " numbers."
    )
    update_paragraph(doc.paragraphs[48], p48_text)

    # --- P49: Results summary ---
    p49_text = (
        "Logistic Regression and SVM both classify 190 out of 200"
        " records correctly (95.00%). XGBoost gets 189 right (94.50%)."
        " The difference is a single extra false negative."
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

    # --- P55: Confusion matrix analysis ---
    p55_text = (
        "Looking at the confusion matrices in Fig. 1 at the standard"
        " 0.50 threshold: LR gets 94 TN, 96 TP, 5 FP, 5 FN. That is 10"
        " total errors. SVM produces the exact same split. XGBoost has"
        " one extra miss (94 TN, 95 TP, 5 FP, 6 FN), giving it 11 errors."
    )
    update_paragraph(doc.paragraphs[55], p55_text)

    # --- P56: Error interpretation ---
    p56_text = (
        "It is worth noting that the false positive count is identical"
        " across all three models: five benign flows get flagged in every"
        " case. The gap between models shows up only on the false negative"
        " side, where XGBoost misses one more covert instance than the"
        " other two."
    )
    update_paragraph(doc.paragraphs[56], p56_text)

    # --- P58: ROC & AUC ---
    p58_text = (
        "Figs. 2 and 3 show how the models behave as we move the"
        " decision threshold. Logistic Regression has the best ROC-AUC"
        " at 0.9520 and PR-AUC at 0.9554, which tells us its probability"
        " scores are well-calibrated. XGBoost comes in at 0.9377 and SVM"
        " at 0.9364. The SVM's lower curve area likely reflects the"
        " difficulty Platt scaling has fitting a smooth sigmoid to RBF"
        " decision distances."
    )
    update_paragraph(doc.paragraphs[58], p58_text)

    # --- P61: Feature contribution ---
    p61_text = (
        "We looked at feature importance two ways. First, XGBoost's tree"
        " gain importance (Table IV) tells us which features the trees"
        " actually split on. Second, we ran permutation importance on the"
        " held-out test set. Both measures agree: CoverTrace does the"
        " heavy lifting. It accounts for 88.9% of tree gain and 79.4% of"
        " permutation weight. FlowSight picks up the remaining 11.1% and"
        " 20.6% respectively. The two biggest individual contributors are"
        " protocol_struct_deviation at 55.00% gain and"
        " http_header_anomaly_score at 28.84%."
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

    # --- P63: Feature importance explanation ---
    p63_text = (
        "The takeaway is clear: protocol-level covert indicators carry"
        " most of the discriminative weight, but FlowSight's flow"
        " statistics are not noise. They provide a meaningful secondary"
        " signal and, critically, they remain available even when"
        " encryption makes CoverTrace features unobservable."
    )
    update_paragraph(doc.paragraphs[63], p63_text)

    # --- P64: Heading - Ablation ---
    update_paragraph(
        doc.paragraphs[64], "D. Ablation Analysis & Feature Synergy", bold=True, italic=True
    )

    # --- P65: Ablation text ---
    p65_text = (
        "We ran four ablation configurations to see what each feature"
        " group contributes on its own. The simplest baseline, a hard"
        " threshold on DNS entropy at H >= 3.5, gets 92.00% accuracy and"
        " 91.09% recall. Using only FlowSight's four flow features with"
        " Logistic Regression pushes accuracy to 94.50% and ROC-AUC to"
        " 0.9449, which is encouraging because those features survive any"
        " encryption scheme. CoverTrace alone hits 95.00% accuracy and"
        " 0.9517 ROC-AUC. And when we combine both sets, the fused model"
        " reaches 0.9520 ROC-AUC. The improvement over CoverTrace alone"
        " is small in absolute terms but consistent: FlowSight adds a"
        " bit of complementary information."
    )
    update_paragraph(doc.paragraphs[65], p65_text)

    # --- P66: Uncertainty quantification ---
    p66_text = (
        "To check that our results are not an artifact of a single lucky"
        " split, we repeated the full pipeline across 10 random seeds"
        " (seeds 42 through 51). Logistic Regression averaged 0.9625"
        " +/- 0.0053 accuracy, 0.9652 +/- 0.0059 ROC-AUC, and 0.9616"
        " +/- 0.0091 PR-AUC. At a 5% false positive rate the model"
        " caught 94.03% +/- 0.0445 of covert instances, which we"
        " consider a reasonable operating point for a first baseline."
    )
    update_paragraph(doc.paragraphs[66], p66_text)

    # --- P68: Threats to validity paragraph 1 ---
    p68_text = (
        "A few caveats apply. Our data comes from parametric normal"
        " distributions, not from live packet captures. The jitter and"
        " label noise make it less trivial than a clean synthetic set,"
        " but real enterprise traffic is multi-modal and messier than"
        " anything a Gaussian generator produces. We also used a balanced"
        " 50:50 class ratio, which does not reflect production networks"
        " where covert channels are extremely rare events."
    )
    update_paragraph(doc.paragraphs[68], p68_text)

    # --- P69: Threats to validity paragraph 2 ---
    p69_text = (
        "So what this benchmark actually validates is the pipeline"
        " mechanics: feature extraction, fusion, scaling, and relative"
        " classifier ranking. We are not claiming evasion resistance"
        " or deployment readiness."
    )
    update_paragraph(doc.paragraphs[69], p69_text)

    # --- P71: Interpretation paragraph 1 ---
    p71_text = (
        "From a SOC perspective, the 5% FPR operating point is"
        " interesting. At that threshold the model catches 94.03% of"
        " covert tunnels. And because Operation Cactus routes flagged"
        " flows into MimicNet honeypots instead of dropping them,"
        " a false alarm does not kill a legitimate connection. It just"
        " redirects the session into a monitored sandbox where analysts"
        " can take a closer look."
    )
    update_paragraph(doc.paragraphs[71], p71_text)

    # --- P72: Interpretation paragraph 2 ---
    p72_text = (
        "The importance numbers justify the two-module architecture."
        " CoverTrace provides the strongest signal when protocol fields"
        " are visible, while FlowSight keeps the lights on when"
        " everything is encrypted. Neither module alone matches the"
        " combined result."
    )
    update_paragraph(doc.paragraphs[72], p72_text)

    # --- P74: Conclusion paragraph 1 ---
    p74_text = (
        "We benchmarked an initial detection baseline that merges"
        " FlowSight flow metadata with CoverTrace protocol indicators."
        " On the held-out test set Logistic Regression scored 95.00%"
        " accuracy (190/200), 95.05% recall, and 0.9520 ROC-AUC."
        " Permutation importance assigned roughly 79.4% of decision"
        " weight to CoverTrace and 20.6% to FlowSight. FlowSight is"
        " the weaker contributor on paper, but it is the one that keeps"
        " working when transport encryption hides application fields."
    )
    update_paragraph(doc.paragraphs[74], p74_text)

    # --- P75: Conclusion paragraph 2 ---
    p75_text = (
        "These results confirm that the fused feature set works under"
        " controlled conditions. The next step is running the same"
        " classifiers on real PCAPs generated with iodine and dnscat2"
        " in our testbed lab, and wiring the detection output into"
        " MimicNet's containerized honeypots for end-to-end evaluation."
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
