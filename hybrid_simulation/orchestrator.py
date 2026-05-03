"""Hybrid Orchestrator — routes tasks to CPU, GPU, or QPU.

This is the brain of the hybrid architecture. It:
  1. Receives cybersecurity workloads (anomaly detection, optimization, search)
  2. Decomposes each workload into sub-tasks
  3. Routes each sub-task to the optimal processing unit
  4. Manages data flow between units (CPU -> GPU -> QPU -> CPU)
  5. Tracks timing, energy, and utilization per unit
  6. Aggregates final results

Pipeline for each experiment:
  QSVM:   CPU(preprocess) -> GPU(feature extract + kernel) -> QPU(quantum kernel) -> CPU(aggregate)
  QAOA:   CPU(graph gen)  -> GPU(cost matrix)              -> QPU(QAOA circuit)   -> CPU(aggregate)
  Grover: CPU(setup)      -> GPU(oracle matrix)            -> QPU(grover circuit)  -> CPU(aggregate)
"""

import time
import sys
import numpy as np
from typing import Dict, Any, List
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from . import cpu_engine
from . import gpu_engine
from . import qpu_engine
from . import vqe_workload
from .data_loader import load_kdd_data
from .cloud_costs import cost_per_task, all_tiers_cost


class HybridOrchestrator:
    """Routes cybersecurity workloads across CPU, GPU, and QPU."""

    def __init__(self, use_real_data: bool = True):
        self.pipeline_log: List[Dict[str, Any]] = []
        self.unit_totals = {"CPU": 0.0, "GPU": 0.0, "QPU": 0.0}
        self.energy_totals = {"CPU": 0.0, "GPU": 0.0, "QPU": 0.0}
        self.task_count = {"CPU": 0, "GPU": 0, "QPU": 0}
        self.start_time = None
        self.use_real_data = use_real_data
        self._iot_data = None

    def _load_data(self):
        """Load real KDD data once (cached for multi-run)."""
        if self._iot_data is None and self.use_real_data:
            print("  Loading KDD Cup 99 dataset...")
            self._iot_data = load_kdd_data()
            print(f"    Quantum subset: {self._iot_data['n_quantum']} samples, "
                  f"{self._iot_data['n_features_quantum']} PCA features")
            print(f"    Classical subset: {self._iot_data['n_classical']} samples, "
                  f"{self._iot_data['n_features_original']} features")
        return self._iot_data

    def _reset_counters(self):
        """Reset counters for a fresh run (used in multi-run)."""
        self.pipeline_log = []
        self.unit_totals = {"CPU": 0.0, "GPU": 0.0, "QPU": 0.0}
        self.energy_totals = {"CPU": 0.0, "GPU": 0.0, "QPU": 0.0}
        self.task_count = {"CPU": 0, "GPU": 0, "QPU": 0}

    def _log_step(self, step, result: dict, experiment: str):
        """Log a pipeline step with timing and energy."""
        unit = result.get("unit", "?")
        entry = {
            "experiment": experiment,
            "step": step,
            "task": result.get("task", ""),
            "unit": unit,
            "ops": result.get("ops", ""),
            "runtime": result.get("runtime", 0),
            "energy_j": result.get("energy_j", 0),
        }
        self.pipeline_log.append(entry)
        self.unit_totals[unit] += result.get("runtime", 0)
        self.energy_totals[unit] += result.get("energy_j", 0)
        self.task_count[unit] += 1

        print(f"    [{unit:>3}] Step {step}: {result.get('task', ''):<28} "
              f"{result.get('runtime', 0):.4f}s  | {result.get('ops', '')}")

    def _header(self, name: str):
        print(f"\n  {'=' * 60}")
        print(f"  > EXPERIMENT: {name}")
        print(f"  {'=' * 60}")

    # ===============================================================
    # EXPERIMENT 1: QSVM Anomaly Detection (Full Hybrid Pipeline)
    # ===============================================================

    def run_qsvm_pipeline(self) -> Dict[str, Any]:
        """Run the full hybrid QSVM pipeline with classical baselines.

        CPU -> GPU -> QPU -> GPU -> CPU
        Classical baselines: SVM, RF, GBM, KNN
        """
        self._header("QSVM ANOMALY DETECTION")
        results = {}
        iot_data = self._load_data()

        # Step 1: CPU - Data preprocessing
        print("  Phase 1: Data Pipeline (CPU)")
        step1 = cpu_engine.preprocess_anomaly_data(iot_data=iot_data)
        self._log_step(1, step1, "QSVM")
        results["preprocess"] = step1

        X_train = step1["X_train"]
        X_test = step1["X_test"]
        y_train = step1["y_train"]
        y_test = step1["y_test"]

        # Step 2: GPU - Neural feature extraction
        print("  Phase 2: Feature Extraction (GPU)")
        step2 = gpu_engine.neural_feature_extraction(X_train)
        self._log_step(2, step2, "QSVM")
        results["gpu_features"] = step2

        # Step 3: GPU - Classical kernel matrix
        step3 = gpu_engine.compute_rbf_kernel_matrix(X_test, X_train)
        self._log_step(3, step3, "QSVM")
        results["gpu_kernel"] = step3

        # Step 4: GPU - Batch classical SVM classification
        step4 = gpu_engine.batch_parallel_classify(
            step3["kernel_matrix"], y_train, step3["kernel_matrix"])
        self._log_step(4, step4, "QSVM")
        results["gpu_classify"] = step4

        # Step 5: CPU - Classical SVM baseline (on quantum-sized data)
        print("  Phase 3: Classical Baselines (CPU)")
        step5 = cpu_engine.classical_svm(X_train, X_test, y_train, y_test)
        self._log_step(5, step5, "QSVM")
        results["classical_svm"] = step5

        # Step 5b-d: Additional classical baselines (on larger data)
        if iot_data is not None:
            Xc_tr = iot_data["X_train_c"]
            Xc_te = iot_data["X_test_c"]
            yc_tr = iot_data["y_train_c"]
            yc_te = iot_data["y_test_c"]
        else:
            Xc_tr, Xc_te, yc_tr, yc_te = X_train, X_test, y_train, y_test

        step5b = cpu_engine.classical_random_forest(Xc_tr, Xc_te, yc_tr, yc_te)
        self._log_step("5b", step5b, "QSVM")
        results["classical_rf"] = step5b

        step5c = cpu_engine.classical_gradient_boosting(Xc_tr, Xc_te, yc_tr, yc_te)
        self._log_step("5c", step5c, "QSVM")
        results["classical_gbm"] = step5c

        step5d = cpu_engine.classical_knn(Xc_tr, Xc_te, yc_tr, yc_te)
        self._log_step("5d", step5d, "QSVM")
        results["classical_knn"] = step5d

        # Step 6: QPU - Quantum kernel evaluation (subset for speed)
        print("  Phase 4: Quantum Kernel (QPU)")
        subset_size = min(15, len(X_train))
        test_subset = min(8, len(X_test))
        step6 = qpu_engine.compute_quantum_kernel_matrix(
            X_train[:subset_size], X_test[:test_subset])
        self._log_step(6, step6, "QSVM")
        results["quantum_kernel"] = step6

        # Step 7: GPU - Classify using quantum kernel
        step7 = gpu_engine.batch_parallel_classify(
            step6["kernel_matrix"], y_train[:subset_size],
            step6["kernel_matrix"])
        self._log_step(7, step7, "QSVM")

        # Step 8: CPU - Aggregate results
        print("  Phase 5: Aggregation (CPU)")
        q_pred = step7["predictions"]
        q_acc  = accuracy_score(y_test[:test_subset], q_pred[:test_subset])
        q_f1   = f1_score(y_test[:test_subset], q_pred[:test_subset], zero_division=0)
        q_prec = precision_score(y_test[:test_subset], q_pred[:test_subset], zero_division=0)
        q_rec  = recall_score(y_test[:test_subset], q_pred[:test_subset], zero_division=0)

        results["comparison"] = {
            # Classical baselines
            "svm_accuracy": step5["accuracy"], "svm_f1": step5["f1_score"],
            "svm_precision": step5.get("precision", 0), "svm_recall": step5.get("recall", 0),
            "svm_runtime": step5["runtime"], "svm_energy": step5["energy_j"],
            "rf_accuracy": step5b["accuracy"], "rf_f1": step5b["f1_score"],
            "rf_precision": step5b["precision"], "rf_recall": step5b["recall"],
            "rf_runtime": step5b["runtime"], "rf_energy": step5b["energy_j"],
            "gbm_accuracy": step5c["accuracy"], "gbm_f1": step5c["f1_score"],
            "gbm_precision": step5c["precision"], "gbm_recall": step5c["recall"],
            "gbm_runtime": step5c["runtime"], "gbm_energy": step5c["energy_j"],
            "knn_accuracy": step5d["accuracy"], "knn_f1": step5d["f1_score"],
            "knn_precision": step5d["precision"], "knn_recall": step5d["recall"],
            "knn_runtime": step5d["runtime"], "knn_energy": step5d["energy_j"],
            # Quantum
            "quantum_accuracy": q_acc, "quantum_f1": q_f1,
            "quantum_precision": q_prec, "quantum_recall": q_rec,
            "quantum_runtime": step6["runtime"], "quantum_energy": step6["energy_j"],
            "qpu_kernel_shape": step6["shape"],
            "qpu_circuits": step6["n_circuits"],
        }

        agg = cpu_engine.aggregate_results(step5, step3, step6)
        self._log_step(8, {**agg, "task": "result_aggregation",
                           "unit": "CPU", "ops": "compare & report",
                           "runtime": agg["aggregation_runtime"],
                           "energy_j": agg["aggregation_energy_j"]}, "QSVM")

        return results

    # ===============================================================
    # EXPERIMENT 2: QAOA Network Optimization (Full Hybrid Pipeline)
    # ===============================================================

    def run_qaoa_pipeline(self) -> Dict[str, Any]:
        """Run the full hybrid QAOA pipeline.

        CPU -> GPU -> QPU -> CPU
        """
        self._header("QAOA NETWORK OPTIMIZATION")
        results = {}

        # Step 1: CPU - Graph generation
        print("  Phase 1: Graph Generation (CPU)")
        step1 = cpu_engine.preprocess_graph_data()
        self._log_step(1, step1, "QAOA")
        results["graph"] = step1

        edges = step1["edges"]
        n_nodes = step1["n_nodes"]
        adjacency = step1["adjacency"]

        # Step 2: GPU - Cost Hamiltonian matrix
        print("  Phase 2: Hamiltonian Construction (GPU)")
        step2 = gpu_engine.compute_qaoa_cost_matrix(adjacency)
        self._log_step(2, step2, "QAOA")
        results["hamiltonian"] = step2

        # Step 3: CPU - Classical greedy baseline
        print("  Phase 3: Classical Baseline (CPU)")
        step3 = cpu_engine.classical_greedy_maxcut(edges, n_nodes)
        self._log_step(3, step3, "QAOA")
        results["classical"] = step3

        # Step 4: QPU - QAOA circuit optimization
        print("  Phase 4: QAOA Optimization (QPU)")
        step4 = qpu_engine.run_qaoa(edges, n_nodes, depth=2)
        self._log_step(4, step4, "QAOA")
        results["quantum"] = step4

        # Step 5: CPU - Aggregate
        print("  Phase 5: Aggregation (CPU)")
        results["comparison"] = {
            "greedy_cut": step3["cut_value"],
            "qaoa_cut": step4["best_cut"],
            "optimal_cut": step4["optimal_cut"],
            "greedy_ratio": step3["cut_value"] / step4["optimal_cut"]
                            if step4["optimal_cut"] > 0 else 0,
            "qaoa_ratio": step4["approx_ratio"],
            "qaoa_circuits": step4["total_circuits"],
        }
        agg = cpu_engine.aggregate_results(step3, step2, step4)
        self._log_step(5, {**agg, "task": "result_aggregation",
                           "unit": "CPU", "ops": "compare & report",
                           "runtime": agg["aggregation_runtime"],
                           "energy_j": agg["aggregation_energy_j"]}, "QAOA")

        return results

    # ===============================================================
    # EXPERIMENT 3: Grover Search (Full Hybrid Pipeline)
    # ===============================================================

    def run_grover_pipeline(self) -> Dict[str, Any]:
        """Run the full hybrid Grover pipeline.

        CPU -> GPU -> QPU -> CPU
        """
        self._header("GROVER CRYPTOGRAPHIC SEARCH")
        results = {}

        n_qubits = 4
        target = "0110"

        # Step 1: CPU - Classical brute-force baseline
        print("  Phase 1: Classical Search (CPU)")
        step1 = cpu_engine.classical_bruteforce_search(n_qubits, target)
        self._log_step(1, step1, "Grover")
        results["classical"] = step1

        # Step 2: GPU - Oracle matrix construction
        print("  Phase 2: Oracle Construction (GPU)")
        step2 = gpu_engine.parallel_oracle_evaluation(n_qubits, target)
        self._log_step(2, step2, "Grover")
        results["oracle"] = step2

        # Step 3: QPU - Grover circuit execution
        print("  Phase 3: Grover Circuit (QPU)")
        step3 = qpu_engine.run_grover(n_qubits, target)
        self._log_step(3, step3, "Grover")
        results["quantum"] = step3

        # Step 4: CPU - Aggregate
        print("  Phase 4: Aggregation (CPU)")
        results["comparison"] = {
            "classical_checks": step1["checks"],
            "quantum_iterations": step3["optimal_iterations"],
            "quantum_success_prob": step3["success_prob"],
            "speedup_factor": step1["checks"] / step3["optimal_iterations"],
            "top_states": step3["top_states"],
        }
        agg = cpu_engine.aggregate_results(step1, step2, step3)
        self._log_step(4, {**agg, "task": "result_aggregation",
                           "unit": "CPU", "ops": "compare & report",
                           "runtime": agg["aggregation_runtime"],
                           "energy_j": agg["aggregation_energy_j"]}, "Grover")

        return results

    # ===============================================================
    # EXPERIMENT 4: VQE Molecular Simulation (NEW for v7)
    # Contrast workload: classical wins for tiny molecules,
    # but classical scales O(2^n) so quantum dominates large molecules.
    # ===============================================================

    def run_vqe_pipeline(self) -> Dict[str, Any]:
        """Run VQE for H2 ground state with classical exact diagonalization
        baseline. CPU -> QPU -> CPU."""
        self._header("VQE MOLECULAR SIMULATION (H2)")
        results = {}

        # Step 1: CPU - Classical exact diagonalization
        print("  Phase 1: Classical Baseline (CPU)")
        step1 = vqe_workload.classical_exact_diagonalization()
        self._log_step(1, step1, "VQE")
        results["classical"] = step1

        # Step 2: QPU - Variational Quantum Eigensolver
        print("  Phase 2: VQE Optimization (QPU)")
        step2 = vqe_workload.run_vqe_h2()
        self._log_step(2, step2, "VQE")
        results["quantum"] = step2

        # Step 3: CPU - Aggregate
        print("  Phase 3: Aggregation (CPU)")
        results["comparison"] = {
            "exact_energy_hartree":   step1["ground_state_energy"],
            "vqe_energy_hartree":     step2["ground_state_energy"],
            "exact_error_hartree":    step1["energy_error_hartree"],
            "vqe_error_hartree":      step2["energy_error_hartree"],
            "classical_runtime":      step1["runtime"],
            "classical_energy_j":     step1["energy_j"],
            "vqe_runtime":            step2["runtime"],
            "vqe_energy_j":           step2["energy_j"],
            "vqe_iterations":         step2["n_iterations"],
            "vqe_circuits":           step2["n_circuits"],
            "n_qubits":               step2["n_qubits"],
        }
        return results

    def run_multi_vqe(self, n_runs: int = 30) -> Dict[str, Any]:
        """Run VQE n_runs times, with random init each time."""
        metrics = {
            "vqe_energy":    [],
            "vqe_error":     [],
            "vqe_runtime":   [],
            "vqe_energy_j":  [],
            "vqe_iters":     [],
            "exact_energy":  [],
            "exact_runtime": [],
            "exact_energy_j": [],
        }
        for i in range(n_runs):
            print(f"\n  === VQE Multi-run {i+1}/{n_runs} ===")
            self._reset_counters()
            r = self.run_vqe_pipeline()
            c = r["comparison"]
            metrics["vqe_energy"].append(c["vqe_energy_hartree"])
            metrics["vqe_error"].append(c["vqe_error_hartree"])
            metrics["vqe_runtime"].append(c["vqe_runtime"])
            metrics["vqe_energy_j"].append(c["vqe_energy_j"])
            metrics["vqe_iters"].append(c["vqe_iterations"])
            metrics["exact_energy"].append(c["exact_energy_hartree"])
            metrics["exact_runtime"].append(c["classical_runtime"])
            metrics["exact_energy_j"].append(c["classical_energy_j"])
        for k in metrics:
            metrics[k] = np.array(metrics[k])
        return metrics

    # ===============================================================
    # FULL PIPELINE: Run all four experiments
    # ===============================================================

    def run_full_pipeline(self) -> Dict[str, Any]:
        """Run the complete hybrid CPU+GPU+QPU pipeline."""
        self.start_time = time.perf_counter()

        print("\n" + "=" * 64)
        print("  HYBRID CPU + GPU + QPU SIMULATION")
        print("  Cybersecurity Workload Pipeline")
        print("=" * 64)
        print(f"\n  Processing Units:")
        print(f"    CPU | Data pipeline, classical algorithms, control")
        print(f"    GPU | Parallel kernels, matrix ops, neural features")
        print(f"    QPU | Quantum circuits (ZZ kernel, QAOA, Grover)")
        print(f"    Orchestrator | Job routing, pipeline coordination")

        qsvm_results = self.run_qsvm_pipeline()
        qaoa_results = self.run_qaoa_pipeline()
        grover_results = self.run_grover_pipeline()
        vqe_results = self.run_vqe_pipeline()

        total_time = time.perf_counter() - self.start_time

        # Final summary
        print(f"\n{'=' * 64}")
        print(f"  HYBRID PIPELINE COMPLETE")
        print(f"{'=' * 64}")

        print(f"\n  Processing Unit Utilization Summary")
        print(f"  {'Unit':<8} {'Tasks':>6} {'Runtime(s)':>12} {'Energy(J)':>15}")
        print(f"  {'-'*45}")
        for unit in ["CPU", "GPU", "QPU"]:
            print(f"  {unit:<8} {self.task_count[unit]:>6} "
                  f"{self.unit_totals[unit]:>12.4f} "
                  f"{self.energy_totals[unit]:>15.2f}")
        total_tasks = sum(self.task_count.values())
        total_energy = sum(self.energy_totals.values())
        print(f"  {'-'*45}")
        print(f"  {'TOTAL':<8} {total_tasks:>6} "
              f"{total_time:>12.4f} {total_energy:>15.2f}")

        # Experiment results summary
        print(f"\n  Experiment Results")
        print(f"  {'-'*55}")

        qc = qsvm_results["comparison"]
        print(f"  QSVM  | SVM Acc: {qc['svm_accuracy']:.2%} | "
              f"RF F1: {qc['rf_f1']:.2%} | "
              f"QSVM Acc: {qc['quantum_accuracy']:.2%}")

        qc2 = qaoa_results["comparison"]
        print(f"  QAOA  | Greedy: {qc2['greedy_cut']} | "
              f"QAOA: {qc2['qaoa_cut']:.2f} | "
              f"Optimal: {qc2['optimal_cut']}")

        qc3 = grover_results["comparison"]
        print(f"  Grover| Checks: {qc3['classical_checks']} | "
              f"Iters: {qc3['quantum_iterations']} | "
              f"P={qc3['quantum_success_prob']:.2%}")

        qc4 = vqe_results["comparison"]
        print(f"  VQE   | Exact: {qc4['exact_energy_hartree']:.4f} Ha | "
              f"VQE: {qc4['vqe_energy_hartree']:.4f} Ha | "
              f"err: {qc4['vqe_error_hartree']:.4f} Ha")

        return {
            "qsvm": qsvm_results,
            "qaoa": qaoa_results,
            "grover": grover_results,
            "vqe":  vqe_results,
            "pipeline_log": self.pipeline_log,
            "unit_totals": self.unit_totals,
            "energy_totals": self.energy_totals,
            "task_count": self.task_count,
            "total_time": total_time,
        }

    # ===============================================================
    # MULTI-RUN: Statistical validation (30 runs)
    # ===============================================================

    def run_multi_qsvm(self, n_runs: int = 30) -> Dict[str, Any]:
        """Run QSVM pipeline n_runs times, collecting per-run metrics.

        Returns lists of per-run accuracy, F1, precision, recall, runtime,
        energy for both quantum and classical methods.
        """
        self._load_data()
        metrics = {
            "quantum":  {"accuracy": [], "f1": [], "precision": [], "recall": [],
                         "runtime": [], "energy": []},
            "svm":      {"accuracy": [], "f1": [], "precision": [], "recall": [],
                         "runtime": [], "energy": []},
            "rf":       {"accuracy": [], "f1": [], "precision": [], "recall": [],
                         "runtime": [], "energy": []},
            "gbm":      {"accuracy": [], "f1": [], "precision": [], "recall": [],
                         "runtime": [], "energy": []},
            "knn":      {"accuracy": [], "f1": [], "precision": [], "recall": [],
                         "runtime": [], "energy": []},
        }

        for i in range(n_runs):
            print(f"\n  === Multi-run {i+1}/{n_runs} ===")
            self._reset_counters()
            result = self.run_qsvm_pipeline()
            comp = result["comparison"]

            for method in ["svm", "rf", "gbm", "knn"]:
                for metric in ["accuracy", "f1", "precision", "recall"]:
                    key = f"{method}_{metric}"
                    metrics[method][metric].append(comp.get(key, 0))
                metrics[method]["runtime"].append(comp.get(f"{method}_runtime", 0))
                metrics[method]["energy"].append(comp.get(f"{method}_energy", 0))

            for metric in ["accuracy", "f1", "precision", "recall"]:
                metrics["quantum"][metric].append(comp.get(f"quantum_{metric}", 0))
            metrics["quantum"]["runtime"].append(comp.get("quantum_runtime", 0))
            metrics["quantum"]["energy"].append(comp.get("quantum_energy", 0))

        # Convert to numpy for stats
        for method in metrics:
            for metric in metrics[method]:
                metrics[method][metric] = np.array(metrics[method][metric])

        return metrics

    def run_multi_qaoa(self, n_runs: int = 30) -> Dict[str, Any]:
        """Run QAOA pipeline n_runs times for statistical validation."""
        metrics = {
            "qaoa_cut": [], "greedy_cut": [], "optimal_cut": [],
            "qaoa_ratio": [], "qaoa_runtime": [], "qaoa_energy": [],
        }
        for i in range(n_runs):
            print(f"\n  === QAOA Multi-run {i+1}/{n_runs} ===")
            self._reset_counters()
            result = self.run_qaoa_pipeline()
            comp = result["comparison"]
            metrics["qaoa_cut"].append(comp["qaoa_cut"])
            metrics["greedy_cut"].append(comp["greedy_cut"])
            metrics["optimal_cut"].append(comp["optimal_cut"])
            metrics["qaoa_ratio"].append(comp["qaoa_ratio"])
            metrics["qaoa_runtime"].append(result["quantum"]["runtime"])
            metrics["qaoa_energy"].append(result["quantum"]["energy_j"])

        for k in metrics:
            metrics[k] = np.array(metrics[k])
        return metrics
