"""Generate professional architecture diagrams for thesis website."""

import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

OUT = os.path.join(config.PROJECT_DIR, "website", "images")
os.makedirs(OUT, exist_ok=True)

# ── Color palette ──────────────────────────────────────────────
C = {
    "bg":       "#141E33",
    "card":     "#1E2D52",
    "card2":    "#243562",
    "blue":     "#4C9BE8",
    "purple":   "#9C6ADE",
    "green":    "#50C878",
    "orange":   "#F0963C",
    "red":      "#E8555A",
    "cyan":     "#4DD9D9",
    "white":    "#E8ECF4",
    "gray":     "#7A8BA8",
    "gold":     "#FFD700",
}

def new_fig(w=14, h=8):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])
    # Add visible border around diagram
    border = mpatches.FancyBboxPatch(
        (0.1, 0.1), 9.8, 9.8, boxstyle="round,pad=0.1",
        facecolor="none", edgecolor="#4C9BE8", linewidth=2, alpha=0.5)
    ax.add_patch(border)
    return fig, ax

def box(ax, x, y, w, h, label, color, fontsize=10, alpha=0.85, lw=1.5, sub=None):
    rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                           facecolor=color, edgecolor="white", linewidth=lw, alpha=alpha)
    ax.add_patch(rect)
    if sub:
        ax.text(x + w/2, y + h/2 + 0.15, label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color="white")
        ax.text(x + w/2, y + h/2 - 0.2, sub, ha="center", va="center",
                fontsize=fontsize - 2, color=C["gray"])
    else:
        ax.text(x + w/2, y + h/2, label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color="white")

def arrow(ax, x1, y1, x2, y2, color="white"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.5, connectionstyle="arc3,rad=0"))

def title_text(ax, x, y, text, fontsize=14):
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            fontweight="bold", color=C["white"])

def caption_text(ax, text):
    ax.text(5, 0.3, text, ha="center", va="center", fontsize=9,
            color=C["gray"], style="italic")

# ════════════════════════════════════════════════════════════════
# DIAGRAM 1: Classical AI Cloud Architecture
# ════════════════════════════════════════════════════════════════
def diagram_classical():
    fig, ax = new_fig(14, 9)
    ax.set_ylim(0, 10.5)

    title_text(ax, 5, 10, "Figure 1: Classical AI Cloud Architecture", 15)

    # Cloud Platform container
    rect = FancyBboxPatch((0.5, 1), 9, 8.2, boxstyle="round,pad=0.3",
                           facecolor=C["card"], edgecolor=C["blue"], linewidth=2, alpha=0.5)
    ax.add_patch(rect)
    ax.text(5, 8.8, "Cloud Infrastructure (AWS / Azure / GCP)", ha="center", fontsize=12,
            fontweight="bold", color=C["blue"])

    # Data Pipeline
    box(ax, 1, 7.2, 2.5, 0.9, "Data Ingestion", C["card2"], sub="Network Logs, Packets")
    box(ax, 4, 7.2, 2.5, 0.9, "Feature Engineering", C["card2"], sub="Preprocessing, Scaling")
    box(ax, 7, 7.2, 2.5, 0.9, "Data Storage", C["card2"], sub="Data Lake / SQL")
    arrow(ax, 3.5, 7.65, 4, 7.65, C["cyan"])
    arrow(ax, 6.5, 7.65, 7, 7.65, C["cyan"])

    # AI Model Layer
    box(ax, 1.5, 5.3, 3, 1, "AI / ML Models", C["purple"], fontsize=12)
    box(ax, 5.5, 5.3, 3, 1, "Training Pipeline", C["purple"], fontsize=12)
    arrow(ax, 4.5, 5.8, 5.5, 5.8, C["purple"])

    # Compute Layer
    ax.text(5, 4.5, "Compute Layer", ha="center", fontsize=11, fontweight="bold", color=C["orange"])
    box(ax, 1.5, 2.8, 3, 1.2, "CPU Cluster", C["card2"], fontsize=13, sub="General Compute, Logic, I/O")
    box(ax, 5.5, 2.8, 3, 1.2, "GPU Cluster", C["card2"], fontsize=13, sub="Matrix Ops, Training, Inference")
    arrow(ax, 3, 5.3, 3, 4.05, C["orange"])
    arrow(ax, 7, 5.3, 7, 4.05, C["orange"])
    ax.annotate("", xy=(5.5, 3.4), xytext=(4.5, 3.4),
                arrowprops=dict(arrowstyle="<->", color=C["gray"], lw=1.2))

    # Output
    box(ax, 3.5, 1.2, 3, 0.9, "Results / API", C["green"], fontsize=11, sub="Predictions, Dashboards")
    arrow(ax, 3, 2.8, 4.2, 2.15, C["green"])
    arrow(ax, 7, 2.8, 5.8, 2.15, C["green"])

    caption_text(ax, "Figure 1: Classical AI cloud architecture with CPU + GPU compute layers for cybersecurity workloads")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "arch_classical.png"), dpi=150, bbox_inches="tight",
                facecolor=C["bg"])
    plt.close()

