"""Pre-compute simulation data for all 7 CPU/GPU/QPU combinations.

Generates a JSON file with results for every possible mix:
  CPU only, GPU only, QPU only, CPU+GPU, CPU+QPU, GPU+QPU, CPU+GPU+QPU

This data powers the interactive web simulator.
"""

import os
import sys
import json
import time
import numpy as np

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from hybrid_simulation import cpu_engine, gpu_engine, qpu_engine


def run_all_combinations():
    """Run experiments for all 7 unit combinations and collect metrics."""

    print("Pre-computing simulation data for all CPU/GPU/QPU combinations...")
    print("=" * 60)

    # Shared data
    preprocess = cpu_engine.preprocess_anomaly_data()
    X_train = preprocess["X_train"]
    X_test = preprocess["X_test"]
    y_train = preprocess["y_train"]
    y_test = preprocess["y_test"]

    graph = cpu_engine.preprocess_graph_data()
    edges = graph["edges"]
    n_nodes = graph["n_nodes"]
    adjacency = graph["adjacency"]

    n_qubits = 4
    target = "0110"

    combos = {
        "CPU":         {"cpu": True,  "gpu": False, "qpu": False},
        "GPU":         {"cpu": False, "gpu": True,  "qpu": False},
        "QPU":         {"cpu": False, "gpu": False, "qpu": True},
        "CPU+GPU":     {"cpu": True,  "gpu": True,  "qpu": False},
        "CPU+QPU":     {"cpu": True,  "gpu": False, "qpu": True},
        "GPU+QPU":     {"cpu": False, "gpu": True,  "qpu": True},
        "CPU+GPU+QPU": {"cpu": True,  "gpu": True,  "qpu": True},
    }

    all_results = {}

    for combo_name, units in combos.items():
        print(f"\n  Running: {combo_name}")
        combo_result = {"units": units, "experiments": {}}
        total_runtime = 0
        total_energy = 0

        # ── QSVM ─────────────────────────────────────────────
        qsvm = {"steps": [], "accuracy": 0, "f1": 0, "runtime": 0, "energy": 0}

        if units["cpu"]:
            # CPU preprocessing
            t0 = time.perf_counter()
            _ = cpu_engine.preprocess_anomaly_data()
            rt = time.perf_counter() - t0
            qsvm["steps"].append({"unit": "CPU", "task": "Data Preprocessing", "runtime": rt, "energy": rt * 150 * 0.7 * 1.2})
            qsvm["runtime"] += rt
            qsvm["energy"] += rt * 150 * 0.7 * 1.2

            # CPU classical SVM
            res = cpu_engine.classical_svm(X_train, X_test, y_train, y_test)
            qsvm["steps"].append({"unit": "CPU", "task": "Classical SVM (RBF)", "runtime": res["runtime"], "energy": res["energy_j"]})
            qsvm["accuracy"] = res["accuracy"]
            qsvm["f1"] = res["f1_score"]
            qsvm["runtime"] += res["runtime"]
            qsvm["energy"] += res["energy_j"]

        if units["gpu"]:
            # GPU kernel matrix
            res = gpu_engine.compute_rbf_kernel_matrix(X_test, X_train)
            qsvm["steps"].append({"unit": "GPU", "task": "Parallel RBF Kernel", "runtime": res["runtime"], "energy": res["energy_j"]})
            qsvm["runtime"] += res["runtime"]
            qsvm["energy"] += res["energy_j"]

            # GPU feature extraction
            res = gpu_engine.neural_feature_extraction(X_train)
            qsvm["steps"].append({"unit": "GPU", "task": "Neural Feature Extraction", "runtime": res["runtime"], "energy": res["energy_j"]})
            qsvm["runtime"] += res["runtime"]
            qsvm["energy"] += res["energy_j"]

            if not units["cpu"] and not units["qpu"]:
                # GPU-only: use kernel classify
                k_train = gpu_engine.compute_rbf_kernel_matrix(X_test, X_train)
                cls = gpu_engine.batch_parallel_classify(k_train["kernel_matrix"], y_train, k_train["kernel_matrix"])
                from sklearn.metrics import accuracy_score, f1_score
                qsvm["accuracy"] = accuracy_score(y_test, cls["predictions"])
                qsvm["f1"] = f1_score(y_test, cls["predictions"], zero_division=0)
                qsvm["steps"].append({"unit": "GPU", "task": "Batch Classification", "runtime": cls["runtime"], "energy": cls["energy_j"]})
                qsvm["runtime"] += cls["runtime"]
                qsvm["energy"] += cls["energy_j"]

        if units["qpu"]:
            # QPU quantum kernel (subset)
            ss = min(15, len(X_train))
            ts = min(8, len(X_test))
            res = qpu_engine.compute_quantum_kernel_matrix(X_train[:ss], X_test[:ts])
            qsvm["steps"].append({"unit": "QPU", "task": f"Quantum Kernel ({res['n_circuits']} circuits)", "runtime": res["runtime"], "energy": res["energy_j"]})
            qsvm["runtime"] += res["runtime"]
            qsvm["energy"] += res["energy_j"]

            if not units["cpu"]:
                # QPU provides accuracy via kernel classify
                cls = gpu_engine.batch_parallel_classify(res["kernel_matrix"], y_train[:ss], res["kernel_matrix"])
                from sklearn.metrics import accuracy_score, f1_score
                qsvm["accuracy"] = accuracy_score(y_test[:ts], cls["predictions"][:ts])
                qsvm["f1"] = f1_score(y_test[:ts], cls["predictions"][:ts], zero_division=0)

        combo_result["experiments"]["qsvm"] = qsvm
        total_runtime += qsvm["runtime"]
        total_energy += qsvm["energy"]

        # ── QAOA ──────────────────────────────────────────────
        qaoa = {"steps": [], "cut_value": 0, "approx_ratio": 0, "optimal_cut": 0, "runtime": 0, "energy": 0}

        if units["cpu"]:
            res = cpu_engine.preprocess_graph_data()
            qaoa["steps"].append({"unit": "CPU", "task": "Graph Generation", "runtime": res["runtime"], "energy": res["energy_j"]})
            qaoa["runtime"] += res["runtime"]
            qaoa["energy"] += res["energy_j"]

            res = cpu_engine.classical_greedy_maxcut(edges, n_nodes)
            qaoa["steps"].append({"unit": "CPU", "task": "Greedy MaxCut", "runtime": res["runtime"], "energy": res["energy_j"]})
            qaoa["cut_value"] = res["cut_value"]
            qaoa["runtime"] += res["runtime"]
            qaoa["energy"] += res["energy_j"]

        if units["gpu"]:
            res = gpu_engine.compute_qaoa_cost_matrix(adjacency)
            qaoa["steps"].append({"unit": "GPU", "task": f"Cost Hamiltonian ({res['dimension']}x{res['dimension']})", "runtime": res["runtime"], "energy": res["energy_j"]})
            qaoa["runtime"] += res["runtime"]
            qaoa["energy"] += res["energy_j"]

        if units["qpu"]:
            res = qpu_engine.run_qaoa(edges, n_nodes, depth=2)
            qaoa["steps"].append({"unit": "QPU", "task": f"QAOA p=2 ({res['total_circuits']} circuits)", "runtime": res["runtime"], "energy": res["energy_j"]})
            qaoa["cut_value"] = res["best_cut"]
            qaoa["approx_ratio"] = res["approx_ratio"]
            qaoa["optimal_cut"] = res["optimal_cut"]
            qaoa["runtime"] += res["runtime"]
            qaoa["energy"] += res["energy_j"]
        elif units["cpu"]:
            # Compute optimal for reference
            optimal = 0
            for bits in range(2 ** n_nodes):
                bs = format(bits, f"0{n_nodes}b")
                cut = sum(1 for i, j in edges if bs[i] != bs[j])
                optimal = max(optimal, cut)
            qaoa["optimal_cut"] = optimal
            qaoa["approx_ratio"] = qaoa["cut_value"] / optimal if optimal > 0 else 0

        combo_result["experiments"]["qaoa"] = qaoa
        total_runtime += qaoa["runtime"]
        total_energy += qaoa["energy"]

        # ── Grover ────────────────────────────────────────────
        grover = {"steps": [], "success_prob": 0, "iterations": 0, "checks": 0, "runtime": 0, "energy": 0}

        if units["cpu"]:
            res = cpu_engine.classical_bruteforce_search(n_qubits, target)
            grover["steps"].append({"unit": "CPU", "task": "Brute-Force Search", "runtime": res["runtime"], "energy": res["energy_j"]})
            grover["checks"] = res["checks"]
            grover["success_prob"] = 1.0
            grover["runtime"] += res["runtime"]
            grover["energy"] += res["energy_j"]

        if units["gpu"]:
            res = gpu_engine.parallel_oracle_evaluation(n_qubits, target)
            grover["steps"].append({"unit": "GPU", "task": "Oracle Matrix Construction", "runtime": res["runtime"], "energy": res["energy_j"]})
            grover["runtime"] += res["runtime"]
            grover["energy"] += res["energy_j"]

        if units["qpu"]:
            res = qpu_engine.run_grover(n_qubits, target)
            grover["steps"].append({"unit": "QPU", "task": f"Grover ({res['optimal_iterations']} iterations)", "runtime": res["runtime"], "energy": res["energy_j"]})
            grover["success_prob"] = res["success_prob"]
            grover["iterations"] = res["optimal_iterations"]
            grover["runtime"] += res["runtime"]
            grover["energy"] += res["energy_j"]

        combo_result["experiments"]["grover"] = grover
        total_runtime += grover["runtime"]
        total_energy += grover["energy"]

        combo_result["total_runtime"] = total_runtime
        combo_result["total_energy"] = total_energy
        all_results[combo_name] = combo_result

        print(f"    Done: {total_runtime:.4f}s | {total_energy:.2f}J")

    return all_results


def main():
    results = run_all_combinations()

    output_path = os.path.join(PROJECT_DIR, "hybrid_simulation", "output",
                               "simulator_data.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  Simulator data saved to: {output_path}")
    return results


if __name__ == "__main__":
    main()
