"""Generate visualization plots for the hybrid CPU+GPU+QPU simulation."""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
# Global font scaling for publication-quality output in narrow paper columns
plt.rcParams.update({
    "font.size":       14,
    "axes.titlesize":  16,
    "axes.labelsize":  14,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "legend.fontsize": 13,
    "figure.titlesize":18,
    "font.weight":     "bold",
    "axes.labelweight":"bold",
    "axes.titleweight":"bold",
})

from typing import Dict, Any, List


# ── Color palette (matches thesis website) ───────────────────
C = {
    "bg":     "#141E33",
    "card":   "#1E2D52",
    "card2":  "#243562",
    "blue":   "#4C9BE8",
    "purple": "#9C6ADE",
    "green":  "#50C878",
    "orange": "#F0963C",
    "red":    "#E8555A",
    "cyan":   "#4DD9D9",
    "white":  "#E8ECF4",
    "gray":   "#7A8BA8",
    "gold":   "#FFD700",
}

UNIT_COLORS = {"CPU": C["blue"], "GPU": C["green"], "QPU": C["purple"]}


def generate_all_plots(results: Dict[str, Any], output_dir: str,
                       qsvm_multi: Dict = None, qaoa_multi: Dict = None,
                       vqe_multi: Dict = None, cloud_costs: Dict = None):
    """Generate all hybrid simulation visualizations."""
    os.makedirs(output_dir, exist_ok=True)

    plot_pipeline_timeline(results, output_dir)
    plot_unit_utilization(results, output_dir)
    plot_energy_breakdown(results, output_dir)
    plot_experiment_comparison(results, output_dir)
    plot_hybrid_architecture_live(results, output_dir)
    plot_hybrid_dashboard(results, output_dir)

    # v6 plots
    if qsvm_multi is not None:
        plot_classifier_comparison(results, output_dir)
        plot_multirun_boxplot(qsvm_multi, output_dir)
        plot_crossover_projection(results, qsvm_multi, output_dir)
    if qaoa_multi is not None:
        plot_qaoa_boxplot(qaoa_multi, output_dir)

    # v7 plots (cross-workload + cloud + pareto)
    if vqe_multi is not None:
        plot_vqe_convergence(results, vqe_multi, output_dir)
    if cloud_costs is not None and qsvm_multi is not None:
        plot_cloud_cost_comparison(cloud_costs, qsvm_multi, vqe_multi, output_dir)
    if qsvm_multi is not None and vqe_multi is not None:
        plot_cross_workload_comparison(qsvm_multi, vqe_multi, output_dir)
        plot_pareto_frontier(qsvm_multi, output_dir)
        plot_allocation_decision_tree(output_dir)

    print(f"\n  All hybrid plots saved to: {output_dir}")


# ═══════════════════════════════════════════════════════════════
# PLOT 1: Pipeline Timeline (Gantt-style)
# ═══════════════════════════════════════════════════════════════

def plot_pipeline_timeline(results: Dict, output_dir: str):
    """Gantt chart showing when each unit was active."""
    log = results["pipeline_log"]
    fig, ax = plt.subplots(figsize=(16, 8))
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])

    experiments = ["QSVM", "QAOA", "Grover", "VQE"]
    y_positions = {"QSVM": 4, "QAOA": 3, "Grover": 2, "VQE": 1}

    cumulative_time = {"QSVM": 0, "QAOA": 0, "Grover": 0, "VQE": 0}

    for entry in log:
        exp = entry["experiment"]
        unit = entry["unit"]
        runtime = entry["runtime"]
        start = cumulative_time[exp]

        color = UNIT_COLORS.get(unit, C["gray"])
        y = y_positions[exp]

        ax.barh(y, runtime, left=start, height=0.5, color=color,
                edgecolor="white", linewidth=0.5, alpha=0.85)

        # Label if wide enough
        if runtime > 0.05:
            ax.text(start + runtime / 2, y, entry["task"],
                    ha="center", va="center", fontsize=11,
                    color="white", fontweight="bold")

        cumulative_time[exp] += runtime

    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(["Grover", "QAOA", "QSVM"], color=C["white"],
                       fontsize=19, fontweight="bold")
    ax.set_xlabel("Time (seconds)", color=C["white"], fontsize=19)
    ax.set_title("Hybrid Pipeline Timeline — Task Execution per Unit",
                 color=C["white"], fontsize=22, fontweight="bold", pad=15)

    # Legend
    handles = [mpatches.Patch(color=UNIT_COLORS[u], label=u)
               for u in ["CPU", "GPU", "QPU"]]
    ax.legend(handles=handles, loc="upper right", fontsize=16,
              facecolor=C["card"], edgecolor=C["gray"], labelcolor=C["white"])

    ax.tick_params(colors=C["gray"])
    ax.grid(axis="x", alpha=0.15)
    for spine in ax.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "hybrid_pipeline_timeline.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PLOT 2: Unit Utilization Pie + Bar
# ═══════════════════════════════════════════════════════════════

