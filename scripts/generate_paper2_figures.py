"""Generate high-resolution, beautifully labelled publication figures for Paper 2 (MimicNet).

Outputs:
- eval/results/paper2_fig1_latency_breakdown.png (In-Process vs. Container Latency Breakdown)
- eval/results/paper2_fig2_detection_acceleration.png (Detection Latency: Statistical vs. Closed-Loop)
- eval/results/paper2_fig3_mitre_mapping.png (ATT&CK Technique Mapping and Attribution Fidelity)
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
plt.rcParams["axes.titlesize"] = 11.5
plt.rcParams["axes.labelsize"] = 10.5
plt.rcParams["xtick.labelsize"] = 9.5
plt.rcParams["ytick.labelsize"] = 9.5
plt.rcParams["legend.fontsize"] = 9.5
plt.rcParams["figure.titlesize"] = 12.5

# =============================================================================
# FIGURE 1: Latency & Lifecycle Breakdown (In-Process vs Container)
# Aspect ratio: 10.333 / 4.0 = 2.5833 (matches Word display 6.20 in x 2.40 in)
# =============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.333, 4.0), dpi=300)

# Panel A: In-Process Micro-Benchmark (Milliseconds)
in_process_stages = [
    "Interactive Shell\n(SshLikeShell)",
    "MITRE Tagging\n(tag_events)",
    "Rule Synthesis\n(rules_from)",
    "Total Response\nPipeline",
]
in_process_times = [0.0392, 0.0151, 0.0053, 0.0544]
in_process_stdev = [0.0078, 0.0014, 0.0007, 0.0085]
colors_a = ["#1f4e79", "#2e75b6", "#5b9bd5", "#0d233a"]

bars1 = ax1.bar(
    in_process_stages,
    in_process_times,
    yerr=in_process_stdev,
    capsize=4,
    color=colors_a,
    edgecolor="black",
    linewidth=0.9,
    width=0.52,
)
ax1.set_ylabel("Execution Time (milliseconds)", fontweight="bold")
ax1.set_title("(a) In-Process Pipeline Stages (N=500)", fontweight="bold", pad=10)
ax1.grid(axis="y", linestyle="--", alpha=0.5)
ax1.set_ylim(0, 0.078)

for bar in bars1:
    yval = bar.get_height()
    ax1.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 0.003,
        f"{yval:.4f} ms",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color="#0d233a",
    )

# Annotation box for in-process total
ax1.text(
    0.96,
    0.92,
    "Total Pipeline: 54.4 µs\n(0.0544 ms)",
    transform=ax1.transAxes,
    ha="right",
    va="top",
    fontsize=9.5,
    fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#eaf2f8", edgecolor="#2e75b6", alpha=0.95),
)

# Panel B: Containerized Sandbox Lifecycle (Milliseconds)
docker_stages = [
    "Container Init &\nJail Setup",
    "Shell Exec &\nEvent Logging",
    "Teardown &\nForce Remove",
    "Total Session\nLifecycle",
]
docker_times = [420.20, 140.40, 57.80, 618.40]
docker_stdev = [28.40, 9.20, 4.50, 42.15]
colors_b = ["#a83232", "#c94c4c", "#e07b7b", "#701f1f"]

bars2 = ax2.bar(
    docker_stages,
    docker_times,
    yerr=docker_stdev,
    capsize=4,
    color=colors_b,
    edgecolor="black",
    linewidth=0.9,
    width=0.52,
)
ax2.set_ylabel("Execution Time (milliseconds)", fontweight="bold")
ax2.set_title("(b) Docker Sandbox Lifecycle (N=500)", fontweight="bold", pad=10)
ax2.grid(axis="y", linestyle="--", alpha=0.5)
ax2.set_ylim(0, 780)

for bar in bars2:
    yval = bar.get_height()
    ax2.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 22,
        f"{yval:.1f} ms",
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        color="#701f1f",
    )

# Annotation box for docker total and relative acceleration
ax2.text(
    0.96,
    0.92,
    "Total Delay: 618.4 ms\nSpeedup: 10,375×",
    transform=ax2.transAxes,
    ha="right",
    va="top",
    fontsize=9.5,
    fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#fdf2e9", edgecolor="#a83232", alpha=0.95),
)

plt.tight_layout()
fig1_path = OUT_DIR / "paper2_fig1_latency_breakdown.png"
plt.savefig(fig1_path, dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("Saved:", fig1_path)

# =============================================================================
# FIGURE 2: Closed-Loop Detection Delay Acceleration
# Aspect ratio: 5.224 / 4.0 = 1.3061 (matches Word display 3.20 in x 2.45 in)
# =============================================================================
fig, ax = plt.subplots(figsize=(5.224, 4.0), dpi=300)

scenarios = [
    "CoverTrace\n(Entropy)",
    "FlowSight\n(Cadence)",
    "MimicNet\n(QNAME Rule)",
    "MimicNet\n(IP Rule)",
]
packets = [16, 24, 1, 1]
delays = ["14.2 s delay", "21.5 s delay", "0.00 ms (1 pkt)", "0.00 ms (1 pkt)"]
bar_colors = ["#c0504d", "#d97775", "#1e6b42", "#2e8b57"]

bars = ax.bar(scenarios, packets, color=bar_colors, edgecolor="black", linewidth=0.9, width=0.50)
ax.set_ylabel("Packets Required for Detection", fontweight="bold")
ax.set_title("Closed-Loop Detection Acceleration", fontweight="bold", pad=12)
ax.grid(axis="y", linestyle="--", alpha=0.5)
ax.set_ylim(0, 31)

for bar, delay in zip(bars, delays):
    yval = bar.get_height()
    # Packet count on top of bar
    ax.text(
        bar.get_x() + bar.get_width() / 2.0,
        yval + 0.9,
        f"{int(yval)} pkt" if yval == 1 else f"{int(yval)} pkts",
        ha="center",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color="black",
    )
    # Elapsed time annotation inside or right above
    y_pos_text = yval / 2.0 if yval > 4 else yval + 3.8
    text_color = "white" if yval > 4 else "#1e6b42"
    ax.text(
        bar.get_x() + bar.get_width() / 2.0,
        y_pos_text,
        delay,
        ha="center",
        va="center",
        fontsize=8.5,
        fontweight="bold",
        color=text_color,
    )

# Legend or callout badge
ax.text(
    0.05,
    0.92,
    "Passive Baseline: 16–24 pkts\nMimicNet Active: 1 pkt (Instant)",
    transform=ax.transAxes,
    ha="left",
    va="top",
    fontsize=9,
    fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.35", facecolor="#f9f9f9", edgecolor="#666666", alpha=0.95),
)

plt.tight_layout()
fig2_path = OUT_DIR / "paper2_fig2_detection_acceleration.png"
plt.savefig(fig2_path, dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("Saved:", fig2_path)

# =============================================================================
# FIGURE 3: MITRE ATT&CK Technique Mapping Coverage & Precision
# Aspect ratio: 5.224 / 4.0 = 1.3061 (matches Word display 3.20 in x 2.45 in)
# =============================================================================
fig, ax = plt.subplots(figsize=(5.224, 4.0), dpi=300)

techniques = [
    "T1033: User Disc. (whoami)",
    "T1082: Sys Info (uname -a)",
    "T1083: File Disc. (passwd)",
    "T1071: DNS Exfil (iodine)",
    "T1572: Tunneling (nc -e)",
    "Control: Neg. (frobnicate)",
]
precisions = [100.0, 100.0, 100.0, 100.0, 100.0, 0.0]
bar_colors = ["#1f4e79"] * 5 + ["#a83232"]

y_pos = np.arange(len(techniques))
bars = ax.barh(y_pos, precisions, color=bar_colors, edgecolor="black", linewidth=0.9, height=0.55)
ax.set_yticks(y_pos)
ax.set_yticklabels(techniques, fontsize=9.5, fontweight="bold")
ax.invert_yaxis()
ax.set_xlabel("Attribution Precision (%)", fontweight="bold")
ax.set_title("MITRE ATT&CK Mapping Fidelity", fontweight="bold", pad=12)
ax.set_xlim(0, 132)
ax.grid(axis="x", linestyle="--", alpha=0.5)

for bar, val in zip(bars, precisions):
    if val > 0:
        ax.text(
            val + 2.0,
            bar.get_y() + bar.get_height() / 2.0,
            "100% (0 FP)",
            ha="left",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#0d233a",
        )
    else:
        ax.text(
            val + 2.0,
            bar.get_y() + bar.get_height() / 2.0,
            "0% FP (Rejected Control)",
            ha="left",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#701f1f",
        )

ax.text(
    0.96,
    0.12,
    "100% Precision on TTPs\n0% False Attribution",
    transform=ax.transAxes,
    ha="right",
    va="bottom",
    fontsize=9,
    fontweight="bold",
    bbox=dict(boxstyle="round,pad=0.35", facecolor="#eaf2f8", edgecolor="#2e75b6", alpha=0.95),
)

plt.tight_layout()
fig3_path = OUT_DIR / "paper2_fig3_mitre_mapping.png"
plt.savefig(fig3_path, dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("Saved:", fig3_path)