# ════════════════════════════════════════════════════════════════
# DIAGRAM 2: Hybrid AI + Quantum Cloud Architecture
# ════════════════════════════════════════════════════════════════
def diagram_hybrid():
    fig, ax = new_fig(14, 10)
    ax.set_ylim(0, 11.5)

    title_text(ax, 5, 11, "Figure 2: Hybrid AI + Quantum Cloud Architecture", 15)

    # Cloud container
    rect = FancyBboxPatch((0.3, 1), 9.4, 9.2, boxstyle="round,pad=0.3",
                           facecolor=C["card"], edgecolor=C["purple"], linewidth=2, alpha=0.5)
    ax.add_patch(rect)
    ax.text(5, 9.8, "Hybrid Cloud Platform", ha="center", fontsize=13,
            fontweight="bold", color=C["purple"])

    # AI Workloads
    box(ax, 1, 8.3, 2.3, 0.9, "Anomaly\nDetection", C["card2"], fontsize=9)
    box(ax, 3.8, 8.3, 2.3, 0.9, "Network\nOptimization", C["card2"], fontsize=9)
    box(ax, 6.7, 8.3, 2.3, 0.9, "Cryptographic\nSearch", C["card2"], fontsize=9)
    ax.text(5, 9.35, "AI + Cybersecurity Workloads", ha="center", fontsize=10,
            fontweight="bold", color=C["cyan"])

    # Orchestration
    box(ax, 2.5, 6.6, 5, 1, "Hybrid Orchestrator / Job Router", C["card2"],
        fontsize=11, sub="Routes tasks to optimal compute unit")
    arrow(ax, 2.15, 8.3, 3.8, 7.65, C["cyan"])
    arrow(ax, 5, 8.3, 5, 7.65, C["cyan"])
    arrow(ax, 7.85, 8.3, 6.2, 7.65, C["cyan"])

    # Compute layer — three columns
    ax.text(5, 5.95, "Hybrid Compute Layer", ha="center", fontsize=11,
            fontweight="bold", color=C["gold"])

    # CPU
    box(ax, 0.8, 4.2, 2.4, 1.3, "CPU", C["blue"], fontsize=14, sub="Logic, Control,\nData Processing")
    # GPU
    box(ax, 3.8, 4.2, 2.4, 1.3, "GPU", C["green"], fontsize=14, sub="Parallel Math,\nML Training")
    # QPU
    box(ax, 6.8, 4.2, 2.4, 1.3, "QPU", C["purple"], fontsize=14, sub="Quantum Kernels,\nOptimization, Search")

    arrow(ax, 3.5, 6.6, 2, 5.55, C["blue"])
    arrow(ax, 5, 6.6, 5, 5.55, C["green"])
    arrow(ax, 6.5, 6.6, 8, 5.55, C["purple"])

    # Interconnect
    ax.annotate("", xy=(3.8, 4.85), xytext=(3.2, 4.85),
                arrowprops=dict(arrowstyle="<->", color=C["gray"], lw=1.2))
    ax.annotate("", xy=(6.8, 4.85), xytext=(6.2, 4.85),
                arrowprops=dict(arrowstyle="<->", color=C["gray"], lw=1.2))

    # Quantum Runtime
    box(ax, 6.3, 2.5, 3.2, 1.2, "Quantum Runtime", C["card2"], fontsize=10,
        sub="Qiskit / Cirq / Braket SDK\nCircuit Compilation, Error Mitigation")
    arrow(ax, 8, 4.2, 7.9, 3.75, C["purple"])

    # Results
    box(ax, 2.5, 1.3, 3.5, 0.8, "Unified Results", C["green"], fontsize=11,
        sub="Accuracy, Latency, Energy")
    arrow(ax, 2, 4.2, 3.5, 2.15, C["blue"])
    arrow(ax, 5, 4.2, 4.5, 2.15, C["green"])
    arrow(ax, 7.9, 2.5, 5.5, 2.15, C["purple"])

    caption_text(ax, "Figure 2: Hybrid AI + Quantum cloud architecture with CPU, GPU, and QPU compute layers")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "arch_hybrid.png"), dpi=150, bbox_inches="tight",
                facecolor=C["bg"])
    plt.close()

