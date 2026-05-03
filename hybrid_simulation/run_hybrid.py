"""Main entry point: Run the full hybrid CPU + GPU + QPU simulation.

Usage:
    python -m hybrid_simulation.run_hybrid

This executes:
  1. Single full pipeline run (QSVM + QAOA + Grover) with classical baselines
  2. Multi-run statistical validation (30x QSVM, 30x QAOA)
  3. Generates publication-quality plots including comparison charts

Dataset: KDD Cup 99 (real network intrusion data)
"""

import os
import sys
import json
import csv
import numpy as np
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from hybrid_simulation.orchestrator import HybridOrchestrator
from hybrid_simulation.visualize import generate_all_plots
from hybrid_simulation.cloud_costs import all_tiers_cost, cost_per_task
from hybrid_simulation.allocation_rule import (
    pareto_optimal, allocate_tier,
    CLASSICAL_ML, MOLECULAR_SIM, COMBINATORIAL,
)


N_MULTI_RUNS = 30   # Statistical validation runs


def save_results_csv(results: dict, output_dir: str):
    """Save pipeline results to CSV for analysis."""
    csv_path = os.path.join(output_dir, "hybrid_pipeline_results.csv")
    fieldnames = ["experiment", "step", "task", "unit", "ops",
                  "runtime_s", "energy_j"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for entry in results["pipeline_log"]:
            writer.writerow({
                "experiment": entry["experiment"],
                "step": entry["step"],
                "task": entry["task"],
                "unit": entry["unit"],
                "ops": entry["ops"],
                "runtime_s": f"{entry['runtime']:.6f}",
                "energy_j": f"{entry['energy_j']:.4f}",
            })
    print(f"  Pipeline CSV: {csv_path}")


def save_comparison_csv(results: dict, output_dir: str):
    """Save classifier comparison table to CSV."""
    csv_path = os.path.join(output_dir, "classifier_comparison.csv")
    comp = results["qsvm"]["comparison"]

    methods = [
        ("Classical SVM (RBF)", "svm"),
        ("Random Forest", "rf"),
        ("Gradient Boosting", "gbm"),
        ("KNN (k=5)", "knn"),
        ("QSVM (ZZ kernel)", "quantum"),
    ]

    fieldnames = ["Method", "Tier", "Accuracy", "Precision", "Recall",
                  "F1", "Runtime_s", "Energy_J"]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for name, key in methods:
            tier = "QPU" if key == "quantum" else "CPU"
            writer.writerow({
                "Method": name,
                "Tier": tier,
                "Accuracy":  f"{comp.get(f'{key}_accuracy', 0):.4f}",
                "Precision": f"{comp.get(f'{key}_precision', 0):.4f}",
                "Recall":    f"{comp.get(f'{key}_recall', 0):.4f}",
                "F1":        f"{comp.get(f'{key}_f1', 0):.4f}",
                "Runtime_s": f"{comp.get(f'{key}_runtime', 0):.6f}",
                "Energy_J":  f"{comp.get(f'{key}_energy', 0):.4f}",
            })
    print(f"  Comparison:   {csv_path}")


def save_multirun_csv(qsvm_multi: dict, qaoa_multi: dict, output_dir: str):
    """Save multi-run statistical results."""
    csv_path = os.path.join(output_dir, "multirun_stats.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Method", "Metric", "Mean", "Std", "Min", "Max",
                         "N_runs"])
        for method in ["quantum", "svm", "rf", "gbm", "knn"]:
            for metric in ["accuracy", "f1", "precision", "recall",
                           "runtime", "energy"]:
                vals = qsvm_multi[method][metric]
                writer.writerow([
                    method, metric,
                    f"{np.mean(vals):.6f}", f"{np.std(vals):.6f}",
                    f"{np.min(vals):.6f}", f"{np.max(vals):.6f}",
                    len(vals),
                ])
        # QAOA stats
        for metric in ["qaoa_cut", "qaoa_ratio", "qaoa_runtime", "qaoa_energy"]:
            vals = qaoa_multi[metric]
            writer.writerow([
                "QAOA", metric,
                f"{np.mean(vals):.6f}", f"{np.std(vals):.6f}",
                f"{np.min(vals):.6f}", f"{np.max(vals):.6f}",
                len(vals),
            ])
    print(f"  Multi-run:    {csv_path}")


