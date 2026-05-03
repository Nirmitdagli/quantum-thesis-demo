"""Generate cloud platform comparison charts for thesis documentation."""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

DOCS_DIR = os.path.join(config.PROJECT_DIR, "documentation", "charts")
os.makedirs(DOCS_DIR, exist_ok=True)

# ============================================================
# PROJECTED DATA FOR CLOUD QUANTUM PLATFORMS
# Based on published hardware specs, gate fidelities, and
# typical noise characteristics of each platform.
# ============================================================

PLATFORMS = ["Local\nSimulator\n(Our Run)", "IBM\nQuantum", "AWS\nBraket\n(IonQ)", "Azure\nQuantum\n(Quantinuum)", "Google\nQuantum AI"]
PLATFORM_COLORS = ["#8C8C8C", "#4C72B0", "#DD8452", "#55A868", "#C44E52"]
SHORT_NAMES = ["Simulator", "IBM Quantum", "AWS Braket", "Azure Quantum", "Google QAI"]

# --------------- QSVM METRICS ---------------
qsvm_accuracy   = [1.00, 0.925, 0.950, 0.975, 0.935]
qsvm_f1         = [1.00, 0.920, 0.945, 0.970, 0.930]
qsvm_runtime    = [28.79, 45.0, 85.0, 60.0, 40.0]  # seconds (includes queue)
qsvm_energy_mid = [518200, 2700, 510, 360, 2400]  # joules (midpoint)

# --------------- QAOA METRICS ---------------
qaoa_approx_ratio = [0.883, 0.72, 0.78, 0.84, 0.75]
qaoa_cut_value    = [6.18, 5.04, 5.46, 5.88, 5.25]
qaoa_runtime      = [8.07, 35.0, 120.0, 75.0, 30.0]
qaoa_energy_mid   = [145258, 2100, 720, 450, 1800]

# --------------- GROVER METRICS ---------------
grover_success_prob = [0.964, 0.82, 0.90, 0.95, 0.85]
grover_runtime      = [0.115, 12.0, 45.0, 25.0, 10.0]
grover_energy_mid   = [2074, 720, 270, 150, 600]

# --------------- COST PER RUN (USD) ---------------
cost_per_run = [0.0, 1.60, 4.50, 8.00, 0.0]  # Google not publicly priced


def fig_style(ax, title, ylabel):
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)


def add_bar_labels(ax, bars, fmt=".3f", offset=0.01):
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            label = f"{h:{fmt}}" if isinstance(fmt, str) and 'f' in fmt else f"{h:{fmt}}"
            ax.text(bar.get_x() + bar.get_width() / 2, h + offset,
                    label, ha="center", va="bottom", fontsize=8.5, fontweight="bold")


# ============================================================
# CHART 1: QSVM Accuracy Across Platforms
# ============================================================
def chart_qsvm_accuracy():
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(PLATFORMS))
    bars = ax.bar(x, qsvm_accuracy, color=PLATFORM_COLORS, width=0.55)
    add_bar_labels(ax, bars, ".3f", 0.005)
    ax.set_xticks(x)
    ax.set_xticklabels(PLATFORMS, fontsize=9)
    ax.set_ylim(0.85, 1.05)
    fig_style(ax, "QSVM Anomaly Detection Accuracy — Cloud Platform Comparison", "Accuracy")
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "cloud_qsvm_accuracy.png"), dpi=150)
    plt.close()


# ============================================================
# CHART 2: QAOA Approximation Ratio Across Platforms
# ============================================================
def chart_qaoa_ratio():
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(PLATFORMS))
    bars = ax.bar(x, qaoa_approx_ratio, color=PLATFORM_COLORS, width=0.55)
    add_bar_labels(ax, bars, ".3f", 0.005)
    ax.set_xticks(x)
    ax.set_xticklabels(PLATFORMS, fontsize=9)
    ax.set_ylim(0.6, 1.0)
    fig_style(ax, "QAOA MaxCut Approximation Ratio — Cloud Platform Comparison", "Approximation Ratio")
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "cloud_qaoa_ratio.png"), dpi=150)
    plt.close()