# ════════════════════════════════════════════════════════════════
# DIAGRAM 3: Experiment Pipeline
# ════════════════════════════════════════════════════════════════
def diagram_pipeline():
    fig, ax = new_fig(14, 10)
    ax.set_ylim(0, 11)

    title_text(ax, 5, 10.5, "Figure 3: Experimental Evaluation Pipeline", 15)

    # Input
    box(ax, 3.5, 9.2, 3, 0.8, "Dataset Input", C["cyan"], fontsize=12,
        sub="Synthetic Anomaly Data, Random Graphs")

    # Feature Engineering
    box(ax, 3.5, 7.8, 3, 0.8, "Feature Engineering", C["card2"], fontsize=11,
        sub="MinMaxScaler, Graph Generation")
    arrow(ax, 5, 9.2, 5, 8.65, C["cyan"])

    # Branch split
    arrow(ax, 3.5, 7.8, 2, 7.3, C["orange"])
    arrow(ax, 6.5, 7.8, 8, 7.3, C["blue"])

    ax.text(2.25, 7.15, "Classical Branch", ha="center", fontsize=10,
            fontweight="bold", color=C["orange"])
    ax.text(7.75, 7.15, "Quantum Branch", ha="center", fontsize=10,
            fontweight="bold", color=C["blue"])

    # Classical algorithms
    box(ax, 0.8, 5.8, 2.8, 0.7, "RBF SVM", C["orange"], fontsize=10, alpha=0.7)
    box(ax, 0.8, 4.8, 2.8, 0.7, "Greedy MaxCut", C["orange"], fontsize=10, alpha=0.7)
    box(ax, 0.8, 3.8, 2.8, 0.7, "Brute-Force Search", C["orange"], fontsize=10, alpha=0.7)
    arrow(ax, 2.25, 7.0, 2.25, 6.55, C["orange"])

    # Quantum algorithms
    box(ax, 6.4, 5.8, 2.8, 0.7, "QSVM (ZZ Kernel)", C["blue"], fontsize=10, alpha=0.7)
    box(ax, 6.4, 4.8, 2.8, 0.7, "QAOA (p=2)", C["blue"], fontsize=10, alpha=0.7)
    box(ax, 6.4, 3.8, 2.8, 0.7, "Grover Search", C["blue"], fontsize=10, alpha=0.7)
    arrow(ax, 7.75, 7.0, 7.75, 6.55, C["blue"])

    # Merge
    arrow(ax, 2.25, 3.8, 3.8, 3.1, C["orange"])
    arrow(ax, 7.75, 3.8, 6.2, 3.1, C["blue"])

    # Evaluation box
    rect = FancyBboxPatch((2.8, 1.5, ), 4.4, 1.5, boxstyle="round,pad=0.2",
                           facecolor=C["card"], edgecolor=C["gold"], linewidth=2, alpha=0.6)
    ax.add_patch(rect)
    ax.text(5, 2.7, "Evaluation Metrics", ha="center", fontsize=12,
            fontweight="bold", color=C["gold"])

    metrics = ["Accuracy", "Latency", "Energy", "Cost"]
    for i, m in enumerate(metrics):
        mx = 3.3 + i * 1.1
        ax.text(mx, 1.9, m, ha="center", fontsize=9, fontweight="bold", color=C["white"])

    # Output
    box(ax, 3, 0.3, 4, 0.7, "Thesis Results + Plots + Reports", C["green"], fontsize=10)
    arrow(ax, 5, 1.5, 5, 1.05, C["green"])

    caption_text(ax, "Figure 3: Dual-branch experimental pipeline comparing classical and quantum algorithms across four metrics")
    ax.text(5, -0.1, "", ha="center")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "arch_pipeline.png"), dpi=150, bbox_inches="tight",
                facecolor=C["bg"])
    plt.close()