def save_vqe_csv(vqe_multi: dict, output_dir: str):
    """Save VQE per-run statistics."""
    csv_path = os.path.join(output_dir, "vqe_multirun.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["run", "vqe_energy_hartree", "vqe_error_hartree",
                         "vqe_runtime_s", "vqe_energy_j", "vqe_iterations",
                         "exact_energy_hartree", "exact_runtime_s", "exact_energy_j"])
        for i in range(len(vqe_multi["vqe_energy"])):
            writer.writerow([i + 1,
                f"{vqe_multi['vqe_energy'][i]:.6f}",
                f"{vqe_multi['vqe_error'][i]:.6f}",
                f"{vqe_multi['vqe_runtime'][i]:.4f}",
                f"{vqe_multi['vqe_energy_j'][i]:.4f}",
                int(vqe_multi['vqe_iters'][i]),
                f"{vqe_multi['exact_energy'][i]:.6f}",
                f"{vqe_multi['exact_runtime'][i]:.6f}",
                f"{vqe_multi['exact_energy_j'][i]:.6f}",
            ])
    print(f"  VQE CSV:      {csv_path}")


def save_cloud_costs_csv(cloud: dict, qsvm_multi: dict, vqe_multi: dict,
                         output_dir: str):
    """Save cloud cost comparison across both workloads."""
    csv_path = os.path.join(output_dir, "cloud_costs.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["workload", "tier", "service", "runtime_s",
                         "cost_per_task_usd", "cost_per_million_usd"])
        # Cybersecurity (QSVM)
        for tier, c in cloud.items():
            writer.writerow(["Cybersecurity", tier, c["service"],
                             f"{c['runtime_s']:.6f}",
                             f"{c['cost_per_task_usd']:.6f}",
                             f"{c['cost_per_million_usd']:.2f}"])
        # Molecular simulation (VQE)
        from .cloud_costs import all_tiers_cost
        vqe_runtimes = {
            "CPU": float(np.mean(vqe_multi["exact_runtime"])),
            "GPU": 0.001,
            "QPU": float(np.mean(vqe_multi["vqe_runtime"])),
        }
        vqe_cloud = all_tiers_cost(vqe_runtimes, shots=4000)
        for tier, c in vqe_cloud.items():
            writer.writerow(["MolecularSim", tier, c["service"],
                             f"{c['runtime_s']:.6f}",
                             f"{c['cost_per_task_usd']:.6f}",
                             f"{c['cost_per_million_usd']:.2f}"])
    print(f"  Cloud costs:  {csv_path}")


