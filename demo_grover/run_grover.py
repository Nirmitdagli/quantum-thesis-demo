"""Run Grover vs Brute-Force search experiment."""

import os
import sys
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from utils.timing import Timer
from utils.energy import estimate_energy
from utils.logger import log_result
from demo_grover import grover_quantum, brute_force_classical


def plot_probability_vs_iterations(
    iterations: list, probabilities: list, n_qubits: int, filepath: str
) -> None:
    """Plot success probability vs number of Grover iterations."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(iterations, probabilities, "o-", color="#4C72B0", markersize=4,
            linewidth=1.2, label="Measured probability")

    opt = grover_quantum.optimal_iterations(n_qubits)
    ax.axvline(x=opt, color="red", linestyle="--", alpha=0.7,
               label=f"Optimal iterations = {opt}")

    ax.set_xlabel("Number of Grover Iterations")
    ax.set_ylabel("Success Probability")
    ax.set_title(f"Grover Search: Success Probability vs Iterations "
                 f"({n_qubits} qubits, N={2**n_qubits})")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()


def plot_runtime_scaling(
    qubit_range: list, q_times: list, c_times: list, filepath: str
) -> None:
    """Plot runtime scaling for quantum simulation vs classical brute-force."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogy(qubit_range, q_times, "o-", label="Grover (Quantum Sim)",
                color="#4C72B0", markersize=6)
    ax.semilogy(qubit_range, c_times, "s-", label="Brute Force (Classical)",
                color="#DD8452", markersize=6)

    ax.set_xlabel("Number of Qubits (n)")
    ax.set_ylabel("Runtime (seconds, log scale)")
    ax.set_title("Grover vs Brute-Force: Runtime Scaling")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()


def run() -> dict:
    """Execute the full Grover experiment and return results dictionary."""
    os.makedirs(config.PLOTS_DIR, exist_ok=True)

    print("\n" + "=" * 60)
    print("  EXPERIMENT 3: Grover Search Algorithm")
    print("=" * 60)

    n_qubits = config.GROVER_QUBITS
    rng = np.random.RandomState(config.RANDOM_STATE)
    marked = rng.randint(0, 2 ** n_qubits)
    opt_iters = grover_quantum.optimal_iterations(n_qubits)

    # --- Grover Quantum ---
    print(f"\n  [Grover Quantum] {n_qubits} qubits, "
          f"target |{format(marked, f'0{n_qubits}b')}>, "
          f"{opt_iters} iterations")
    with Timer("Grover") as qt:
        success_prob, _, target_bs = grover_quantum.run_grover(n_qubits, marked)
    q_energy = estimate_energy(qt.elapsed)
    print(f"    Success Probability: {success_prob:.4f}")
    print(f"    Optimal Iterations:  {opt_iters}")
    print(f"    Runtime:             {qt.elapsed:.4f}s")
    print(f"    Energy:              {q_energy[0]:.2f} – {q_energy[1]:.2f} J")

    # --- Classical Brute-Force ---
    print(f"\n  [Brute-Force Classical] Searching {2**n_qubits} states")
    with Timer("BruteForce") as ct:
        c_time, found = brute_force_classical.brute_force_search(n_qubits, marked)
    c_energy = estimate_energy(ct.elapsed)
    print(f"    Found State:         |{format(found, f'0{n_qubits}b')}> "
          f"(target: |{target_bs}>)")
    print(f"    Runtime:             {ct.elapsed:.6f}s")
    print(f"    Energy:              {c_energy[0]:.6f} – {c_energy[1]:.6f} J")

    # --- Probability vs Iterations Plot ---
    print("\n  Generating probability vs iterations plot...")
    iterations, probabilities = grover_quantum.run_grover_varying_iterations(
        n_qubits
    )
    plot_probability_vs_iterations(
        iterations, probabilities, n_qubits,
        os.path.join(config.PLOTS_DIR, "grover_probability_vs_iterations.png"),
    )

    # --- Runtime Scaling Study ---
    print("  Generating runtime scaling plot...")
    qubit_range = list(config.GROVER_SCALING_RANGE)
    q_times = []
    c_times = []
    for nq in qubit_range:
        m = rng.randint(0, 2 ** nq)
        t0 = time.perf_counter()
        grover_quantum.run_grover(nq, m, shots=config.SHOTS)
        q_times.append(time.perf_counter() - t0)
        c_t, _ = brute_force_classical.brute_force_search(nq, m)
        c_times.append(max(c_t, 1e-9))

    plot_runtime_scaling(
        qubit_range, q_times, c_times,
        os.path.join(config.PLOTS_DIR, "grover_runtime_scaling.png"),
    )
    print("  Plots saved.")

    # --- Log ---
    log_result("Grover", "Grover Quantum", "aer_simulator", n_qubits,
               config.SHOTS, success_prob, 0.0, qt.elapsed, *q_energy)
    log_result("Grover", "Brute-Force Classical", "classical", n_qubits,
               0, 1.0, 0.0, ct.elapsed, *c_energy)

    return {
        "quantum": {
            "success_prob": success_prob,
            "runtime": qt.elapsed,
            "energy": q_energy,
        },
        "classical": {"runtime": ct.elapsed, "energy": c_energy},
        "scaling": {
            "qubits": qubit_range,
            "q_times": q_times,
            "c_times": c_times,
        },
    }


if __name__ == "__main__":
    run()