# ════════════════════════════════════════════════════════════════
# DIAGRAM 4: Cloud Implementation
# ════════════════════════════════════════════════════════════════
def diagram_cloud_impl():
    fig, ax = new_fig(14, 9)
    ax.set_ylim(0, 10.5)

    title_text(ax, 5, 10, "Figure 4: Cloud Quantum Implementation Model", 15)

    # User layer
    box(ax, 3, 8.5, 4, 0.8, "Researcher Environment", C["card2"], fontsize=11,
        sub="Python + Qiskit + Experiment Scripts")

    # SDK layer
    arrow(ax, 5, 8.5, 5, 8.0, C["cyan"])
    box(ax, 2.5, 6.8, 5, 0.9, "Quantum SDK / API Layer", C["card2"], fontsize=11,
        sub="Qiskit Runtime  |  Braket SDK  |  Azure Quantum  |  Cirq")

    # Cloud services
    arrow(ax, 3.3, 6.8, 1.6, 6.1, C["blue"])
    arrow(ax, 4.4, 6.8, 3.8, 6.1, C["orange"])
    arrow(ax, 5.6, 6.8, 6.2, 6.1, C["green"])
    arrow(ax, 6.7, 6.8, 8.4, 6.1, C["red"])

    box(ax, 0.3, 4.8, 2.5, 1.2, "IBM\nQuantum", C["blue"], fontsize=11, alpha=0.8)
    box(ax, 3, 4.8, 2.5, 1.2, "AWS\nBraket", C["orange"], fontsize=11, alpha=0.8)
    box(ax, 5.7, 4.8, 2.5, 1.2, "Azure\nQuantum", C["green"], fontsize=11, alpha=0.8)
    box(ax, 7.5, 4.8, 2.2, 1.2, "Google\nQAI", C["red"], fontsize=11, alpha=0.8)

    # Hardware
    ax.text(5, 4.2, "Hardware Layer", ha="center", fontsize=11, fontweight="bold", color=C["gold"])

    box(ax, 0.5, 2.5, 2.5, 1.2, "CPU", C["card2"], fontsize=13,
        sub="x86/ARM Servers")
    box(ax, 3.5, 2.5, 2.5, 1.2, "GPU", C["card2"], fontsize=13,
        sub="NVIDIA A100/H100")
    box(ax, 6.5, 2.5, 3, 1.2, "QPU", C["purple"], fontsize=13,
        sub="Superconducting / Trapped Ion")

    arrow(ax, 1.55, 4.8, 1.75, 3.75, C["gray"])
    arrow(ax, 4.25, 4.8, 4.75, 3.75, C["gray"])
    arrow(ax, 6.95, 4.8, 8, 3.75, C["purple"])

    # Results
    box(ax, 3, 1.2, 4, 0.8, "Metrics: Accuracy | Latency | Energy | Cost", C["green"],
        fontsize=9)
    arrow(ax, 1.75, 2.5, 4, 2.05, C["green"])
    arrow(ax, 4.75, 2.5, 5, 2.05, C["green"])
    arrow(ax, 8, 2.5, 6, 2.05, C["green"])

    caption_text(ax, "Figure 4: Cloud implementation model showing user environment, SDK layer, providers, and hardware")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "arch_cloud_impl.png"), dpi=150, bbox_inches="tight",
                facecolor=C["bg"])
    plt.close()