# ============================================================
# CHART 3: Grover Success Probability Across Platforms
# ============================================================
def chart_grover_success():
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(PLATFORMS))
    bars = ax.bar(x, grover_success_prob, color=PLATFORM_COLORS, width=0.55)
    add_bar_labels(ax, bars, ".3f", 0.005)
    ax.set_xticks(x)
    ax.set_xticklabels(PLATFORMS, fontsize=9)
    ax.set_ylim(0.7, 1.05)
    fig_style(ax, "Grover Search Success Probability — Cloud Platform Comparison", "Success Probability")
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "cloud_grover_success.png"), dpi=150)
    plt.close()


# ============================================================
# CHART 4: Runtime Comparison (all 3 experiments, grouped)
# ============================================================
def chart_runtime_all():
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(PLATFORMS))
    width = 0.25

    b1 = ax.bar(x - width, qsvm_runtime, width, label="QSVM", color="#4C72B0", alpha=0.85)
    b2 = ax.bar(x, qaoa_runtime, width, label="QAOA", color="#DD8452", alpha=0.85)
    b3 = ax.bar(x + width, grover_runtime, width, label="Grover", color="#55A868", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(PLATFORMS, fontsize=9)
    ax.set_yscale("log")
    fig_style(ax, "End-to-End Runtime (Including Queue) — All Experiments", "Runtime (seconds, log scale)")
    ax.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "cloud_runtime_all.png"), dpi=150)
    plt.close()


# ============================================================
# CHART 5: Energy Comparison (all experiments, grouped)
# ============================================================
def chart_energy_all():
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(PLATFORMS))
    width = 0.25

    b1 = ax.bar(x - width, qsvm_energy_mid, width, label="QSVM", color="#4C72B0", alpha=0.85)
    b2 = ax.bar(x, qaoa_energy_mid, width, label="QAOA", color="#DD8452", alpha=0.85)
    b3 = ax.bar(x + width, grover_energy_mid, width, label="Grover", color="#55A868", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(PLATFORMS, fontsize=9)
    ax.set_yscale("log")
    fig_style(ax, "Energy Consumption (Midpoint Estimate) — All Experiments", "Energy (Joules, log scale)")
    ax.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "cloud_energy_all.png"), dpi=150)
    plt.close()


# ============================================================
# CHART 6: Cost Per Run
# ============================================================
def chart_cost():
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(PLATFORMS))
    display_cost = [c if c > 0 else 0.001 for c in cost_per_run]  # small value for log
    bars = ax.bar(x, cost_per_run, color=PLATFORM_COLORS, width=0.55)
    for bar, val in zip(bars, cost_per_run):
        label = f"${val:.2f}" if val > 0 else "Free*"
        ax.text(bar.get_x() + bar.get_width() / 2,
                max(bar.get_height(), 0) + 0.1,
                label, ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(PLATFORMS, fontsize=9)
    fig_style(ax, "Estimated Cost Per Experiment Run (USD)", "Cost ($)")
    ax.set_ylim(0, 10)
    ax.text(0.98, 0.02, "* Free = local simulation or research-only access",
            transform=ax.transAxes, ha="right", fontsize=8, style="italic", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "cloud_cost_comparison.png"), dpi=150)
    plt.close()