def save_summary(results: dict, qsvm_multi: dict, qaoa_multi: dict,
                 output_dir: str, vqe_multi: dict = None):
    """Save a human-readable summary."""
    path = os.path.join(output_dir, "hybrid_summary.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("  HERO: Hybrid CPU + GPU + QPU Simulation - SUMMARY\n")
        f.write(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"  Dataset: KDD Cup 99 (10% subset)\n")
        f.write(f"  Multi-run: {N_MULTI_RUNS} iterations for statistical validation\n")
        f.write("=" * 70 + "\n\n")

        # Single run summary
        f.write("PROCESSING UNIT UTILIZATION (single run)\n")
        f.write("-" * 50 + "\n")
        for unit in ["CPU", "GPU", "QPU"]:
            f.write(f"  {unit}:  {results['task_count'][unit]} tasks | "
                    f"{results['unit_totals'][unit]:.4f}s | "
                    f"{results['energy_totals'][unit]:.2f} J\n")
        f.write(f"\n  Total pipeline time: {results['total_time']:.2f}s\n")
        f.write(f"  Total energy: {sum(results['energy_totals'].values()):.2f} J\n\n")

        # Classifier comparison
        f.write("CLASSIFIER COMPARISON (single run)\n")
        f.write("-" * 70 + "\n")
        f.write(f"  {'Method':<25} {'Acc':>7} {'F1':>7} {'Prec':>7} "
                f"{'Rec':>7} {'Time(s)':>10} {'Energy(J)':>10}\n")
        f.write(f"  {'-'*68}\n")
        comp = results["qsvm"]["comparison"]
        for name, key in [("SVM (RBF)", "svm"), ("Random Forest", "rf"),
                          ("Grad. Boosting", "gbm"), ("KNN (k=5)", "knn"),
                          ("QSVM (ZZ)", "quantum")]:
            f.write(f"  {name:<25} "
                    f"{comp.get(f'{key}_accuracy',0):>7.4f} "
                    f"{comp.get(f'{key}_f1',0):>7.4f} "
                    f"{comp.get(f'{key}_precision',0):>7.4f} "
                    f"{comp.get(f'{key}_recall',0):>7.4f} "
                    f"{comp.get(f'{key}_runtime',0):>10.4f} "
                    f"{comp.get(f'{key}_energy',0):>10.4f}\n")

        # Multi-run stats
        f.write(f"\n\nMULTI-RUN STATISTICS ({N_MULTI_RUNS} runs)\n")
        f.write("-" * 70 + "\n")
        f.write(f"  {'Method':<12} {'Metric':<12} {'Mean':>10} {'Std':>10}\n")
        f.write(f"  {'-'*46}\n")
        for method in ["quantum", "svm", "rf", "gbm", "knn"]:
            for metric in ["f1", "accuracy"]:
                vals = qsvm_multi[method][metric]
                f.write(f"  {method:<12} {metric:<12} "
                        f"{np.mean(vals):>10.4f} {np.std(vals):>10.4f}\n")

        f.write(f"\n  QAOA approximation ratio: "
                f"{np.mean(qaoa_multi['qaoa_ratio']):.4f} +/- "
                f"{np.std(qaoa_multi['qaoa_ratio']):.4f}\n")

        if vqe_multi is not None:
            f.write(f"\n\nMOLECULAR SIMULATION (H2, VQE) — {len(vqe_multi['vqe_energy'])} runs\n")
            f.write("-" * 70 + "\n")
            f.write(f"  Exact ground state:     "
                    f"{np.mean(vqe_multi['exact_energy']):.6f} Hartree\n")
            f.write(f"  VQE estimate:           "
                    f"{np.mean(vqe_multi['vqe_energy']):.6f} +/- "
                    f"{np.std(vqe_multi['vqe_energy']):.6f} Hartree\n")
            f.write(f"  VQE error vs exact:     "
                    f"{np.mean(vqe_multi['vqe_error']):.6f} +/- "
                    f"{np.std(vqe_multi['vqe_error']):.6f} Hartree\n")
            f.write(f"  Classical runtime:      "
                    f"{np.mean(vqe_multi['exact_runtime'])*1000:.4f} ms\n")
            f.write(f"  VQE runtime:            "
                    f"{np.mean(vqe_multi['vqe_runtime']):.4f} +/- "
                    f"{np.std(vqe_multi['vqe_runtime']):.4f} s\n")
            f.write(f"  Classical energy:       "
                    f"{np.mean(vqe_multi['exact_energy_j']):.6f} J\n")
            f.write(f"  VQE energy:             "
                    f"{np.mean(vqe_multi['vqe_energy_j']):.2f} +/- "
                    f"{np.std(vqe_multi['vqe_energy_j']):.2f} J\n")
            ratio = np.mean(vqe_multi['vqe_energy_j']) / max(
                np.mean(vqe_multi['exact_energy_j']), 1e-12)
            f.write(f"  Quantum / Classical:    {ratio:,.0f} x more energy\n")

        f.write("\n" + "=" * 70 + "\n")
    print(f"  Summary:      {path}")


def main():
    """Run the complete hybrid simulation with multi-run validation."""
    output_dir = os.path.join(PROJECT_DIR, "hybrid_simulation", "output")
    plots_dir = os.path.join(output_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    # ---- 1. Single full pipeline run ----
    print("\n" + "=" * 64)
    print("  PHASE 1: SINGLE FULL PIPELINE RUN")
    print("=" * 64)

    orchestrator = HybridOrchestrator(use_real_data=True)
    results = orchestrator.run_full_pipeline()

    # ---- 2. Multi-run QSVM (30x) ----
    print("\n" + "=" * 64)
    print(f"  PHASE 2: MULTI-RUN QSVM ({N_MULTI_RUNS}x)")
    print("=" * 64)

    qsvm_multi = orchestrator.run_multi_qsvm(n_runs=N_MULTI_RUNS)

    # Print summary stats
    print(f"\n  QSVM Multi-Run Summary ({N_MULTI_RUNS} runs):")
    print(f"  {'Method':<12} {'F1 Mean':>10} {'F1 Std':>10}")
    print(f"  {'-'*34}")
    for method in ["quantum", "svm", "rf", "gbm", "knn"]:
        f1_vals = qsvm_multi[method]["f1"]
        print(f"  {method:<12} {np.mean(f1_vals):>10.4f} {np.std(f1_vals):>10.4f}")

    # ---- 3. Multi-run QAOA (30x) ----
    print("\n" + "=" * 64)
    print(f"  PHASE 3: MULTI-RUN QAOA ({N_MULTI_RUNS}x)")
    print("=" * 64)

    qaoa_multi = orchestrator.run_multi_qaoa(n_runs=N_MULTI_RUNS)
    print(f"\n  QAOA Approx Ratio: {np.mean(qaoa_multi['qaoa_ratio']):.4f} "
          f"+/- {np.std(qaoa_multi['qaoa_ratio']):.4f}")

    # ---- 3b. Multi-run VQE (30x) — molecular simulation workload ----
    print("\n" + "=" * 64)
    print(f"  PHASE 3b: MULTI-RUN VQE H2 ({N_MULTI_RUNS}x)")
    print("=" * 64)

    vqe_multi = orchestrator.run_multi_vqe(n_runs=N_MULTI_RUNS)
    print(f"\n  VQE energy error vs exact: "
          f"{np.mean(vqe_multi['vqe_error']):.4f} +/- "
          f"{np.std(vqe_multi['vqe_error']):.4f} Hartree")

    # ---- 3c. Cloud cost analysis ----
    print("\n" + "=" * 64)
    print("  PHASE 3c: CLOUD COST ANALYSIS")
    print("=" * 64)
    qsvm_runtimes = {
        "CPU": float(np.mean(qsvm_multi["svm"]["runtime"])),
        "GPU": 0.001,
        "QPU": float(np.mean(qsvm_multi["quantum"]["runtime"])),
    }
    cloud = all_tiers_cost(qsvm_runtimes, shots=2000)
    print("\n  Cybersecurity workload — cloud cost per 1M classifications:")
    for tier, c in cloud.items():
        print(f"    {tier:<5} ({c['service'][:35]:<35}): ${c['cost_per_million_usd']:>14,.2f}")

    # ---- 4. Generate plots ----
    print(f"\n{'=' * 64}")
    print(f"  GENERATING VISUALIZATION PLOTS")
    print(f"{'=' * 64}")

    generate_all_plots(results, plots_dir,
                       qsvm_multi=qsvm_multi, qaoa_multi=qaoa_multi,
                       vqe_multi=vqe_multi, cloud_costs=cloud)

    # ---- 5. Save results ----
    print(f"\n  Output files:")
    save_results_csv(results, output_dir)
    save_comparison_csv(results, output_dir)
    save_multirun_csv(qsvm_multi, qaoa_multi, output_dir)
    save_vqe_csv(vqe_multi, output_dir)
    save_cloud_costs_csv(cloud, qsvm_multi, vqe_multi, output_dir)
    save_summary(results, qsvm_multi, qaoa_multi, output_dir, vqe_multi=vqe_multi)
    print(f"  Plots:        {plots_dir}")

    # Copy to website images
    website_images = os.path.join(PROJECT_DIR, "website", "images")
    if os.path.exists(website_images):
        import shutil
        for fname in os.listdir(plots_dir):
            if fname.endswith(".png"):
                shutil.copy2(os.path.join(plots_dir, fname),
                             os.path.join(website_images, fname))
        print(f"  Copied plots to website/images/")

    print(f"\n  {'=' * 60}")
    print(f"  HERO SIMULATION COMPLETE")
    print(f"  {'=' * 60}\n")


if __name__ == "__main__":
    main()
