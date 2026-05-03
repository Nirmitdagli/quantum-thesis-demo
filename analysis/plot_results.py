"""Generate publication-quality analysis plots from results.csv."""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def load_results() -> pd.DataFrame:
    """Load the experiment results CSV."""
    return pd.read_csv(config.RESULTS_CSV)


def plot_accuracy_comparison(df: pd.DataFrame) -> None:
    """Bar chart of primary metric for each algorithm across experiments."""
    fig, ax = plt.subplots(figsize=(10, 6))
    experiments = df["experiment"].unique()
    x = np.arange(len(experiments))
    width = 0.3

    # For each experiment, plot quantum (first row) and classical (second row)
    quantum_vals = []
    classical_vals = []
    q_labels = []
    c_labels = []
    for exp in experiments:
        sub = df[df["experiment"] == exp]
        rows = sub.to_dict("records")
        quantum_vals.append(rows[0]["metric_primary"])
        q_labels.append(rows[0]["algorithm"])
        if len(rows) > 1:
            classical_vals.append(rows[1]["metric_primary"])
            c_labels.append(rows[1]["algorithm"])
        else:
            classical_vals.append(0)
            c_labels.append("")

    bars_q = ax.bar(x - width / 2, quantum_vals, width,
                    label="Quantum", color="#4C72B0")
    bars_c = ax.bar(x + width / 2, classical_vals, width,
                    label="Classical", color="#DD8452")

    for bars in [bars_q, bars_c]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                        f"{h:.3f}", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(experiments)
    ax.set_ylabel("Primary Metric Value")
    ax.set_title("Primary Metric Comparison — Quantum vs Classical")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOTS_DIR, "accuracy_comparison.png"), dpi=150)
    plt.close()


def plot_runtime_comparison(df: pd.DataFrame) -> None:
    """Grouped bar chart of runtime for quantum vs classical."""
    fig, ax = plt.subplots(figsize=(10, 6))
    experiments = df["experiment"].unique()
    x = np.arange(len(experiments))
    width = 0.3

    q_runtimes = []
    c_runtimes = []
    for exp in experiments:
        sub = df[df["experiment"] == exp]
        rows = sub.to_dict("records")
        q_runtimes.append(rows[0]["runtime_seconds"])
        c_runtimes.append(rows[1]["runtime_seconds"] if len(rows) > 1 else 0)

    bars_q = ax.bar(x - width / 2, q_runtimes, width,
                    label="Quantum", color="#4C72B0")
    bars_c = ax.bar(x + width / 2, c_runtimes, width,
                    label="Classical", color="#DD8452")

    for bars in [bars_q, bars_c]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                label = f"{h:.2f}s" if h >= 0.01 else f"{h:.1e}s"
                ax.text(bar.get_x() + bar.get_width() / 2, h,
                        label, ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(experiments)
    ax.set_ylabel("Runtime (seconds)")
    ax.set_title("Runtime Comparison — Quantum vs Classical")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOTS_DIR, "runtime_comparison.png"), dpi=150)
    plt.close()


def plot_energy_estimation(df: pd.DataFrame) -> None:
    """Bar chart with error bars showing energy estimation ranges."""
    fig, ax = plt.subplots(figsize=(11, 6))

    labels = []
    mids = []
    errs_low = []
    errs_high = []
    colors = []

    for _, row in df.iterrows():
        labels.append(f"{row['experiment']}\n{row['algorithm']}")
        low = row["energy_low"]
        high = row["energy_high"]
        mid = (low + high) / 2.0
        mids.append(mid)
        errs_low.append(mid - low)
        errs_high.append(high - mid)
        is_quantum = any(kw in row["algorithm"].lower()
                         for kw in ["quantum", "qaoa", "grover"])
        colors.append("#4C72B0" if is_quantum else "#DD8452")

    x = np.arange(len(labels))
    ax.bar(x, mids, color=colors, alpha=0.85)
    ax.errorbar(x, mids, yerr=[errs_low, errs_high],
                fmt="none", ecolor="black", capsize=5, linewidth=1.5)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Energy (Joules)")
    ax.set_title("Energy Estimation — Cloud Model (PUE = 1.2)")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOTS_DIR, "energy_estimation.png"), dpi=150)
    plt.close()


def plot_cut_value_comparison(df: pd.DataFrame) -> None:
    """QAOA-specific cut value comparison from logged results."""
    qaoa = df[df["experiment"] == "QAOA"]
    if qaoa.empty:
        return

    fig, ax = plt.subplots(figsize=(7, 5))
    labels = qaoa["algorithm"].tolist()
    values = qaoa["metric_primary"].astype(float).tolist()
    colors = ["#4C72B0", "#DD8452"]

    bars = ax.bar(labels, values, color=colors[:len(labels)], width=0.4)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                f"{val:.2f}", ha="center", fontsize=11, fontweight="bold")

    ax.set_ylabel("Cut Value")
    ax.set_title("QAOA vs Greedy — MaxCut Results")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOTS_DIR, "cut_value_comparison.png"), dpi=150)
    plt.close()


def plot_grover_scaling(df: pd.DataFrame) -> None:
    """Grover vs Brute-Force runtime bar comparison from logged data."""
    grover = df[df["experiment"] == "Grover"]
    if grover.empty:
        return

    fig, ax = plt.subplots(figsize=(7, 5))
    labels = grover["algorithm"].tolist()
    runtimes = grover["runtime_seconds"].astype(float).tolist()
    colors = ["#4C72B0", "#DD8452"]

    bars = ax.bar(labels, runtimes, color=colors[:len(labels)], width=0.4)
    for bar, val in zip(bars, runtimes):
        label = f"{val:.4f}s" if val >= 0.001 else f"{val:.2e}s"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                label, ha="center", va="bottom", fontsize=10)

    ax.set_ylabel("Runtime (seconds)")
    ax.set_title("Grover vs Brute-Force — Runtime at 4 Qubits")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(config.PLOTS_DIR, "grover_scaling.png"), dpi=150)
    plt.close()


def generate_all_plots() -> None:
    """Generate all analysis plots from results.csv."""
    os.makedirs(config.PLOTS_DIR, exist_ok=True)
    df = load_results()
    plot_accuracy_comparison(df)
    plot_runtime_comparison(df)
    plot_energy_estimation(df)
    plot_cut_value_comparison(df)
    plot_grover_scaling(df)
    print(f"  Analysis plots saved to {config.PLOTS_DIR}")


if __name__ == "__main__":
    generate_all_plots()
