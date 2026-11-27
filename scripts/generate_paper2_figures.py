"""Generate publication-grade figures for Paper 2 (MimicNet).

Outputs:
- eval/results/paper2_fig1_latency_breakdown.png (In-Process vs. Containerized Latency Breakdown)
- eval/results/paper2_fig2_detection_acceleration.png (Detection Latency: Statistical vs. Closed-Loop)
- eval/results/paper2_fig3_mitre_mapping.png (ATT&CK Technique Mapping and Zero-False Attribution)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = Path(__file__).resolve().parent.parent / "eval" / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Set global academic typography
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif", "serif"]
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 11
plt.rcParams["axes.labelsize"] = 10
plt.rcParams["xtick.labelsize"] = 9
plt.rcParams["ytick.labelsize"] = 9
plt.rcParams["legend.fontsize"] = 9
plt.rcParams["figure.titlesize"] = 12

# =============================================================================
# FIGURE 1: Latency & Lifecycle Breakdown (In-Process vs Container)
# =============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8), dpi=300)

# Panel A: In-Process Micro-Benchmark (Milliseconds)
in_process_stages = [
    "Shell Dialogue\n(SshLikeShell)",
    "MITRE Mapping\n(tag_events)",
    "Rule Synthesis\n(rules_from)",
    "Total Combined\nPipeline",
]
in_process_times = [0.0392, 0.0151, 0.0053, 0.0544]
in_process_stdev = [0.0078, 0.0014, 0.0007, 0.0085]
colors_a = ["#2b5c8f", "#3c80be", "#5ba3e0", "#183e66"]

bars1 = ax1.bar(
    in_process_stages,
    in_process_times,
    yerr=in_process_stdev,
    capsize=4,
    color=colors_a,
    edgecolor="black",
    linewidth=0.8,
    width=0.55,
)
ax1.set_ylabel("Execution Time (milliseconds)", fontweight="bold")
ax1.set_title("(a) In-Process Pipeline Stages (N=500)", fontweight="bold", pad=8)
ax1.grid(axis="y", linestyle="--", alpha=0.5)
ax1.set_ylim(0, 0.075)

for bar in bars1:
    yval = bar.get_height()
    ax1.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 0.003,
        f"{yval:.4f} ms",
        ha="center",
        va="bottom",
        fontsize=8.5,
        fontweight="bold",
    )

# Panel B: Containerized Sandbox Lifecycle (Milliseconds)
docker_stages = [
    "Container Init &\nNamespace Setup",
    "Shell Script\nExecution & Log",
    "Teardown &\nForce Remove",
    "Total Session\n(engage())",
]
docker_times = [420.20, 140.40, 57.80, 618.40]
docker_stdev = [28.40, 9.20, 4.50, 42.15]
colors_b = ["#b0533c", "#d16e54", "#e8927d", "#8c3b27"]

bars2 = ax2.bar(
    docker_stages,
    docker_times,
    yerr=docker_stdev,
    capsize=4,
    color=colors_b,
    edgecolor="black",
    linewidth=0.8,
    width=0.55,
)
ax2.set_ylabel("Execution Time (milliseconds)", fontweight="bold")
ax2.set_title("(b) Docker Sandbox Lifecycle (N=500)", fontweight="bold", pad=8)
ax2.grid(axis="y", linestyle="--", alpha=0.5)
ax2.set_ylim(0, 750)

for bar in bars2:
    yval = bar.get_height()
    ax2.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 20,
        f"{yval:.1f} ms",
        ha="center",
        va="bottom",
        fontsize=8.5,
        fontweight="bold",
    )

plt.tight_layout()
fig1_path = OUT_DIR / "paper2_fig1_latency_breakdown.png"
plt.savefig(fig1_path, bbox_inches="tight")
plt.close()
print("Saved:", fig1_path)

# =============================================================================
# FIGURE 2: Closed-Loop Detection Delay Acceleration
# =============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3.8), dpi=300)

scenarios = [
    "CoverTrace Entropy\n(Statistical Baseline)",
    "FlowSight Cadence\n(Statistical Baseline)",
    "MimicNet QNAME Rule\n(Closed-Loop Active)",
    "MimicNet IP Rule\n(Closed-Loop Active)",
]
packets = [16, 24, 1, 1]
times = [14.20, 21.50, 0.00, 0.00]
confidences = [0.9520, 0.9450, 1.0000, 1.0000]
bar_colors = ["#4a7c59", "#68a077", "#215233", "#123820"]

# Left Panel: Detection Delay in Packets
bars_p = ax1.bar(scenarios, packets, color=bar_colors, edgecolor="black", linewidth=0.8, width=0.55)
ax1.set_ylabel("Packets Required for Detection", fontweight="bold")
ax1.set_title("(a) Packet Delay Before Detection", fontweight="bold", pad=8)
ax1.grid(axis="y", linestyle="--", alpha=0.5)
ax1.set_ylim(0, 30)

for bar in bars_p:
    yval = bar.get_height()
    ax1.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 0.8,
        f"{int(yval)} pkt" if yval == 1 else f"{int(yval)} pkts",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
    )

# Right Panel: Elapsed Detection Time in Seconds
bars_t = ax2.bar(scenarios, times, color=bar_colors, edgecolor="black", linewidth=0.8, width=0.55)
ax2.set_ylabel("Elapsed Detection Delay (seconds)", fontweight="bold")
ax2.set_title("(b) Elapsed Time Before Detection", fontweight="bold", pad=8)
ax2.grid(axis="y", linestyle="--", alpha=0.5)
ax2.set_ylim(0, 26)

for bar, conf in zip(bars_t, confidences):
    yval = bar.get_height()
    label = f"{yval:.2f} s\n(Score: {conf:.4f})" if yval > 0 else "0.00 ms\n(Score: 1.0000)"
    ax2.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 0.8,
        label,
        ha="center",
        va="bottom",
        fontsize=8.5,
        fontweight="bold",
    )

plt.tight_layout()
fig2_path = OUT_DIR / "paper2_fig2_detection_acceleration.png"
plt.savefig(fig2_path, bbox_inches="tight")
plt.close()
print("Saved:", fig2_path)

# =============================================================================
# FIGURE 3: MITRE ATT&CK Technique Mapping Coverage & Zero-Hallucination
# =============================================================================
fig, ax = plt.subplots(figsize=(8.5, 3.6), dpi=300)

techniques = [
    "T1033: User Discovery (whoami)",
    "T1082: System Info Discovery (uname)",
    "T1083: File Discovery (cat /etc/passwd)",
    "T1071.004: App Layer DNS (iodine)",
    "T1572: Protocol Tunneling (iodine -f)",
    "T1048: Exfil Over Alt Protocol (iodine)",
    "T1059.004: Unix Shell (/bin/sh in reply)",
    "Unmapped Inputs (frobnicate, zork)",
]
status_val = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 0.0, 0.0]  # Precision percentage
bar_colors = ["#2b5c8f"] * 6 + ["#b0533c", "#b0533c"]

y_pos = np.arange(len(techniques))
bars = ax.barh(y_pos, status_val, color=bar_colors, edgecolor="black", linewidth=0.8, height=0.6)
ax.set_yticks(y_pos)
ax.set_yticklabels(techniques, fontsize=9.5)
ax.invert_yaxis()
ax.set_xlabel("Attribution Precision (%)", fontweight="bold")
ax.set_title(
    "MITRE ATT&CK Attribution Fidelity: Verified Matches vs. Negative Controls",
    fontweight="bold",
    pad=8,
)
ax.set_xlim(0, 115)
ax.grid(axis="x", linestyle="--", alpha=0.5)

for bar, val in zip(bars, status_val):
    if val > 0:
        ax.text(
            val + 1.5,
            bar.get_y() + bar.get_height() / 2.0,
            "100% Verified (0 FP)",
            ha="left",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="#183e66",
        )
    else:
        ax.text(
            val + 1.5,
            bar.get_y() + bar.get_height() / 2.0,
            "0% (Correctly Rejected Control)",
            ha="left",
            va="center",
            fontsize=8.5,
            fontweight="bold",
            color="#8c3b27",
        )

plt.tight_layout()
fig3_path = OUT_DIR / "paper2_fig3_mitre_mapping.png"
plt.savefig(fig3_path, bbox_inches="tight")
plt.close()
print("Saved:", fig3_path)
