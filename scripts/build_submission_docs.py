"""Build the final revised Paper 1 Word document (.docx) and Reviewer Response Table (.docx).

Saves to both docs/paper/ and C:\\Users\\Admin\\Desktop\\.
"""

from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
DOCS_PAPER = ROOT / "docs" / "paper"
DESKTOP = Path(os.environ.get("USERPROFILE", "C:/Users/Admin")) / "Desktop"
RESULTS_DIR = ROOT / "eval" / "results"

ORIGINAL_DOCX = DOCS_PAPER / "Operation_Cactus_Paper_Final(2).docx"
REVISED_DOCX_NAME = "Operation_Cactus_Paper_Revised.docx"
RESPONSE_DOCX_NAME = "Reviewer_Response_Table.docx"


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for m, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{m}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_background(cell, fill_hex: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def build_reviewer_response_docx(out_path: Path):
    doc = Document()

    # 0.75 in margins
    for sec in doc.sections:
        sec.top_margin = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin = Inches(0.75)
        sec.right_margin = Inches(0.75)
        sec.page_width = Inches(8.27)
        sec.page_height = Inches(11.69)

    # Title
    p_title = doc.add_paragraph()
    r_title = p_title.add_run("Reviewer Response Table — Paper 1 Revision")
    r_title.font.name = "Arial"
    r_title.font.size = Pt(16)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0, 51, 102)
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run(
        "Operation Cactus: Behavioral Traffic Analysis and Covert Channel Detection for Encrypted Network Threats\nDate: November 24, 2026 | Capstone Phase-II"
    )
    r_sub.font.name = "Arial"
    r_sub.font.size = Pt(10)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(100, 100, 100)
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()

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
                # clean bold and html
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
                # remove markdown links format
                import re

                loc = re.sub(r"\(file:[^\)]+\)", "", loc)
                table_data.append((num, comment, action, loc))

    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Header
    hdr_cells = table.rows[0].cells
    hdr_titles = [
        "#",
        "Reviewer Comment",
        "Action Taken & Changes Made",
        "Section & Artifact Location",
    ]
    col_widths = [Inches(0.4), Inches(2.0), Inches(3.2), Inches(1.4)]

    for i, title in enumerate(hdr_titles):
        cell = hdr_cells[i]
        cell.width = col_widths[i]
        p = cell.paragraphs[0]
        r = p.add_run(title)
        r.font.name = "Arial"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)
        set_cell_background(cell, "003366")
        set_cell_margins(cell, 120, 120, 140, 140)

    for num, comment, action, loc in table_data:
        row = table.add_row()
        cells = row.cells
        cells[0].width = col_widths[0]
        cells[1].width = col_widths[1]
        cells[2].width = col_widths[2]
        cells[3].width = col_widths[3]

        for i, text in enumerate([num, comment, action, loc]):
            cell = cells[i]
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.name = "Arial"
            r.font.size = Pt(8.5)
            if i == 0 or i == 1:
                r.font.bold = True
            set_cell_margins(cell, 100, 100, 120, 120)

    # Style borders
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f"<w:tblBorders {nsdecls('w')}>"
        '<w:top w:val="single" w:sz="6" w:space="0" w:color="003366"/>'
        '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="003366"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:insideV w:val="none"/>'
        '<w:left w:val="none"/>'
        '<w:right w:val="none"/>'
        "</w:tblBorders>"
    )
    tblPr.append(borders)

    doc.save(str(out_path))
    print(f"Saved response document to: {out_path}")