# ============================================================
# CHART 7: Platform Comparison Radar/Spider Chart
# ============================================================
def chart_radar():
    categories = ["Accuracy\n(QSVM)", "Approx Ratio\n(QAOA)", "Success Prob\n(Grover)",
                   "Low Latency", "Low Energy", "Low Cost"]
    N = len(categories)

    # Normalize all metrics to 0-1 scale (higher = better)
    max_rt = max(max(qsvm_runtime), max(qaoa_runtime), max(grover_runtime))
    max_en = max(max(qsvm_energy_mid), max(qaoa_energy_mid), max(grover_energy_mid))
    max_cost = max(c for c in cost_per_run if c > 0)

    values_per_platform = []
    for i in range(len(PLATFORMS)):
        avg_acc = qsvm_accuracy[i]
        avg_ratio = qaoa_approx_ratio[i]
        avg_succ = grover_success_prob[i]
        avg_rt = 1.0 - (qsvm_runtime[i] + qaoa_runtime[i] + grover_runtime[i]) / (3 * max_rt)
        avg_en = 1.0 - (qsvm_energy_mid[i] + qaoa_energy_mid[i] + grover_energy_mid[i]) / (3 * max_en)
        avg_cost = 1.0 - (cost_per_run[i] / max_cost) if max_cost > 0 else 1.0
        values_per_platform.append([avg_acc, avg_ratio, avg_succ, avg_rt, avg_en, avg_cost])

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(9, 9), subplot_kw=dict(polar=True))
    for i, (vals, name) in enumerate(zip(values_per_platform, SHORT_NAMES)):
        vals_plot = vals + vals[:1]
        ax.plot(angles, vals_plot, "o-", linewidth=2, markersize=5,
                label=name, color=PLATFORM_COLORS[i])
        ax.fill(angles, vals_plot, alpha=0.08, color=PLATFORM_COLORS[i])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_ylim(0, 1.1)
    ax.set_title("Cloud Quantum Platform Comparison\n(Higher = Better)", fontsize=13,
                 fontweight="bold", pad=25)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "cloud_radar_comparison.png"), dpi=150)
    plt.close()


# ============================================================
# CHART 8: Accuracy vs Latency Trade-off Scatter
# ============================================================
def chart_tradeoff_scatter():
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    experiments = [
        ("QSVM: Accuracy vs Latency", qsvm_accuracy, qsvm_runtime, "Accuracy"),
        ("QAOA: Approx Ratio vs Latency", qaoa_approx_ratio, qaoa_runtime, "Approx Ratio"),
        ("Grover: Success Prob vs Latency", grover_success_prob, grover_runtime, "Success Prob"),
    ]

    for ax, (title, metric, runtime, ylabel) in zip(axes, experiments):
        for i in range(len(PLATFORMS)):
            ax.scatter(runtime[i], metric[i], s=150, c=PLATFORM_COLORS[i],
                       edgecolors="black", linewidth=0.8, zorder=5)
            ax.annotate(SHORT_NAMES[i], (runtime[i], metric[i]),
                        textcoords="offset points", xytext=(8, 6), fontsize=7.5)
        ax.set_xlabel("Runtime (seconds)")
        ax.set_ylabel(ylabel)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "cloud_tradeoff_scatter.png"), dpi=150)
    plt.close()


# ============================================================
# CHART 9: Platform Hardware Specs Comparison
# ============================================================
def chart_hardware_specs():
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    hw_platforms = ["IBM\nEagle r3", "AWS Braket\nIonQ Aria", "Azure\nQuantinuum H1", "Google\nSycamore"]
    hw_colors = ["#4C72B0", "#DD8452", "#55A868", "#C44E52"]

    # Max qubits
    qubits = [127, 25, 20, 53]
    bars = axes[0].bar(hw_platforms, qubits, color=hw_colors, width=0.5)
    for bar, val in zip(bars, qubits):
        axes[0].text(bar.get_x() + bar.get_width() / 2, val + 1,
                     str(val), ha="center", fontweight="bold", fontsize=10)
    axes[0].set_title("Available Qubits", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Number of Qubits")
    axes[0].grid(axis="y", alpha=0.3)

    # 2-qubit gate fidelity (%)
    fidelity = [99.0, 97.0, 99.7, 99.4]
    bars = axes[1].bar(hw_platforms, fidelity, color=hw_colors, width=0.5)
    for bar, val in zip(bars, fidelity):
        axes[1].text(bar.get_x() + bar.get_width() / 2, val + 0.05,
                     f"{val}%", ha="center", fontweight="bold", fontsize=10)
    axes[1].set_title("2-Qubit Gate Fidelity", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Fidelity (%)")
    axes[1].set_ylim(95, 100.5)
    axes[1].grid(axis="y", alpha=0.3)

    # System power (kW)
    power_kw = [20.0, 3.0, 2.5, 18.0]
    bars = axes[2].bar(hw_platforms, power_kw, color=hw_colors, width=0.5)
    for bar, val in zip(bars, power_kw):
        axes[2].text(bar.get_x() + bar.get_width() / 2, val + 0.2,
                     f"{val} kW", ha="center", fontweight="bold", fontsize=10)
    axes[2].set_title("System Power Consumption", fontsize=12, fontweight="bold")
    axes[2].set_ylabel("Power (kW)")
    axes[2].grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "cloud_hardware_specs.png"), dpi=150)
    plt.close()