# ════════════════════════════════════════════════════════════════
# DIAGRAM 5: Final Complete System Architecture
# ════════════════════════════════════════════════════════════════
def diagram_complete():
    fig, ax = new_fig(16, 12)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 14)

    title_text(ax, 6, 13.5, "Figure 5: Complete Thesis System Architecture", 16)

    # ── Layer 1: Cloud Platform ──
    rect = FancyBboxPatch((0.3, 0.5), 11.4, 12.5, boxstyle="round,pad=0.3",
                           facecolor=C["card"], edgecolor=C["purple"], linewidth=2.5, alpha=0.3)
    ax.add_patch(rect)
    ax.text(6, 12.6, "Cloud Platform (IBM / AWS / Azure / GCP)", ha="center",
            fontsize=13, fontweight="bold", color=C["purple"])

    # ── Layer 2: Cybersecurity Workloads ──
    rect2 = FancyBboxPatch((0.8, 10.3), 10.4, 1.8, boxstyle="round,pad=0.2",
                            facecolor=C["card2"], edgecolor=C["cyan"], linewidth=1.5, alpha=0.5)
    ax.add_patch(rect2)
    ax.text(6, 11.8, "Cybersecurity AI Workloads", ha="center", fontsize=11,
            fontweight="bold", color=C["cyan"])
    box(ax, 1.2, 10.5, 2.8, 0.9, "Anomaly Detection\n(QSVM)", C["card2"], fontsize=9)
    box(ax, 4.6, 10.5, 2.8, 0.9, "Network Optimization\n(QAOA)", C["card2"], fontsize=9)
    box(ax, 8, 10.5, 2.8, 0.9, "Crypto Search\n(Grover)", C["card2"], fontsize=9)

    # ── Layer 3: Orchestrator ──
    box(ax, 2.5, 8.8, 7, 1, "Hybrid Orchestrator", C["card2"], fontsize=12,
        sub="Classical/Quantum Job Router  |  Circuit Compiler  |  Error Mitigation")
    arrow(ax, 2.6, 10.5, 4.5, 9.85, C["cyan"])
    arrow(ax, 6, 10.5, 6, 9.85, C["cyan"])
    arrow(ax, 9.4, 10.5, 7.5, 9.85, C["cyan"])

    # ── Layer 4: Hybrid Compute ──
    rect3 = FancyBboxPatch((0.8, 5.8), 10.4, 2.5, boxstyle="round,pad=0.2",
                            facecolor=C["card2"], edgecolor=C["gold"], linewidth=1.5, alpha=0.4)
    ax.add_patch(rect3)
    ax.text(6, 8.0, "Hybrid Compute Layer", ha="center", fontsize=11,
            fontweight="bold", color=C["gold"])

    box(ax, 1.2, 6.1, 2.8, 1.3, "CPU", C["blue"], fontsize=15,
        sub="Control Plane\nData Pipeline\nClassical Algorithms")
    box(ax, 4.6, 6.1, 2.8, 1.3, "GPU", C["green"], fontsize=15,
        sub="ML Training\nMatrix Operations\nNeural Networks")
    box(ax, 8, 6.1, 2.8, 1.3, "QPU", C["purple"], fontsize=15,
        sub="Quantum Kernels\nQAOA Circuits\nGrover Oracle")

    arrow(ax, 4, 8.8, 2.6, 7.45, C["blue"])
    arrow(ax, 6, 8.8, 6, 7.45, C["green"])
    arrow(ax, 8, 8.8, 9.4, 7.45, C["purple"])

    # Interconnects
    ax.annotate("", xy=(4.6, 6.75), xytext=(4, 6.75),
                arrowprops=dict(arrowstyle="<->", color=C["gray"], lw=1.5))
    ax.annotate("", xy=(8, 6.75), xytext=(7.4, 6.75),
                arrowprops=dict(arrowstyle="<->", color=C["gray"], lw=1.5))

    # ── Layer 5: Evaluation ──
    rect4 = FancyBboxPatch((1.5, 3.5), 9, 1.8, boxstyle="round,pad=0.2",
                            facecolor=C["card2"], edgecolor=C["green"], linewidth=1.5, alpha=0.4)
    ax.add_patch(rect4)
    ax.text(6, 5.0, "Evaluation Framework", ha="center", fontsize=11,
            fontweight="bold", color=C["green"])

    metrics = [("Accuracy", C["blue"]), ("Latency", C["orange"]),
               ("Energy", C["green"]), ("Cost", C["purple"])]
    for i, (m, c) in enumerate(metrics):
        mx = 2.5 + i * 2
        box(ax, mx, 3.7, 1.6, 0.7, m, c, fontsize=10, alpha=0.7)

    arrow(ax, 2.6, 6.1, 3.3, 5.35, C["blue"])
    arrow(ax, 6, 6.1, 6, 5.35, C["green"])
    arrow(ax, 9.4, 6.1, 8, 5.35, C["purple"])

    # ── Layer 6: Output ──
    box(ax, 2.5, 1.8, 3, 1, "Results CSV\nPlots & Charts", C["card2"], fontsize=10)
    box(ax, 6.5, 1.8, 3, 1, "Thesis Report\nComparison Tables", C["card2"], fontsize=10)
    arrow(ax, 4, 3.5, 4, 2.85, C["green"])
    arrow(ax, 8, 3.5, 8, 2.85, C["green"])

    box(ax, 3.5, 0.7, 5, 0.7, "Thesis Demo: python run_all_experiments.py", C["green"],
        fontsize=10)
    arrow(ax, 4, 1.8, 5, 1.45, C["green"])
    arrow(ax, 8, 1.8, 7, 1.45, C["green"])

    ax.text(6, 0.15, "Figure 5: Complete system architecture — from cloud platform through hybrid compute to thesis evaluation outputs",
            ha="center", fontsize=9, color=C["gray"], style="italic")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "arch_complete.png"), dpi=150, bbox_inches="tight",
                facecolor=C["bg"])
    plt.close()

