"""Run QAOA vs Classical Greedy MaxCut experiment."""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from utils.timing import Timer
from utils.energy import estimate_energy
from utils.logger import log_result
from demo_qaoa import qaoa_quantum, maxcut_classical


def plot_cut_comparison(
    q_cut: float, c_cut: float, opt_cut: int, filepath: str
) -> None:
    """Bar chart comparing QAOA, Greedy, and Optimal cut values."""
    labels = ["QAOA\n(Quantum)", "Greedy\n(Classical)", "Optimal\n(Exact)"]
    values = [q_cut, float(c_cut), float(opt_cut)]
    colors = ["#4C72B0", "#DD8452", "#55A868"]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(labels, values, color=colors, width=0.5)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
                f"{val:.2f}", ha="center", va="bottom", fontsize=12,
                fontweight="bold")
    ax.set_ylabel("Cut Value")
    ax.set_title("MaxCut Comparison: QAOA vs Greedy vs Optimal")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()


def plot_convergence(convergence: list, filepath: str) -> None:
    """Line plot of QAOA expected cut value during optimization."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(1, len(convergence) + 1), convergence,
            "o-", markersize=2, color="#4C72B0", linewidth=1.0)
    ax.set_xlabel("COBYLA Iteration")
    ax.set_ylabel("Expected Cut Value")
    ax.set_title("QAOA Optimization Convergence (p = 2)")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()


def run() -> dict:
    """Execute the full QAOA experiment and return results dictionary."""
    os.makedirs(config.PLOTS_DIR, exist_ok=True)

    print("\n" + "=" * 60)
    print("  EXPERIMENT 2: QAOA MaxCut Optimization")
    print("=" * 60)

    n_qubits, edges = qaoa_quantum.generate_random_graph()
    optimal_cut = qaoa_quantum.find_max_cut_brute_force(n_qubits, edges)
    print(f"  Graph: {n_qubits} nodes, {len(edges)} edges")
    print(f"  Optimal MaxCut value: {optimal_cut}")

    # --- QAOA Quantum ---
    print("\n  [QAOA Quantum — depth p=2, COBYLA optimizer]")
    with Timer("QAOA") as qt:
        q_cut, convergence = qaoa_quantum.run_qaoa(n_qubits, edges)
    q_energy = estimate_energy(qt.elapsed)
    q_ratio = q_cut / optimal_cut if optimal_cut > 0 else 0.0
    print(f"    Expected Cut Value:  {q_cut:.2f}")
    print(f"    Approximation Ratio: {q_ratio:.4f}")
    print(f"    Runtime:             {qt.elapsed:.2f}s")
    print(f"    Energy:              {q_energy[0]:.1f} – {q_energy[1]:.1f} J")

    # --- Classical Greedy ---
    print("\n  [Greedy Classical Heuristic]")
    with Timer("Greedy") as ct:
        c_cut, set_a, set_b = maxcut_classical.greedy_maxcut(n_qubits, edges)
    c_energy = estimate_energy(ct.elapsed)
    c_ratio = c_cut / optimal_cut if optimal_cut > 0 else 0.0
    print(f"    Cut Value:           {c_cut}")
    print(f"    Approximation Ratio: {c_ratio:.4f}")
    print(f"    Runtime:             {ct.elapsed:.6f}s")
    print(f"    Energy:              {c_energy[0]:.6f} – {c_energy[1]:.6f} J")

    # --- Plots ---
    plot_cut_comparison(
        q_cut, c_cut, optimal_cut,
        os.path.join(config.PLOTS_DIR, "qaoa_cut_comparison.png"),
    )
    plot_convergence(
        convergence,
        os.path.join(config.PLOTS_DIR, "qaoa_convergence.png"),
    )
    print("  Plots saved.")

    # --- Log ---
    log_result("QAOA", "QAOA Quantum", "aer_simulator", n_qubits, config.SHOTS,
               q_cut, q_ratio, qt.elapsed, *q_energy)
    log_result("QAOA", "Greedy Classical", "classical", n_qubits, 0,
               float(c_cut), c_ratio, ct.elapsed, *c_energy)

    return {
        "quantum": {"cut": q_cut, "ratio": q_ratio, "runtime": qt.elapsed, "energy": q_energy},
        "classical": {"cut": c_cut, "ratio": c_ratio, "runtime": ct.elapsed, "energy": c_energy},
        "optimal_cut": optimal_cut,
        "convergence": convergence,
    }


if __name__ == "__main__":
    run()