def plot_unit_utilization(results: Dict, output_dir: str):
    """Pie chart of time spent on each unit + bar chart of task counts."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor(C["bg"])

    units = ["CPU", "GPU", "QPU"]
    times = [results["unit_totals"][u] for u in units]
    counts = [results["task_count"][u] for u in units]
    colors = [UNIT_COLORS[u] for u in units]

    # Pie chart
    ax1.set_facecolor(C["bg"])
    wedges, texts, autotexts = ax1.pie(
        times, labels=units, colors=colors, autopct="%1.1f%%",
        startangle=90, textprops={"color": C["white"], "fontweight": "bold"},
        wedgeprops={"edgecolor": C["bg"], "linewidth": 2})
    for t in autotexts:
        t.set_fontsize(11)
        t.set_color("white")
    ax1.set_title("Runtime Distribution by Unit",
                  color=C["white"], fontsize=21, fontweight="bold")

    # Bar chart
    ax2.set_facecolor(C["bg"])
    bars = ax2.bar(units, counts, color=colors, edgecolor="white",
                   linewidth=1, alpha=0.85, width=0.5)
    for bar, count, t in zip(bars, counts, times):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                 f"{count} tasks\n{t:.3f}s",
                 ha="center", va="bottom", color=C["white"],
                 fontsize=16, fontweight="bold")
    ax2.set_ylabel("Number of Tasks", color=C["white"], fontsize=18)
    ax2.set_title("Tasks Executed per Unit",
                  color=C["white"], fontsize=21, fontweight="bold")
    ax2.tick_params(colors=C["gray"])
    for spine in ax2.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)
    ax2.set_xticklabels(units, color=C["white"], fontsize=19)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "hybrid_unit_utilization.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PLOT 3: Energy Breakdown
# ═══════════════════════════════════════════════════════════════

def plot_energy_breakdown(results: Dict, output_dir: str):
    """Stacked bar chart of energy per experiment per unit."""
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])

    experiments = ["QSVM", "QAOA", "Grover", "VQE"]
    log = results["pipeline_log"]

    cpu_energy = []
    gpu_energy = []
    qpu_energy = []

    for exp in experiments:
        exp_log = [e for e in log if e["experiment"] == exp]
        cpu_energy.append(sum(e["energy_j"] for e in exp_log if e["unit"] == "CPU"))
        gpu_energy.append(sum(e["energy_j"] for e in exp_log if e["unit"] == "GPU"))
        qpu_energy.append(sum(e["energy_j"] for e in exp_log if e["unit"] == "QPU"))

    x = np.arange(len(experiments))
    width = 0.5

    ax.bar(x, cpu_energy, width, label="CPU", color=C["blue"], alpha=0.85)
    ax.bar(x, gpu_energy, width, bottom=cpu_energy, label="GPU",
           color=C["green"], alpha=0.85)
    bottoms = [c + g for c, g in zip(cpu_energy, gpu_energy)]
    ax.bar(x, qpu_energy, width, bottom=bottoms, label="QPU",
           color=C["purple"], alpha=0.85)

    # Total labels
    for i, (c, g, q) in enumerate(zip(cpu_energy, gpu_energy, qpu_energy)):
        total = c + g + q
        ax.text(i, total + total * 0.02, f"{total:.1f} J",
                ha="center", va="bottom", color=C["white"],
                fontsize=16, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(experiments, color=C["white"], fontsize=19)
    ax.set_ylabel("Energy (Joules)", color=C["white"], fontsize=18)
    ax.set_title("Energy Consumption by Experiment and Processing Unit",
                 color=C["white"], fontsize=22, fontweight="bold", pad=15)
    ax.legend(fontsize=16, facecolor=C["card"], edgecolor=C["gray"],
              labelcolor=C["white"])
    ax.tick_params(colors=C["gray"])
    ax.grid(axis="y", alpha=0.15)
    for spine in ax.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "hybrid_energy_breakdown.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PLOT 4: Experiment Comparison
# ═══════════════════════════════════════════════════════════════

def plot_experiment_comparison(results: Dict, output_dir: str):
    """Side-by-side classical vs quantum results for all three experiments."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.patch.set_facecolor(C["bg"])
    fig.suptitle("Hybrid Pipeline Results: Classical vs Quantum",
                 color=C["white"], fontsize=24, fontweight="bold", y=1.02)

    # QSVM
    ax = axes[0]
    ax.set_facecolor(C["bg"])
    qc = results["qsvm"]["comparison"]
    metrics = ["Accuracy", "F1 Score"]
    classical = [qc.get("classical_accuracy", qc.get("svm_accuracy", 0)), qc.get("classical_f1", qc.get("svm_f1", 0))]
    quantum = [qc["quantum_accuracy"], qc["quantum_f1"]]
    x = np.arange(len(metrics))
    w = 0.3
    ax.bar(x - w/2, classical, w, color=C["orange"], label="Classical (CPU)",
           alpha=0.85)
    ax.bar(x + w/2, quantum, w, color=C["purple"], label="Quantum (QPU)",
           alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, color=C["white"])
    ax.set_ylim(0, 1.15)
    ax.set_title("QSVM Anomaly Detection", color=C["cyan"], fontsize=19,
                 fontweight="bold")
    ax.legend(fontsize=13, facecolor=C["card"], edgecolor=C["gray"],
              labelcolor=C["white"])
    ax.tick_params(colors=C["gray"])
    for spine in ax.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    # QAOA
    ax = axes[1]
    ax.set_facecolor(C["bg"])
    qc2 = results["qaoa"]["comparison"]
    labels = ["Cut Value", "Approx Ratio"]
    classical2 = [qc2["greedy_cut"], qc2["greedy_ratio"]]
    quantum2 = [qc2["qaoa_cut"], qc2["qaoa_ratio"]]
    optimal = [qc2["optimal_cut"], 1.0]
    x = np.arange(len(labels))
    ax.bar(x - w, classical2, w, color=C["orange"], label="Greedy (CPU)",
           alpha=0.85)
    ax.bar(x, quantum2, w, color=C["purple"], label="QAOA (QPU)", alpha=0.85)
    ax.bar(x + w, optimal, w, color=C["gold"], label="Optimal", alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=C["white"])
    ax.set_title("QAOA MaxCut", color=C["cyan"], fontsize=19,
                 fontweight="bold")
    ax.legend(fontsize=13, facecolor=C["card"], edgecolor=C["gray"],
              labelcolor=C["white"])
    ax.tick_params(colors=C["gray"])
    for spine in ax.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    # Grover
    ax = axes[2]
    ax.set_facecolor(C["bg"])
    qc3 = results["grover"]["comparison"]
    labels3 = ["Iterations/Checks", "Speedup"]
    classical3 = [qc3["classical_checks"], 1]
    quantum3 = [qc3["quantum_iterations"], qc3["speedup_factor"]]
    x = np.arange(len(labels3))
    ax.bar(x - w/2, classical3, w, color=C["orange"],
           label="Brute Force (CPU)", alpha=0.85)
    ax.bar(x + w/2, quantum3, w, color=C["purple"],
           label="Grover (QPU)", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(labels3, color=C["white"])
    ax.set_title("Grover Search", color=C["cyan"], fontsize=19,
                 fontweight="bold")
    ax.legend(fontsize=13, facecolor=C["card"], edgecolor=C["gray"],
              labelcolor=C["white"])
    ax.tick_params(colors=C["gray"])
    for spine in ax.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "hybrid_experiment_comparison.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PLOT 5: Live Architecture Diagram (with data flow arrows)
# ═══════════════════════════════════════════════════════════════

def plot_hybrid_architecture_live(results: Dict, output_dir: str):
    """Architecture diagram annotated with actual runtime/energy data."""
    fig, ax = plt.subplots(figsize=(16, 11))
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 12)
    ax.set_aspect("equal")
    ax.axis("off")

    def box(x, y, w, h, label, color, sub=None, fontsize=18):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                               facecolor=color, edgecolor="white",
                               linewidth=1.5, alpha=0.85)
        ax.add_patch(rect)
        if sub:
            ax.text(x + w/2, y + h/2 + 0.18, label, ha="center",
                    va="center", fontsize=fontsize, fontweight="bold",
                    color="white")
            ax.text(x + w/2, y + h/2 - 0.18, sub, ha="center",
                    va="center", fontsize=max(10, fontsize - 3), color=C["gray"])
        else:
            ax.text(x + w/2, y + h/2, label, ha="center", va="center",
                    fontsize=fontsize, fontweight="bold", color="white")

    def arrow(x1, y1, x2, y2, color="white", lw=1.5):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=color, lw=lw))

    # Title
    ax.text(6, 11.5, "Hybrid CPU + GPU + QPU — Live Simulation Results",
            ha="center", va="center", fontsize=26, fontweight="bold",
            color=C["white"])

    # Workloads
    ax.text(6, 10.8, "Cybersecurity AI Workloads", ha="center",
            fontsize=18, fontweight="bold", color=C["cyan"])
    box(0.5, 9.8, 3.2, 0.8, "Anomaly Detection", C["card2"],
        sub="QSVM Pipeline")
    box(4.4, 9.8, 3.2, 0.8, "Network Optimization", C["card2"],
        sub="QAOA Pipeline")
    box(8.3, 9.8, 3.2, 0.8, "Crypto Search", C["card2"],
        sub="Grover Pipeline")

    # Orchestrator
    box(2, 8.3, 8, 0.9, "Hybrid Orchestrator",
        C["card2"], sub="Job Router  |  Circuit Compiler  |  Pipeline Coordinator")
    arrow(2.1, 9.8, 4, 9.25, C["cyan"])
    arrow(6, 9.8, 6, 9.25, C["cyan"])
    arrow(9.9, 9.8, 8, 9.25, C["cyan"])

    # Compute units with REAL data
    ax.text(6, 7.7, "Hybrid Compute Layer", ha="center", fontsize=19,
            fontweight="bold", color=C["gold"])

    cpu_t = results["unit_totals"]["CPU"]
    gpu_t = results["unit_totals"]["GPU"]
    qpu_t = results["unit_totals"]["QPU"]
    cpu_e = results["energy_totals"]["CPU"]
    gpu_e = results["energy_totals"]["GPU"]
    qpu_e = results["energy_totals"]["QPU"]

    box(0.3, 5.5, 3.4, 1.8, "CPU", C["blue"],
        sub=f"{cpu_t:.4f}s | {cpu_e:.1f}J", fontsize=26)
    box(4.3, 5.5, 3.4, 1.8, "GPU", C["green"],
        sub=f"{gpu_t:.4f}s | {gpu_e:.1f}J", fontsize=26)
    box(8.3, 5.5, 3.4, 1.8, "QPU", C["purple"],
        sub=f"{qpu_t:.4f}s | {qpu_e:.1f}J", fontsize=26)

    # Sub-labels for each unit (with example workloads)
    ax.text(2, 5.3, "Control | Preprocess | Classical ML",
            ha="center", fontsize=12, color=C["gray"])
    ax.text(2, 5.0, "(SVM, RF, GBM, KNN baselines)",
            ha="center", fontsize=10, color=C["gray"], style="italic")
    ax.text(6, 5.3, "Kernels | Matrix Ops | Neural Net",
            ha="center", fontsize=12, color=C["gray"])
    ax.text(6, 5.0, "(Deep features, parallel batching)",
            ha="center", fontsize=10, color=C["gray"], style="italic")
    ax.text(10, 5.3, "QSVM | QAOA | Grover | VQE",
            ha="center", fontsize=12, color=C["gray"])
    ax.text(10, 5.0, "(Quantum kernels, molecular sim.)",
            ha="center", fontsize=10, color=C["gold"], style="italic")

    arrow(4, 8.3, 2, 7.35, C["blue"], lw=2)
    arrow(6, 8.3, 6, 7.35, C["green"], lw=2)
    arrow(8, 8.3, 10, 7.35, C["purple"], lw=2)

    # Interconnects
    ax.annotate("", xy=(4.3, 6.4), xytext=(3.7, 6.4),
                arrowprops=dict(arrowstyle="<->", color=C["gold"], lw=2))
    ax.annotate("", xy=(8.3, 6.4), xytext=(7.7, 6.4),
                arrowprops=dict(arrowstyle="<->", color=C["gold"], lw=2))
    ax.text(4, 6.7, "PCIe", ha="center", fontsize=11, color=C["gold"])
    ax.text(8, 6.7, "Cloud API", ha="center", fontsize=11, color=C["gold"])

    # Results layer
    total_t = results["total_time"]
    total_e = sum(results["energy_totals"].values())
    box(2, 3.5, 8, 1.2, "Unified Results", C["green"],
        sub=f"Total: {total_t:.2f}s | {total_e:.1f}J | {sum(results['task_count'].values())} tasks",
        fontsize=21)
    arrow(2, 5.5, 4, 4.75, C["blue"])
    arrow(6, 5.5, 6, 4.75, C["green"])
    arrow(10, 5.5, 8, 4.75, C["purple"])

    # Results boxes
    qc = results["qsvm"]["comparison"]
    qc2 = results["qaoa"]["comparison"]
    qc3 = results["grover"]["comparison"]

    box(0.5, 1.8, 3.2, 1.2, "QSVM Result", C["card2"],
        sub=f"Acc: {qc.get('svm_accuracy', qc.get('classical_accuracy', 0)):.0%} / {qc['quantum_accuracy']:.0%}")
    box(4.4, 1.8, 3.2, 1.2, "QAOA Result", C["card2"],
        sub=f"Cut: {qc2['greedy_cut']} / {qc2['qaoa_cut']:.1f}")
    box(8.3, 1.8, 3.2, 1.2, "Grover Result", C["card2"],
        sub=f"P(success): {qc3['quantum_success_prob']:.1%}")

    arrow(4, 3.5, 2.1, 3.05, C["green"])
    arrow(6, 3.5, 6, 3.05, C["green"])
    arrow(8, 3.5, 9.9, 3.05, C["green"])

    # Footer
    ax.text(6, 1.1, "Hybrid CPU+GPU+QPU Simulation — Cybersecurity Thesis Demo",
            ha="center", fontsize=16, color=C["gray"], style="italic")
    ax.text(6, 0.6, f"Pipeline: {len(results['pipeline_log'])} steps | "
            f"CPU: {results['task_count']['CPU']} tasks | "
            f"GPU: {results['task_count']['GPU']} tasks | "
            f"QPU: {results['task_count']['QPU']} tasks",
            ha="center", fontsize=14, color=C["gray"])

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "hybrid_architecture_live.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()