# ════════════════════════════════════════════════════════════════
# DIAGRAM 6: Energy Comparison Infographic
# ════════════════════════════════════════════════════════════════
def diagram_energy():
    fig, axes = plt.subplots(1, 2, figsize=(15, 7))
    fig.patch.set_facecolor(C["bg"])
    fig.suptitle("Energy Consumption: Classical Simulation vs Real Quantum Hardware",
                 fontsize=14, fontweight="bold", color=C["white"], y=0.98)

    # Left: Our simulation energy
    ax = axes[0]
    ax.set_facecolor(C["bg"])
    exps = ["QSVM", "QAOA", "Grover"]
    q_sim = [518200, 145258, 2074]
    c_vals = [133, 0.85, 0.13]

    x = np.arange(len(exps))
    w = 0.35
    b1 = ax.bar(x - w/2, q_sim, w, color=C["blue"], alpha=0.85, label="Quantum (Simulator)")
    b2 = ax.bar(x + w/2, c_vals, w, color=C["orange"], alpha=0.85, label="Classical")
    ax.set_xticks(x)
    ax.set_xticklabels(exps, color=C["white"], fontsize=11)
    ax.set_yscale("log")
    ax.set_ylabel("Energy (Joules, log scale)", color=C["white"], fontsize=10)
    ax.set_title("Simulation on Classical Hardware", color=C["cyan"], fontsize=12, fontweight="bold")
    ax.legend(fontsize=9, facecolor=C["card"], edgecolor=C["gray"], labelcolor=C["white"])
    ax.tick_params(colors=C["gray"])
    ax.grid(axis="y", alpha=0.15)
    for spine in ax.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    # Right: Projected real QC hardware
    ax2 = axes[1]
    ax2.set_facecolor(C["bg"])
    platforms = ["Classical\nHPC", "IBM\nQuantum", "AWS\nBraket", "Azure\nQuantinuum", "Google\nQAI"]
    total_energy = [665531, 5520, 1500, 960, 4800]
    colors = [C["orange"], C["blue"], C["orange"], C["green"], C["red"]]

    bars = ax2.bar(platforms, total_energy, color=colors, alpha=0.85, width=0.5)
    for bar, val in zip(bars, total_energy):
        label = f"{val:,.0f} J"
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                 label, ha="center", va="bottom", fontsize=9, fontweight="bold", color=C["white"])
    ax2.set_yscale("log")
    ax2.set_ylabel("Total Energy All 3 Experiments (J, log)", color=C["white"], fontsize=10)
    ax2.set_title("Projected on Real Hardware", color=C["cyan"], fontsize=12, fontweight="bold")
    ax2.tick_params(colors=C["gray"])
    ax2.grid(axis="y", alpha=0.15)
    for spine in ax2.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)
    ax2.set_xticklabels(platforms, color=C["white"], fontsize=9)

    # Savings annotation
    ax2.annotate("693x\nless energy", xy=(3, 960), xytext=(3.8, 50000),
                 fontsize=11, fontweight="bold", color=C["green"],
                 ha="center",
                 arrowprops=dict(arrowstyle="->", color=C["green"], lw=2))

    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "arch_energy_comparison.png"), dpi=150, bbox_inches="tight",
                facecolor=C["bg"])
    plt.close()


if __name__ == "__main__":
    print("Generating architecture diagrams...")
    diagram_classical()
    print("  [1/6] Classical AI Cloud Architecture")
    diagram_hybrid()
    print("  [2/6] Hybrid AI + Quantum Cloud Architecture")
    diagram_pipeline()
    print("  [3/6] Experimental Evaluation Pipeline")
    diagram_cloud_impl()
    print("  [4/6] Cloud Implementation Model")
    diagram_complete()
    print("  [5/6] Complete System Architecture")
    diagram_energy()
    print("  [6/6] Energy Comparison Infographic")
    print(f"\nAll diagrams saved to: {OUT}")