def update_paper_docx(out_path: Path):
    doc = Document(str(ORIGINAL_DOCX))

    # 1. Update Abstract (Paragraph 4)
    revised_abstract = (
        "Abstract—This paper presents an implemented detection baseline for Operation Cactus, a network threat detection "
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
        "in subsequent project phases."
    )
    doc.paragraphs[4].text = revised_abstract

    # 2. Update Section IV-A text (Paragraph 21)
    p21_text = (
        "The synthetic data generator produces 1,000 total instances, balanced initially between 500 benign flow records and "
        "500 covert-channel-labelled records (Table I), using a fixed random seed (42) for full reproducibility. "
        "Covert-channel records are drawn from distributions that emulate DNS tunneling, ICMP timing channels, and HTTP header "
        "manipulation: higher and more variable DNS subdomain entropy, larger chi-square deviation from expected ICMP inter-packet "
        "timing, elevated HTTP header anomaly scores, and greater protocol structural deviation, combined with smaller and more "
        "uniform packet sizes and more regular inter-arrival timing consistent with automated tunnel traffic. Benign records are "
        "drawn from distributions with low entropy, near-zero chi-square deviation, minimal header/protocol anomaly, and more variable, "
        "human-driven flow statistics. To avoid unrealistically perfect class separability, 4% Gaussian measurement jitter is added "
        "to every feature and exactly 4% of labels are randomly flipped after generation (flipping 40 instances to yield 496 benign and "
        "504 covert noisy instances), so that the two classes overlap in feature space the way real covert and benign traffic would."
    )
    doc.paragraphs[21].text = p21_text

    # Update Table I (Table 1 in docx)
    t1 = doc.tables[1]
    # Header: Class, Samples, Percentage
    t1.rows[1].cells[0].text = "Covert-channel-labelled"
    t1.rows[1].cells[1].text = "504 (500 pre-noise)"
    t1.rows[1].cells[2].text = "50.4%"
    t1.rows[2].cells[0].text = "Benign"
    t1.rows[2].cells[1].text = "496 (500 pre-noise)"
    t1.rows[2].cells[2].text = "49.6%"
    t1.rows[3].cells[0].text = "Total"
    t1.rows[3].cells[1].text = "1000"
    t1.rows[3].cells[2].text = "100%"

    # 3. Update Section IV-B (Paragraph 27)
    p27_text = (
        "Data partitioning applies an 80:20 stratified split with random_state=42 on the noisy labels. The resulting held-out "
        "partition contains exactly 200 records: because label noise is applied prior to splitting, the realized test-set composition "
        "is exactly 99 benign-labelled and 101 covert-labelled records rather than an exact 100/100 split. StandardScaler is fitted "
        "only on the training partition and then applied to both training and test features, preventing information from the held-out "
        "data from influencing scaling parameters. All split IDs, final labels, and predictions are persisted for full auditability."
    )
    doc.paragraphs[27].text = p27_text

    # Update Table II (Table 6 in docx)
    t6 = doc.tables[6]
    for row in t6.rows:
        param = row.cells[0].text.strip()
        if "Total records" in param:
            row.cells[1].text = "1000 synthetic (500 benign, 500 covert pre-noise)"
        elif "Held-out test" in param:
            row.cells[1].text = "200 (99 benign / 101 covert, 80:20 stratified)"
        elif "Label noise" in param or "Measurement noise" in param:
            row.cells[1].text = "4% label flips; 4% Gaussian feature jitter"

    # 4. Update Section VI (Paragraph 48, 49)
    doc.paragraphs[48].text = (
        "The three classifiers were evaluated on the same 200-record held-out synthetic test set (99 benign, 101 covert). "
        "Table III summarizes the resulting metrics. These values describe performance on the generated benchmark and provide "
        "an implemented baseline for comparison with Phase-II empirical capture evaluations."
    )
    doc.paragraphs[49].text = (
        "Logistic Regression correctly classifies 190 of 200 test records (95.00% accuracy, 0.9520 ROC-AUC, 0.9554 PR-AUC). "
        "SVM correctly classifies 190 of 200 (95.00% accuracy, 0.9364 ROC-AUC, 0.9318 PR-AUC), and XGBoost correctly classifies "
        "189 of 200 (94.50% accuracy, 0.9377 ROC-AUC, 0.9004 PR-AUC)."
    )

    # Update Table III (Table 7 in docx)
    t7 = doc.tables[7]
    # Rows: 0=Hdr, 1=XGBoost, 2=SVM, 3=Logistic Regression
    # Cols: Model, Accuracy, Precision, Recall, F1, Specificity, AUC
    t7.rows[1].cells[0].text = "XGBoost"
    t7.rows[1].cells[1].text = "94.50%"
    t7.rows[1].cells[2].text = "95.00%"
    t7.rows[1].cells[3].text = "94.06%"
    t7.rows[1].cells[4].text = "94.53%"
    t7.rows[1].cells[5].text = "94.95%"
    t7.rows[1].cells[6].text = "0.9377"

    t7.rows[2].cells[0].text = "SVM"
    t7.rows[2].cells[1].text = "95.00%"
    t7.rows[2].cells[2].text = "95.05%"
    t7.rows[2].cells[3].text = "95.05%"
    t7.rows[2].cells[4].text = "95.05%"
    t7.rows[2].cells[5].text = "94.95%"
    t7.rows[2].cells[6].text = "0.9364"

    t7.rows[3].cells[0].text = "Logistic Regression"
    t7.rows[3].cells[1].text = "95.00%"
    t7.rows[3].cells[2].text = "95.05%"
    t7.rows[3].cells[3].text = "95.05%"
    t7.rows[3].cells[4].text = "95.05%"
    t7.rows[3].cells[5].text = "94.95%"
    t7.rows[3].cells[6].text = "0.9520"

    # Update Confusion Matrix text (Paragraph 53)
    doc.paragraphs[53].text = (
        "The confusion matrices in Fig. 1 show that Logistic Regression produces 10 total classification errors out of 200 "
        "(94 true negatives, 96 true positives, 5 false positives, and 5 false negatives). SVM similarly produces 10 total errors "
        "(94 TN, 96 TP, 5 FP, 5 FN). XGBoost records 11 total errors (94 TN, 95 TP, 5 FP, 6 FN). "
        "At the fixed 0.5 decision threshold, Logistic Regression and SVM are tied, while Logistic Regression demonstrates superior "
        "probability ranking (0.9520 ROC-AUC and 0.9554 PR-AUC)."
    )

    # Update Table IV (Table 9 in docx) - Feature Importances
    t9 = doc.tables[9]
    # Rows: 0=Hdr, 1..8=Features
    import_data = [
        ("protocol_struct_deviation", "CoverTrace", "55.00%"),
        ("http_header_anomaly_score", "CoverTrace", "28.84%"),
        ("flow_pkt_size_variance", "FlowSight", "3.47%"),
        ("flow_burst_ratio", "FlowSight", "2.60%"),
        ("dns_subdomain_entropy", "CoverTrace", "2.55%"),
        ("icmp_timing_chi2", "CoverTrace", "2.53%"),
        ("flow_iat_mean_ms", "FlowSight", "2.53%"),
        ("flow_avg_pkt_size_log", "FlowSight", "2.48%"),
    ]
    for r_idx, (f, m, val) in enumerate(import_data):
        row = t9.rows[r_idx + 1]
        row.cells[0].text = f
        row.cells[1].text = m
        row.cells[2].text = val

    # Update Section VII Conclusion (Paragraph 74)
    doc.paragraphs[74].text = (
        "This work evaluated XGBoost, a Support Vector Machine, and Logistic Regression on a common synthetic binary-classification "
        "benchmark fusing Operation Cactus's FlowSight flow statistics with its CoverTrace covert-channel indicators. Logistic Regression "
        "achieved 95.00% accuracy and 0.9520 ROC-AUC on the held-out synthetic test set (95.05% recall and 95.54% PR-AUC). Across 10 repeated "
        "seeds, Logistic Regression achieved a mean accuracy of 0.9625 ± 0.0053 and 0.9403 ± 0.0445 true positive rate at a 5% false-positive rate. "
        "An ablation study demonstrated that CoverTrace features provide 0.9517 standalone AUC, FlowSight provides 0.9449 standalone AUC as an "
        "always-on fallback under full payload encryption, and the fused model maximizes overall discrimination (0.9520 AUC), outperforming a simple "
        "entropy threshold by +3.00% accuracy. Permutation importance confirmed that CoverTrace accounts for 79.4% of decision weight versus "
        "20.6% for FlowSight. These results provide an implemented baseline for the detection layer. Planned Phase-II work replaces the synthetic "
        "records with empirical captures from lab tunneling tools (iodine, dnscat2) and links detection to MimicNet's adaptive honeypot deception layer."
    )

    temp_docx = DOCS_PAPER / "temp_updated.docx"
    doc.save(str(temp_docx))

    # Now replace the images inside the docx zip archive with the new figures
    fig1_bytes = (RESULTS_DIR / "fig1_confusion_matrices.png").read_bytes()
    fig2_bytes = (RESULTS_DIR / "fig2_roc_curves.png").read_bytes()
    fig3_bytes = (RESULTS_DIR / "fig3_metrics_comparison.png").read_bytes()

    with zipfile.ZipFile(str(temp_docx), "r") as zin:
        with zipfile.ZipFile(str(out_path), "w") as zout:
            for item in zin.infolist():
                if item.filename == "word/media/62cc89968d264d9f29eb622c5b7bd8c3f1355b7f.png":
                    zout.writestr(item, fig1_bytes)
                elif item.filename == "word/media/a4c2b016444ada586887d9147ed1a8ed6ce0d85e.png":
                    zout.writestr(item, fig2_bytes)
                elif item.filename == "word/media/26b3465f4562127755024d3d581973f2e49c3d3f.png":
                    zout.writestr(item, fig3_bytes)
                else:
                    zout.writestr(item, zin.read(item.filename))

    if temp_docx.exists():
        temp_docx.unlink()

    print(f"Saved revised paper document to: {out_path}")


if __name__ == "__main__":
    revised_paper_path = DOCS_PAPER / REVISED_DOCX_NAME
    response_table_path = DOCS_PAPER / RESPONSE_DOCX_NAME

    update_paper_docx(revised_paper_path)
    build_reviewer_response_docx(response_table_path)

    # Copy directly to Desktop for convenient user access
    desktop_paper = DESKTOP / REVISED_DOCX_NAME
    desktop_response = DESKTOP / RESPONSE_DOCX_NAME

    shutil.copyfile(str(revised_paper_path), str(desktop_paper))
    shutil.copyfile(str(response_table_path), str(desktop_response))

    print(f"Copied {REVISED_DOCX_NAME} to Desktop: {desktop_paper}")
    print(f"Copied {RESPONSE_DOCX_NAME} to Desktop: {desktop_response}")
