"""Main entry point: run all quantum thesis demo experiments.

Usage:
    python run_all_experiments.py

Executes three experiments (QSVM, QAOA, Grover), logs all results,
generates publication-quality plots, and produces a final summary report.
"""

import os
import sys
import time

# Ensure project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from utils.logger import clear_results
from demo_qsvm.run_qsvm import run as run_qsvm
from demo_qaoa.run_qaoa import run as run_qaoa
from demo_grover.run_grover import run as run_grover
from analysis.plot_results import generate_all_plots
from analysis.generate_tables import generate_all as generate_tables


def print_comparison_table(
    qsvm_res: dict, qaoa_res: dict, grover_res: dict
) -> None:
    """Print a formatted quantum vs classical comparison table."""
    print("\n" + "=" * 72)
    print("  QUANTUM vs CLASSICAL — COMPARISON TABLE")
    print("=" * 72)
    header = (f"  {'Experiment':<12} {'Algorithm':<22} "
              f"{'Metric':<10} {'Runtime(s)':<12} {'Energy(J)':<16}")
    print(header)
    print("  " + "-" * 68)

    # QSVM
    q = qsvm_res["quantum"]
    c = qsvm_res["classical"]
    print(f"  {'QSVM':<12} {'Quantum SVM':<22} "
          f"{q['metrics']['accuracy']:<10.4f} {q['runtime']:<12.4f} "
          f"{q['energy'][0]:.0f}-{q['energy'][1]:.0f}")
    print(f"  {'':<12} {'Classical SVM':<22} "
          f"{c['metrics']['accuracy']:<10.4f} {c['runtime']:<12.4f} "
          f"{c['energy'][0]:.0f}-{c['energy'][1]:.0f}")

    # QAOA
    q = qaoa_res["quantum"]
    c = qaoa_res["classical"]
    print(f"  {'QAOA':<12} {'QAOA Quantum':<22} "
          f"{q['cut']:<10.2f} {q['runtime']:<12.4f} "
          f"{q['energy'][0]:.0f}-{q['energy'][1]:.0f}")
    print(f"  {'':<12} {'Greedy Classical':<22} "
          f"{c['cut']:<10.2f} {c['runtime']:<12.6f} "
          f"{c['energy'][0]:.4f}-{c['energy'][1]:.4f}")

    # Grover
    q = grover_res["quantum"]
    c = grover_res["classical"]
    print(f"  {'Grover':<12} {'Grover Quantum':<22} "
          f"{q['success_prob']:<10.4f} {q['runtime']:<12.4f} "
          f"{q['energy'][0]:.2f}-{q['energy'][1]:.2f}")
    print(f"  {'':<12} {'Brute-Force':<22} "
          f"{'1.0000':<10} {c['runtime']:<12.6f} "
          f"{c['energy'][0]:.4f}-{c['energy'][1]:.4f}")

    print("  " + "-" * 68)


def main() -> None:
    """Run the complete thesis demo pipeline."""
    print("\n" + "#" * 60)
    print("#")
    print("#  Hybrid Quantum-AI Models for Cybersecurity")
    print("#  on Cloud Platforms")
    print("#")
    print("#  Accuracy / Latency / Energy Trade-offs")
    print("#  Thesis Demo — Full Experiment Pipeline")
    print("#")
    print("#" * 60)

    # Clean previous results
    clear_results()
    os.makedirs(config.PLOTS_DIR, exist_ok=True)

    total_start = time.perf_counter()

    # Run all three experiments
    qsvm_results = run_qsvm()
    qaoa_results = run_qaoa()
    grover_results = run_grover()

    total_elapsed = time.perf_counter() - total_start

    # Generate analysis plots and final tables
    print("\n" + "=" * 60)
    print("  GENERATING ANALYSIS PLOTS AND FINAL REPORT")
    print("=" * 60)
    generate_all_plots()
    generate_tables()

    # Print comparison table
    print_comparison_table(qsvm_results, qaoa_results, grover_results)

    # Final summary
    print("\n" + "#" * 60)
    print("#  ALL EXPERIMENTS COMPLETE")
    print(f"#  Total pipeline time: {total_elapsed:.2f} seconds")
    print("#" * 60)
    print(f"\n  Output files:")
    print(f"    Results CSV:      {config.RESULTS_CSV}")
    print(f"    Plots directory:  {config.PLOTS_DIR}")
    print(f"    Final table:      {config.FINAL_TABLE_CSV}")
    print(f"    Final summary:    {config.FINAL_SUMMARY_TXT}")
    print()


if __name__ == "__main__":
    main()