# ═══════════════════════════════════════════════════════════════
# PLOT 6: Full Dashboard
# ═══════════════════════════════════════════════════════════════

def plot_hybrid_dashboard(results: Dict, output_dir: str):
    """Full summary dashboard combining all metrics."""
    fig = plt.figure(figsize=(20, 14))
    fig.patch.set_facecolor(C["bg"])
    fig.suptitle("HYBRID CPU + GPU + QPU SIMULATION DASHBOARD",
                 fontsize=29, fontweight="bold", color=C["white"], y=0.98)

    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.3)

    # ── Top row: Unit metrics ─────────────────────────────────
    # Runtime per unit (horizontal bar)
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor(C["bg"])
    units = ["CPU", "GPU", "QPU"]
    times = [results["unit_totals"][u] for u in units]
    colors = [UNIT_COLORS[u] for u in units]
    bars = ax1.barh(units, times, color=colors, alpha=0.85, height=0.5)
    for bar, t in zip(bars, times):
        ax1.text(bar.get_width() + max(times) * 0.02,
                 bar.get_y() + bar.get_height() / 2,
                 f"{t:.4f}s", va="center", color=C["white"],
                 fontsize=16, fontweight="bold")
    ax1.set_title("Runtime by Unit", color=C["cyan"], fontsize=19,
                  fontweight="bold")
    ax1.tick_params(colors=C["gray"])
    ax1.set_yticklabels(units, color=C["white"], fontsize=18)
    for spine in ax1.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    # Energy per unit (horizontal bar)
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor(C["bg"])
    energies = [results["energy_totals"][u] for u in units]
    bars = ax2.barh(units, energies, color=colors, alpha=0.85, height=0.5)
    for bar, e in zip(bars, energies):
        ax2.text(bar.get_width() + max(energies) * 0.02,
                 bar.get_y() + bar.get_height() / 2,
                 f"{e:.1f}J", va="center", color=C["white"],
                 fontsize=16, fontweight="bold")
    ax2.set_title("Energy by Unit", color=C["cyan"], fontsize=19,
                  fontweight="bold")
    ax2.tick_params(colors=C["gray"])
    ax2.set_yticklabels(units, color=C["white"], fontsize=18)
    for spine in ax2.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    # Task count per unit (pie)
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.set_facecolor(C["bg"])
    counts = [results["task_count"][u] for u in units]
    ax3.pie(counts, labels=units, colors=colors, autopct="%1.0f%%",
            textprops={"color": C["white"], "fontweight": "bold"},
            wedgeprops={"edgecolor": C["bg"], "linewidth": 2})
    ax3.set_title("Task Distribution", color=C["cyan"], fontsize=19,
                  fontweight="bold")

    # ── Middle row: Experiment results ────────────────────────
    # QSVM
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.set_facecolor(C["bg"])
    qc = results["qsvm"]["comparison"]
    labels = ["Accuracy", "F1"]
    cl = [qc.get("classical_accuracy", qc.get("svm_accuracy", 0)), qc.get("classical_f1", qc.get("svm_f1", 0))]
    qu = [qc["quantum_accuracy"], qc["quantum_f1"]]
    x = np.arange(len(labels))
    w = 0.3
    ax4.bar(x - w/2, cl, w, color=C["orange"], label="Classical", alpha=0.85)
    ax4.bar(x + w/2, qu, w, color=C["purple"], label="Quantum", alpha=0.85)
    ax4.set_xticks(x)
    ax4.set_xticklabels(labels, color=C["white"])
    ax4.set_ylim(0, 1.2)
    ax4.set_title("QSVM: Anomaly Detection", color=C["cyan"], fontsize=19,
                  fontweight="bold")
    ax4.legend(fontsize=13, facecolor=C["card"], edgecolor=C["gray"],
               labelcolor=C["white"])
    ax4.tick_params(colors=C["gray"])
    for spine in ax4.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    # QAOA
    ax5 = fig.add_subplot(gs[1, 1])
    ax5.set_facecolor(C["bg"])
    qc2 = results["qaoa"]["comparison"]
    labels2 = ["Greedy", "QAOA", "Optimal"]
    vals = [qc2["greedy_cut"], qc2["qaoa_cut"], qc2["optimal_cut"]]
    cols = [C["orange"], C["purple"], C["gold"]]
    bars = ax5.bar(labels2, vals, color=cols, alpha=0.85, width=0.5)
    for bar, v in zip(bars, vals):
        ax5.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                 f"{v:.1f}", ha="center", color=C["white"], fontsize=16,
                 fontweight="bold")
    ax5.set_title("QAOA: MaxCut Value", color=C["cyan"], fontsize=19,
                  fontweight="bold")
    ax5.set_xticklabels(labels2, color=C["white"])
    ax5.tick_params(colors=C["gray"])
    for spine in ax5.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    # Grover
    ax6 = fig.add_subplot(gs[1, 2])
    ax6.set_facecolor(C["bg"])
    qc3 = results["grover"]["comparison"]
    labels3 = ["Classical\nChecks", "Grover\nIterations"]
    vals3 = [qc3["classical_checks"], qc3["quantum_iterations"]]
    cols3 = [C["orange"], C["purple"]]
    bars = ax6.bar(labels3, vals3, color=cols3, alpha=0.85, width=0.5)
    for bar, v in zip(bars, vals3):
        ax6.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                 str(v), ha="center", color=C["white"], fontsize=19,
                 fontweight="bold")
    ax6.set_title(f"Grover: {qc3['speedup_factor']:.1f}x Speedup",
                  color=C["cyan"], fontsize=19, fontweight="bold")
    ax6.set_xticklabels(labels3, color=C["white"])
    ax6.tick_params(colors=C["gray"])
    for spine in ax6.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    # ── Bottom row: Pipeline timeline ─────────────────────────
    ax7 = fig.add_subplot(gs[2, :])
    ax7.set_facecolor(C["bg"])

    log = results["pipeline_log"]
    experiments = ["QSVM", "QAOA", "Grover", "VQE"]
    y_positions = {"QSVM": 4, "QAOA": 3, "Grover": 2, "VQE": 1}
    cumulative_time = {"QSVM": 0, "QAOA": 0, "Grover": 0, "VQE": 0}

    for entry in log:
        exp = entry["experiment"]
        unit = entry["unit"]
        runtime = entry["runtime"]
        start = cumulative_time[exp]
        color = UNIT_COLORS.get(unit, C["gray"])
        y = y_positions[exp]

        ax7.barh(y, runtime, left=start, height=0.5, color=color,
                 edgecolor="white", linewidth=0.5, alpha=0.85)
        if runtime > 0.05:
            ax7.text(start + runtime / 2, y, entry["task"][:15],
                     ha="center", va="center", fontsize=10,
                     color="white", fontweight="bold")
        cumulative_time[exp] += runtime

    ax7.set_yticks([1, 2, 3])
    ax7.set_yticklabels(["Grover", "QAOA", "QSVM"], color=C["white"],
                        fontsize=18)
    ax7.set_xlabel("Time (seconds)", color=C["white"], fontsize=18)
    ax7.set_title("Pipeline Execution Timeline",
                  color=C["white"], fontsize=21, fontweight="bold")

    handles = [mpatches.Patch(color=UNIT_COLORS[u], label=u)
               for u in ["CPU", "GPU", "QPU"]]
    ax7.legend(handles=handles, loc="upper right", fontsize=14,
               facecolor=C["card"], edgecolor=C["gray"], labelcolor=C["white"])
    ax7.tick_params(colors=C["gray"])
    ax7.grid(axis="x", alpha=0.15)
    for spine in ax7.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    plt.savefig(os.path.join(output_dir, "hybrid_simulation_dashboard.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()


# ===================================================================
# PLOT 7: Classifier Comparison Bar Chart (single run)
# ===================================================================

def plot_classifier_comparison(results: Dict, output_dir: str):
    """Grouped bar chart: Accuracy, F1, Precision, Recall for all methods."""
    comp = results["qsvm"]["comparison"]

    methods = ["SVM", "RF", "GBM", "KNN", "QSVM"]
    keys    = ["svm", "rf", "gbm", "knn", "quantum"]
    metrics_names = ["Accuracy", "F1", "Precision", "Recall"]
    metric_keys   = ["accuracy", "f1", "precision", "recall"]

    data = {}
    for m_name, m_key in zip(metrics_names, metric_keys):
        data[m_name] = [comp.get(f"{k}_{m_key}", 0) for k in keys]

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])

    x = np.arange(len(methods))
    width = 0.18
    colors = [C["blue"], C["green"], C["orange"], C["cyan"]]

    for i, (m_name, color) in enumerate(zip(metrics_names, colors)):
        bars = ax.bar(x + i * width, data[m_name], width, label=m_name,
                      color=color, alpha=0.85, edgecolor="white", linewidth=0.5)
        for bar, val in zip(bars, data[m_name]):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f"{val:.2f}", ha="center", va="bottom",
                    color=C["white"], fontsize=10, fontweight="bold")

    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(methods, color=C["white"])
    ax.set_ylabel("Score", color=C["white"])
    ax.set_title("Classifier Comparison: Classical vs Quantum (KDD Cup 99)",
                 color=C["white"], fontsize=16, pad=15)
    ax.set_ylim(0, 1.15)
    ax.tick_params(colors=C["white"])
    ax.legend(loc="upper right", facecolor=C["card"], edgecolor=C["gray"],
              labelcolor=C["white"])
    ax.grid(axis="y", alpha=0.15)
    for spine in ax.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    plt.savefig(os.path.join(output_dir, "classifier_comparison.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"    Saved: classifier_comparison.png")


# ===================================================================
# PLOT 8: Multi-Run Box Plot (QSVM F1 scores)
# ===================================================================

def plot_multirun_boxplot(qsvm_multi: Dict, output_dir: str):
    """Box plot of F1 scores across 30 runs for each classifier."""
    methods = ["QSVM", "SVM", "RF", "GBM", "KNN"]
    keys    = ["quantum", "svm", "rf", "gbm", "knn"]
    colors  = [C["purple"], C["blue"], C["green"], C["orange"], C["cyan"]]

    f1_data = [qsvm_multi[k]["f1"] for k in keys]

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])

    bp = ax.boxplot(f1_data, labels=methods, patch_artist=True,
                    widths=0.5, showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor=C["gold"],
                                   markeredgecolor=C["gold"], markersize=8),
                    medianprops=dict(color=C["white"], linewidth=2),
                    whiskerprops=dict(color=C["gray"]),
                    capprops=dict(color=C["gray"]),
                    flierprops=dict(marker="o", markerfacecolor=C["red"],
                                    markersize=5))

    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
        patch.set_edgecolor(C["white"])

    # Annotate means
    for i, (k, method) in enumerate(zip(keys, methods)):
        vals = qsvm_multi[k]["f1"]
        ax.text(i + 1, np.mean(vals) + 0.02,
                f"{np.mean(vals):.3f}+/-{np.std(vals):.3f}",
                ha="center", color=C["white"], fontsize=10, fontweight="bold")

    ax.set_ylabel("F1 Score", color=C["white"])
    ax.set_title(f"Multi-Run F1 Distribution ({len(f1_data[0])} runs, KDD Cup 99)",
                 color=C["white"], fontsize=16, pad=15)
    ax.tick_params(colors=C["white"])
    ax.grid(axis="y", alpha=0.15)
    for spine in ax.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    plt.savefig(os.path.join(output_dir, "multirun_f1_boxplot.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"    Saved: multirun_f1_boxplot.png")


# ===================================================================
# PLOT 9: QAOA Multi-Run Box Plot
# ===================================================================

def plot_qaoa_boxplot(qaoa_multi: Dict, output_dir: str):
    """Box plot of QAOA approximation ratio across 30 runs."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor(C["bg"])

    # Approximation ratio
    ax = axes[0]
    ax.set_facecolor(C["bg"])
    bp = ax.boxplot([qaoa_multi["qaoa_ratio"]], labels=["QAOA"],
                    patch_artist=True, widths=0.4, showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor=C["gold"],
                                   markeredgecolor=C["gold"], markersize=8),
                    medianprops=dict(color=C["white"], linewidth=2))
    bp["boxes"][0].set_facecolor(C["purple"])
    bp["boxes"][0].set_alpha(0.7)
    bp["boxes"][0].set_edgecolor(C["white"])
    ax.axhline(y=1.0, color=C["green"], linestyle="--", alpha=0.5,
               label="Optimal")
    greedy_mean = np.mean(qaoa_multi["greedy_cut"]) / np.mean(qaoa_multi["optimal_cut"])
    ax.axhline(y=greedy_mean, color=C["orange"], linestyle="--", alpha=0.5,
               label=f"Greedy ({greedy_mean:.2f})")
    ax.set_ylabel("Approximation Ratio", color=C["white"])
    ax.set_title("QAOA MaxCut Approx. Ratio", color=C["white"], fontsize=14)
    ax.tick_params(colors=C["white"])
    ax.legend(facecolor=C["card"], edgecolor=C["gray"], labelcolor=C["white"])
    ax.grid(axis="y", alpha=0.15)
    for spine in ax.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    # Runtime
    ax2 = axes[1]
    ax2.set_facecolor(C["bg"])
    bp2 = ax2.boxplot([qaoa_multi["qaoa_runtime"]], labels=["QAOA"],
                      patch_artist=True, widths=0.4, showmeans=True,
                      meanprops=dict(marker="D", markerfacecolor=C["gold"],
                                     markeredgecolor=C["gold"], markersize=8),
                      medianprops=dict(color=C["white"], linewidth=2))
    bp2["boxes"][0].set_facecolor(C["purple"])
    bp2["boxes"][0].set_alpha(0.7)
    bp2["boxes"][0].set_edgecolor(C["white"])
    ax2.set_ylabel("Runtime (s)", color=C["white"])
    ax2.set_title("QAOA Runtime Distribution", color=C["white"], fontsize=14)
    ax2.tick_params(colors=C["white"])
    ax2.grid(axis="y", alpha=0.15)
    for spine in ax2.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    fig.suptitle(f"QAOA Statistical Validation ({len(qaoa_multi['qaoa_ratio'])} runs)",
                 color=C["white"], fontsize=16, y=1.02)

    plt.savefig(os.path.join(output_dir, "qaoa_multirun_boxplot.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"    Saved: qaoa_multirun_boxplot.png")


# ===================================================================
# PLOT 10: Crossover Projection (Quantum vs Classical Cost Curve)
# ===================================================================

def plot_crossover_projection(results: Dict, qsvm_multi: Dict, output_dir: str):
    """Project when quantum kernel becomes cost-competitive.

    Uses measured per-task costs and theoretical scaling:
      Classical RBF kernel: O(n^2 * d)  where d = feature dimension
      Quantum ZZ kernel:    O(n^2 * log(d))
    Plot cost-per-classification vs feature dimension.
    """
    comp = results["qsvm"]["comparison"]

    # Measured base costs at d=4 features
    d_base = 4
    classical_cost_base = np.mean(qsvm_multi["svm"]["energy"])     # SVM energy
    quantum_cost_base   = np.mean(qsvm_multi["quantum"]["energy"]) # QSVM energy
    rf_cost_base        = np.mean(qsvm_multi["rf"]["energy"])      # RF energy

    # Theoretical scaling
    feature_dims = np.logspace(0.6, 5, 200)  # 4 to 100,000

    # Classical SVM: kernel computation scales O(d) (each RBF entry is d multiplies)
    classical_cost = classical_cost_base * (feature_dims / d_base)

    # Random Forest: scales roughly O(d * log(n)) ~ O(d) for fixed n
    rf_cost = rf_cost_base * (feature_dims / d_base)

    # Quantum kernel: ZZ feature map uses O(d) gates, but on log(d) qubits
    # Real advantage: amplitude encoding gives O(log d) per kernel entry
    # Projected scaling with fault-tolerant hardware
    quantum_cost_today = quantum_cost_base * (feature_dims / d_base)  # today: same scaling, higher constant
    quantum_cost_ft = quantum_cost_base * np.log2(feature_dims) / np.log2(d_base) * 0.01  # fault-tolerant projection

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])

    ax.loglog(feature_dims, classical_cost, color=C["blue"], linewidth=2.5,
              label="Classical SVM (measured, O(d))")
    ax.loglog(feature_dims, rf_cost, color=C["green"], linewidth=2.5,
              label="Random Forest (measured, O(d))")
    ax.loglog(feature_dims, quantum_cost_today, color=C["purple"], linewidth=2.5,
              linestyle="--", label="QSVM today (simulator, O(d))")
    ax.loglog(feature_dims, quantum_cost_ft, color=C["gold"], linewidth=2.5,
              label="QSVM projected (fault-tolerant, O(log d))")

    # Find crossover
    cross_idx = np.argmin(np.abs(classical_cost - quantum_cost_ft))
    cross_d = feature_dims[cross_idx]
    cross_cost = classical_cost[cross_idx]

    ax.scatter([cross_d], [cross_cost], color=C["red"], s=200, zorder=5,
               edgecolors="white", linewidth=2)
    ax.annotate(f"Crossover: d ~ {cross_d:.0f}",
                xy=(cross_d, cross_cost),
                xytext=(cross_d * 3, cross_cost * 5),
                arrowprops=dict(arrowstyle="->", color=C["white"], lw=2),
                color=C["white"], fontsize=13, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", facecolor=C["card"],
                          edgecolor=C["red"], alpha=0.9))

    # Mark today's measured point
    ax.scatter([d_base], [classical_cost_base], color=C["blue"], s=120,
               marker="^", zorder=5, edgecolors="white")
    ax.scatter([d_base], [quantum_cost_base], color=C["purple"], s=120,
               marker="^", zorder=5, edgecolors="white")
    ax.annotate("Today (d=4)", xy=(d_base, quantum_cost_base),
                xytext=(d_base * 3, quantum_cost_base * 1.5),
                arrowprops=dict(arrowstyle="->", color=C["white"], lw=1.5),
                color=C["white"], fontsize=11)

    ax.set_xlabel("Feature Dimensions (d)", color=C["white"])
    ax.set_ylabel("Energy per Classification (J)", color=C["white"])
    ax.set_title("Quantum-Classical Cost Crossover Projection",
                 color=C["white"], fontsize=16, pad=15)
    ax.tick_params(colors=C["white"])
    ax.legend(loc="upper left", facecolor=C["card"], edgecolor=C["gray"],
              labelcolor=C["white"], fontsize=12)
    ax.grid(True, alpha=0.15, which="both")
    for spine in ax.spines.values():
        spine.set_color(C["gray"])
        spine.set_alpha(0.3)

    # Add disclaimer
    ax.text(0.98, 0.02,
            "Projection assumes fault-tolerant hardware\n"
            "with amplitude encoding (O(log d) per entry).\n"
            "Not a deployment prediction.",
            transform=ax.transAxes, ha="right", va="bottom",
            color=C["gray"], fontsize=9, fontstyle="italic",
            bbox=dict(boxstyle="round", facecolor=C["bg"], alpha=0.8))

    plt.savefig(os.path.join(output_dir, "crossover_projection.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"    Saved: crossover_projection.png")


# =====================================================================
# PLOT 11: VQE Convergence (molecular simulation contrast workload)
# =====================================================================

def plot_vqe_convergence(results: Dict, vqe_multi: Dict, output_dir: str):
    """VQE energy convergence vs iteration with exact reference line."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.patch.set_facecolor(C["bg"])

    # Left: single-run convergence trace
    ax = axes[0]
    ax.set_facecolor(C["bg"])
    convergence = results["vqe"]["quantum"]["convergence"]
    exact = results["vqe"]["classical"]["ground_state_energy"]

    iters = np.arange(1, len(convergence) + 1)
    ax.plot(iters, convergence, color=C["purple"], linewidth=2.5, alpha=0.9,
            label="VQE estimate")
    ax.axhline(y=exact, color=C["green"], linestyle="--", linewidth=2,
               label=f"Exact (NumPy): {exact:.4f} Ha")
    ax.scatter([iters[-1]], [convergence[-1]], color=C["gold"], s=180,
               zorder=5, edgecolors="white", linewidth=2,
               label=f"Final: {convergence[-1]:.4f} Ha")

    ax.set_xlabel("COBYLA iteration", color=C["white"])
    ax.set_ylabel("Energy (Hartree)", color=C["white"])
    ax.set_title("VQE Convergence (single run, H2)",
                 color=C["white"], fontsize=14)
    ax.tick_params(colors=C["white"])
    ax.legend(facecolor=C["card"], edgecolor=C["gray"], labelcolor=C["white"],
              loc="upper right")
    ax.grid(alpha=0.15)
    for sp in ax.spines.values():
        sp.set_color(C["gray"])
        sp.set_alpha(0.3)

    # Right: 30-run final-energy distribution
    ax2 = axes[1]
    ax2.set_facecolor(C["bg"])
    bp = ax2.boxplot([vqe_multi["vqe_energy"]], labels=["VQE H2"],
                     patch_artist=True, widths=0.4, showmeans=True,
                     meanprops=dict(marker="D", markerfacecolor=C["gold"],
                                    markeredgecolor=C["gold"], markersize=8),
                     medianprops=dict(color=C["white"], linewidth=2))
    bp["boxes"][0].set_facecolor(C["purple"])
    bp["boxes"][0].set_alpha(0.7)
    bp["boxes"][0].set_edgecolor(C["white"])
    ax2.axhline(y=np.mean(vqe_multi["exact_energy"]),
                color=C["green"], linestyle="--", linewidth=2,
                label=f"Exact: {np.mean(vqe_multi['exact_energy']):.4f} Ha")
    ax2.set_ylabel("VQE final energy (Hartree)", color=C["white"])
    ax2.set_title(f"VQE Distribution ({len(vqe_multi['vqe_energy'])} runs)",
                  color=C["white"], fontsize=14)
    ax2.tick_params(colors=C["white"])
    ax2.legend(facecolor=C["card"], edgecolor=C["gray"], labelcolor=C["white"])
    ax2.grid(axis="y", alpha=0.15)
    for sp in ax2.spines.values():
        sp.set_color(C["gray"])
        sp.set_alpha(0.3)

    fig.suptitle("Workload 2 — Molecular Simulation: H2 Ground State via VQE",
                 color=C["white"], fontsize=16, y=1.02)

    plt.savefig(os.path.join(output_dir, "vqe_convergence.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"    Saved: vqe_convergence.png")


# =====================================================================
# PLOT 12: Cloud Cost Comparison (across workloads and tiers)
# =====================================================================

def plot_cloud_cost_comparison(cloud_costs: Dict, qsvm_multi: Dict,
                               vqe_multi: Dict, output_dir: str):
    """Bar chart: cloud cost per million tasks across tiers and workloads."""
    from .cloud_costs import all_tiers_cost

    qsvm_cost = {t: cloud_costs[t]["cost_per_million_usd"]
                 for t in ["CPU", "GPU", "QPU"]}
    vqe_runtimes = {
        "CPU": float(np.mean(vqe_multi["exact_runtime"])),
        "GPU": 0.001,
        "QPU": float(np.mean(vqe_multi["vqe_runtime"])),
    }
    vqe_cloud = all_tiers_cost(vqe_runtimes, shots=4000)
    vqe_cost = {t: vqe_cloud[t]["cost_per_million_usd"]
                for t in ["CPU", "GPU", "QPU"]}

    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])

    tiers = ["CPU", "GPU", "QPU"]
    x = np.arange(len(tiers))
    width = 0.38

    cy = [qsvm_cost[t] for t in tiers]
    vy = [vqe_cost[t]  for t in tiers]
    bars1 = ax.bar(x - width/2, cy, width, label="Cybersecurity (QSVM)",
                   color=C["blue"], alpha=0.85, edgecolor="white")
    bars2 = ax.bar(x + width/2, vy, width, label="Molecular Sim (VQE)",
                   color=C["purple"], alpha=0.85, edgecolor="white")

    for bar, v in zip(bars1, cy):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f"${v:,.2f}", ha="center", va="bottom",
                color=C["white"], fontsize=11, fontweight="bold")
    for bar, v in zip(bars2, vy):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f"${v:,.2f}", ha="center", va="bottom",
                color=C["white"], fontsize=11, fontweight="bold")

    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(tiers, color=C["white"])
    ax.set_xlabel("Cloud Tier", color=C["white"])
    ax.set_ylabel("Cost per 1M Tasks (USD, log scale)", color=C["white"])
    ax.set_title("Cloud Cost per Workload across CPU/GPU/QPU Tiers (April 2026)",
                 color=C["white"], fontsize=15, pad=15)
    ax.tick_params(colors=C["white"])
    ax.legend(facecolor=C["card"], edgecolor=C["gray"], labelcolor=C["white"])
    ax.grid(axis="y", alpha=0.15, which="both")
    for sp in ax.spines.values():
        sp.set_color(C["gray"])
        sp.set_alpha(0.3)

    plt.savefig(os.path.join(output_dir, "cloud_cost_comparison.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"    Saved: cloud_cost_comparison.png")


# =====================================================================
# PLOT 13: Cross-Workload Comparison (cybersecurity vs molecular)
# =====================================================================

def plot_cross_workload_comparison(qsvm_multi: Dict, vqe_multi: Dict,
                                    output_dir: str):
    """Side-by-side panels: cybersecurity (classical wins) vs
    molecular simulation (quantum needed at scale)."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6.5))
    fig.patch.set_facecolor(C["bg"])

    # Left panel: Cybersecurity — quantum loses
    ax = axes[0]
    ax.set_facecolor(C["bg"])
    methods = ["RF", "GBM", "KNN", "SVM", "QSVM"]
    keys    = ["rf", "gbm", "knn", "svm", "quantum"]
    colors  = [C["green"], C["orange"], C["cyan"], C["blue"], C["purple"]]
    energies = [float(np.mean(qsvm_multi[k]["energy"])) for k in keys]

    bars = ax.bar(methods, energies, color=colors, edgecolor="white",
                  alpha=0.85)
    for b, e in zip(bars, energies):
        ax.text(b.get_x() + b.get_width()/2, b.get_height(),
                f"{e:,.1f} J", ha="center", va="bottom",
                color=C["white"], fontsize=11, fontweight="bold")
    ax.set_yscale("log")
    ax.set_ylabel("Energy per task (J, log)", color=C["white"])
    ax.set_title("Workload 1 — Cybersecurity (KDD Cup 99)\n"
                 "CLASSICAL WINS by ~13,000x",
                 color=C["white"], fontsize=14)
    ax.tick_params(colors=C["white"])
    ax.grid(axis="y", alpha=0.15, which="both")
    for sp in ax.spines.values():
        sp.set_color(C["gray"])
        sp.set_alpha(0.3)

    # Right panel: Molecular — quantum needed at scale
    ax2 = axes[1]
    ax2.set_facecolor(C["bg"])
    n_qubits = np.arange(2, 60)
    classical_ram_gb = (2 ** (2 * n_qubits) * 16) / (1024 ** 3)  # complex128 dense state-vector
    quantum_circuit_depth = n_qubits * 50  # ~50 gates per qubit (illustrative, polynomial)

    ax2.plot(n_qubits, classical_ram_gb, color=C["blue"], linewidth=2.5,
             label="Classical state-vector RAM (GB)")
    ax2.plot(n_qubits, quantum_circuit_depth, color=C["purple"], linewidth=2.5,
             label="Quantum circuit depth (gates)")
    ax2.axhline(y=1024, color=C["red"], linestyle="--", alpha=0.7,
                label="1 TB RAM wall")
    ax2.axvline(x=2, color=C["gold"], linestyle=":", alpha=0.7)
    ax2.text(3, 1e3, "H2 (today, classical wins)", color=C["gold"], fontsize=10)
    ax2.axvline(x=50, color=C["red"], linestyle=":", alpha=0.7)
    ax2.text(40, 1e6, "FeMoco region\n(only quantum feasible)",
             color=C["red"], fontsize=10, ha="right")

    ax2.set_yscale("log")
    ax2.set_xlabel("Number of qubits (n)", color=C["white"])
    ax2.set_ylabel("Resource (log scale)", color=C["white"])
    ax2.set_title("Workload 2 — Molecular Simulation (H2 -> FeMoco)\n"
                  "QUANTUM SCALES POLYNOMIALLY, classical hits RAM wall",
                  color=C["white"], fontsize=14)
    ax2.tick_params(colors=C["white"])
    ax2.legend(facecolor=C["card"], edgecolor=C["gray"], labelcolor=C["white"],
               loc="upper left")
    ax2.grid(alpha=0.15, which="both")
    for sp in ax2.spines.values():
        sp.set_color(C["gray"])
        sp.set_alpha(0.3)

    fig.suptitle("Cross-Workload Analysis: Two Contrasting Verdicts on Quantum",
                 color=C["white"], fontsize=17, y=1.02, fontweight="bold")
    plt.savefig(os.path.join(output_dir, "cross_workload_comparison.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"    Saved: cross_workload_comparison.png")


# =====================================================================
# PLOT 14: Pareto Frontier (cost x energy x accuracy)
# =====================================================================

def plot_pareto_frontier(qsvm_multi: Dict, output_dir: str):
    """Pareto frontier across cybersecurity classifiers."""
    from .allocation_rule import pareto_optimal
    from .cloud_costs import cost_per_task

    methods = []
    spec = [
        ("SVM",  "svm",     "CPU", C["blue"]),
        ("RF",   "rf",      "CPU", C["green"]),
        ("GBM",  "gbm",     "CPU", C["orange"]),
        ("KNN",  "knn",     "CPU", C["cyan"]),
        ("QSVM", "quantum", "QPU", C["purple"]),
    ]
    for name, key, tier, color in spec:
        runtime = float(np.mean(qsvm_multi[key]["runtime"]))
        energy  = float(np.mean(qsvm_multi[key]["energy"]))
        f1      = float(np.mean(qsvm_multi[key]["f1"]))
        cost    = cost_per_task(tier, runtime, n_shots=2000)
        methods.append({"name": name, "color": color, "tier": tier,
                        "cost": cost, "energy": energy,
                        "latency": runtime, "accuracy": f1})

    P = pareto_optimal(methods)
    P_names = {m["name"] for m in P}

    fig, ax = plt.subplots(figsize=(12, 8))
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])

    for m in methods:
        is_pareto = m["name"] in P_names
        size = 600 if is_pareto else 250
        edge = C["gold"] if is_pareto else "white"
        lw   = 3 if is_pareto else 1
        ax.scatter(m["energy"], m["accuracy"], s=size, color=m["color"],
                   edgecolor=edge, linewidth=lw, alpha=0.9, zorder=3 if is_pareto else 2)
        label = f"{m['name']} (Pareto)" if is_pareto else m["name"]
        offset_y = 0.015 if m["name"] != "SVM" else -0.025
        ax.annotate(label, xy=(m["energy"], m["accuracy"]),
                    xytext=(m["energy"] * 1.6, m["accuracy"] + offset_y),
                    color=C["white"], fontsize=12, fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color=C["gray"], lw=0.8))

    # Connect Pareto-optimal points
    P_sorted = sorted(P, key=lambda m: m["energy"])
    if len(P_sorted) > 1:
        ax.plot([m["energy"] for m in P_sorted],
                [m["accuracy"] for m in P_sorted],
                "--", color=C["gold"], linewidth=2, alpha=0.7,
                label="Pareto frontier")

    ax.set_xscale("log")
    ax.set_xlabel("Energy per task (J, log)", color=C["white"])
    ax.set_ylabel("F1 score", color=C["white"])
    ax.set_title("Pareto Frontier: Energy vs. Accuracy on Cybersecurity Workload",
                 color=C["white"], fontsize=15, pad=15)
    ax.tick_params(colors=C["white"])
    ax.legend(facecolor=C["card"], edgecolor=C["gray"], labelcolor=C["white"],
              loc="lower right")
    ax.grid(alpha=0.15, which="both")
    for sp in ax.spines.values():
        sp.set_color(C["gray"])
        sp.set_alpha(0.3)

    ax.text(0.02, 0.98,
            f"Pareto-optimal methods: {sorted(P_names)}\n"
            f"Dominated:              {sorted({m['name'] for m in methods} - P_names)}",
            transform=ax.transAxes, va="top", color=C["gold"],
            fontsize=11, family="monospace",
            bbox=dict(boxstyle="round", facecolor=C["card"], alpha=0.85,
                      edgecolor=C["gray"]))

    plt.savefig(os.path.join(output_dir, "pareto_frontier.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"    Saved: pareto_frontier.png")


# =====================================================================
# PLOT 15: Allocation Decision Tree (the headline visual)
# =====================================================================

def plot_allocation_decision_tree(output_dir: str):
    """Visual representation of the workload-aware allocation rule."""
    fig, ax = plt.subplots(figsize=(16, 10))
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def node(x, y, w, h, label, color, sub=None, fontsize=12):
        rect = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.15",
                              facecolor=color, edgecolor="white", linewidth=1.5,
                              alpha=0.9)
        ax.add_patch(rect)
        if sub:
            ax.text(x, y + h/4, label, ha="center", va="center",
                    fontsize=fontsize, fontweight="bold", color="white")
            ax.text(x, y - h/4, sub, ha="center", va="center",
                    fontsize=fontsize - 2, color=C["gray"])
        else:
            ax.text(x, y, label, ha="center", va="center",
                    fontsize=fontsize, fontweight="bold", color="white")

    def edge(x1, y1, x2, y2, label="", color=None):
        c = color or C["gray"]
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", color=c, lw=1.8))
        if label:
            ax.text((x1 + x2)/2, (y1 + y2)/2 + 0.15, label,
                    ha="center", color=C["gold"], fontsize=10,
                    fontweight="bold", style="italic")

    # Root
    node(8, 9.2, 4, 0.9, "Workload arrives", C["card2"],
         sub="What type? What size?", fontsize=14)

    # Three branches
    node(3,  7.5, 3.4, 0.8, "Molecular simulation", C["purple"], fontsize=11)
    node(8,  7.5, 3.4, 0.8, "Classical ML",         C["blue"],   fontsize=11)
    node(13, 7.5, 3.4, 0.8, "Combinatorial opt.",   C["orange"], fontsize=11)
    edge(8, 8.7, 3,  7.9, "molecular", C["purple"])
    edge(8, 8.7, 8,  7.9, "tabular/ML", C["blue"])
    edge(8, 8.7, 13, 7.9, "MaxCut/SAT", C["orange"])

    # Sub-decisions
    # Molecular branch
    node(1.6, 5.7, 2.6, 0.7, "n <= 30 qubits?", C["card2"], fontsize=10)
    node(4.4, 5.7, 2.4, 0.7, "n > 30 qubits?",  C["card2"], fontsize=10)
    edge(3, 7.1, 1.6, 6.05)
    edge(3, 7.1, 4.4, 6.05)

    # Classical-ML branch
    node(6,   5.7, 2.0, 0.7, "d < 100",  C["card2"], fontsize=10)
    node(8,   5.7, 2.0, 0.7, "d < 10K",  C["card2"], fontsize=10)
    node(10,  5.7, 2.2, 0.7, "d >= 10K", C["card2"], fontsize=10)
    edge(8, 7.1, 6,  6.05)
    edge(8, 7.1, 8,  6.05)
    edge(8, 7.1, 10, 6.05)

    # Combinatorial branch
    node(11.6, 5.7, 2.4, 0.7, "n < 50",  C["card2"], fontsize=10)
    node(14.4, 5.7, 2.4, 0.7, "n >= 50", C["card2"], fontsize=10)
    edge(13, 7.1, 11.6, 6.05)
    edge(13, 7.1, 14.4, 6.05)

    # Tier outcomes
    node(1.6, 3.6, 2.0, 1.0, "CPU", C["blue"],   sub="(diagonalize)", fontsize=18)
    node(4.4, 3.6, 2.0, 1.0, "QPU", C["purple"], sub="(only feasible)", fontsize=18)
    node(6,   3.6, 1.6, 1.0, "CPU", C["blue"],   sub="(SVM/RF)", fontsize=18)
    node(8,   3.6, 1.6, 1.0, "GPU", C["green"],  sub="(NN/kernel)", fontsize=18)
    node(10,  3.6, 1.8, 1.0, "MEAS",C["orange"], sub="(use HERO)", fontsize=15)
    node(11.6,3.6, 2.0, 1.0, "CPU", C["blue"],   sub="(greedy/DP)", fontsize=18)
    node(14.4,3.6, 2.0, 1.0, "QPU", C["purple"], sub="(QAOA)", fontsize=18)

    edge(1.6, 5.35, 1.6, 4.1, "yes", C["green"])
    edge(4.4, 5.35, 4.4, 4.1, "yes", C["red"])
    edge(6,   5.35, 6,   4.1, "yes", C["green"])
    edge(8,   5.35, 8,   4.1, "yes", C["green"])
    edge(10,  5.35, 10,  4.1, "yes", C["orange"])
    edge(11.6,5.35, 11.6,4.1, "yes", C["green"])
    edge(14.4,5.35, 14.4,4.1, "yes", C["red"])

    # Examples row
    node(1.6, 1.8, 2.0, 0.8, "H2, LiH",       C["card"], fontsize=10)
    node(4.4, 1.8, 2.0, 0.8, "FeMoco, ATP",   C["card"], fontsize=10)
    node(6,   1.8, 1.6, 0.8, "IDS, fraud",    C["card"], fontsize=10)
    node(8,   1.8, 1.6, 0.8, "ImageNet, RAG", C["card"], fontsize=10)
    node(10,  1.8, 1.8, 0.8, "Genomics, HEP", C["card"], fontsize=10)
    node(11.6,1.8, 2.0, 0.8, "Routing 12-N",  C["card"], fontsize=10)
    node(14.4,1.8, 2.0, 0.8, "Logistics 1k", C["card"], fontsize=10)

    for i, x in enumerate([1.6, 4.4, 6, 8, 10, 11.6, 14.4]):
        edge(x, 3.1, x, 2.2)

    ax.text(8, 0.6,
            "Algorithm 1: Workload-aware Tier Allocation. "
            "Thresholds calibrated from HERO measurements (Section VII).",
            ha="center", color=C["gray"], fontsize=12, style="italic")

    ax.text(8, 9.85, "HERO Allocation Rule",
            ha="center", color=C["white"], fontsize=22, fontweight="bold")

    plt.savefig(os.path.join(output_dir, "allocation_decision_tree.png"),
                dpi=150, bbox_inches="tight", facecolor=C["bg"])
    plt.close()
    print(f"    Saved: allocation_decision_tree.png")