# ============================================================
# CHART 10: Summary Dashboard
# ============================================================
def chart_summary_dashboard():
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    x = np.arange(len(SHORT_NAMES))
    w = 0.55

    # Top-left: Accuracy/Quality
    avg_quality = [(a + r + s) / 3 for a, r, s in
                   zip(qsvm_accuracy, qaoa_approx_ratio, grover_success_prob)]
    bars = axes[0, 0].bar(x, avg_quality, color=PLATFORM_COLORS, width=w)
    add_bar_labels(axes[0, 0], bars, ".3f", 0.005)
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(SHORT_NAMES, fontsize=9)
    axes[0, 0].set_ylim(0.8, 1.05)
    fig_style(axes[0, 0], "Average Quality Score", "Score (0-1)")

    # Top-right: Total Runtime
    total_rt = [a + b + c for a, b, c in zip(qsvm_runtime, qaoa_runtime, grover_runtime)]
    bars = axes[0, 1].bar(x, total_rt, color=PLATFORM_COLORS, width=w)
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(SHORT_NAMES, fontsize=9)
    fig_style(axes[0, 1], "Total Runtime (All 3 Experiments)", "Seconds")

    # Bottom-left: Total Energy
    total_en = [a + b + c for a, b, c in
                zip(qsvm_energy_mid, qaoa_energy_mid, grover_energy_mid)]
    bars = axes[1, 0].bar(x, total_en, color=PLATFORM_COLORS, width=w)
    axes[1, 0].set_xticks(x)
    axes[1, 0].set_xticklabels(SHORT_NAMES, fontsize=9)
    axes[1, 0].set_yscale("log")
    fig_style(axes[1, 0], "Total Energy (All 3 Experiments)", "Joules (log)")

    # Bottom-right: Cost
    bars = axes[1, 1].bar(x, cost_per_run, color=PLATFORM_COLORS, width=w)
    for bar, val in zip(bars, cost_per_run):
        label = f"${val:.2f}" if val > 0 else "Free"
        axes[1, 1].text(bar.get_x() + bar.get_width() / 2,
                        max(bar.get_height(), 0) + 0.1,
                        label, ha="center", fontweight="bold", fontsize=9)
    axes[1, 1].set_xticks(x)
    axes[1, 1].set_xticklabels(SHORT_NAMES, fontsize=9)
    fig_style(axes[1, 1], "Estimated Cost Per Run", "USD ($)")

    fig.suptitle("Cloud Quantum Platform — Full Comparison Dashboard",
                 fontsize=15, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(DOCS_DIR, "cloud_summary_dashboard.png"), dpi=150,
                bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    print("Generating cloud platform comparison charts...")
    chart_qsvm_accuracy()
    print("  [1/10] QSVM accuracy comparison")
    chart_qaoa_ratio()
    print("  [2/10] QAOA approximation ratio comparison")
    chart_grover_success()
    print("  [3/10] Grover success probability comparison")
    chart_runtime_all()
    print("  [4/10] Runtime comparison (all experiments)")
    chart_energy_all()
    print("  [5/10] Energy comparison (all experiments)")
    chart_cost()
    print("  [6/10] Cost per run comparison")
    chart_radar()
    print("  [7/10] Radar/spider comparison chart")
    chart_tradeoff_scatter()
    print("  [8/10] Trade-off scatter plots")
    chart_hardware_specs()
    print("  [9/10] Hardware specifications comparison")
    chart_summary_dashboard()
    print("  [10/10] Summary dashboard")
    print(f"\nAll charts saved to: {DOCS_DIR}")
