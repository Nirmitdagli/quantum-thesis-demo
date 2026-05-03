"""CPU Engine — handles data preprocessing, classical algorithms, and control logic.

In the hybrid architecture, the CPU is responsible for:
  1. Data ingestion and preprocessing (feature engineering, scaling)
  2. Classical baseline algorithms (SVM, RF, GradientBoosting, KNN)
  3. Control plane operations (orchestration overhead, result aggregation)
  4. I/O operations (logging, CSV writes, plot generation triggers)
"""

import time
import numpy as np
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (accuracy_score, f1_score,
                              precision_score, recall_score)
from typing import Dict, Any, Tuple


# ── Power model for CPU ──────────────────────────────────────
CPU_TDP_WATTS = 150          # Typical server CPU (Xeon / EPYC)
CPU_UTILIZATION = 0.70       # Average utilization during workload
CPU_PUE = 1.2                # Power Usage Effectiveness


def _cpu_energy(runtime: float) -> float:
    """Estimate CPU energy in joules."""
    return runtime * CPU_TDP_WATTS * CPU_UTILIZATION * CPU_PUE


# ═══════════════════════════════════════════════════════════════
# TASK 1: Data Preprocessing Pipeline
# ═══════════════════════════════════════════════════════════════

def preprocess_anomaly_data(n_samples: int = 120, n_features: int = 4,
                            random_state: int = 42,
                            iot_data: dict = None) -> Dict[str, Any]:
    """CPU: Load and preprocess cybersecurity anomaly data.

    If *iot_data* is provided (from data_loader.load_kdd_data), uses real
    KDD Cup 99 network intrusion data.  Otherwise falls back to synthetic
    data for backward-compatibility.
    """
    t0 = time.perf_counter()

    if iot_data is not None:
        # Real data path — pre-split and scaled by data_loader
        X_train = iot_data["X_train_q"]
        X_test  = iot_data["X_test_q"]
        y_train = iot_data["y_train_q"]
        y_test  = iot_data["y_test_q"]
        n_samples  = len(X_train) + len(X_test)
        n_features = X_train.shape[1]
        src = f"KDD Cup 99 (PCA-{n_features}, [0,pi])"
    else:
        # Synthetic fallback (backward-compatible)
        rng = np.random.RandomState(random_state)
        n_normal  = n_samples // 2
        n_anomaly = n_samples - n_normal
        X_normal  = rng.normal(loc=0.2, scale=0.1, size=(n_normal, n_features))
        X_anomaly = rng.normal(loc=0.8, scale=0.1, size=(n_anomaly, n_features))
        X_raw = np.vstack([X_normal, X_anomaly])
        y = np.array([0] * n_normal + [1] * n_anomaly)
        scaler = MinMaxScaler(feature_range=(0, np.pi))
        X_scaled = scaler.fit_transform(X_raw)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.33, random_state=random_state, stratify=y)
        src = "synthetic"

    runtime = time.perf_counter() - t0

    return {
        "task": "data_preprocessing",
        "unit": "CPU",
        "X_train": X_train, "X_test": X_test,
        "y_train": y_train, "y_test": y_test,
        "n_samples": n_samples, "n_features": n_features,
        "runtime": runtime,
        "energy_j": _cpu_energy(runtime),
        "ops": f"ingestion -> scaling -> split ({src})",
    }


def preprocess_graph_data(n_nodes: int = 7, edge_prob: float = 0.35,
                          random_state: int = 42) -> Dict[str, Any]:
    """CPU: Generate random graph for network segmentation optimization."""
    t0 = time.perf_counter()

    rng = np.random.RandomState(random_state)
    edges = []
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if rng.random() < edge_prob:
                edges.append((i, j))

    # Compute adjacency matrix (CPU linear algebra)
    adj = np.zeros((n_nodes, n_nodes))
    for i, j in edges:
        adj[i][j] = 1
        adj[j][i] = 1

    runtime = time.perf_counter() - t0

    return {
        "task": "graph_preprocessing",
        "unit": "CPU",
        "n_nodes": n_nodes, "n_edges": len(edges),
        "edges": edges, "adjacency": adj,
        "runtime": runtime,
        "energy_j": _cpu_energy(runtime),
        "ops": "graph generation -> adjacency matrix",
    }


# ═══════════════════════════════════════════════════════════════
# TASK 2: Classical Baseline Algorithms
# ═══════════════════════════════════════════════════════════════

def classical_svm(X_train, X_test, y_train, y_test) -> Dict[str, Any]:
    """CPU: Train and evaluate classical SVM with RBF kernel."""
    t0 = time.perf_counter()

    clf = SVC(kernel="rbf", gamma="scale")
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    metrics = _all_metrics(y_test, y_pred)

    runtime = time.perf_counter() - t0

    return {
        "task": "classical_svm",
        "unit": "CPU",
        **metrics,
        "predictions": y_pred,
        "runtime": runtime,
        "energy_j": _cpu_energy(runtime),
        "ops": "RBF kernel -> SVM fit -> predict",
    }


def _all_metrics(y_true, y_pred):
    """Compute accuracy, precision, recall, F1 in one call."""
    return {
        "accuracy":  accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall":    recall_score(y_true, y_pred, zero_division=0),
        "f1_score":  f1_score(y_true, y_pred, zero_division=0),
    }


def classical_random_forest(X_train, X_test, y_train, y_test,
                            random_state: int = 42) -> Dict[str, Any]:
    """CPU: Train and evaluate Random Forest classifier."""
    t0 = time.perf_counter()
    clf = RandomForestClassifier(n_estimators=100, random_state=random_state)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    metrics = _all_metrics(y_test, y_pred)
    runtime = time.perf_counter() - t0
    return {
        "task": "random_forest", "unit": "CPU",
        **metrics, "predictions": y_pred,
        "runtime": runtime, "energy_j": _cpu_energy(runtime),
        "ops": "RF(100 trees) fit -> predict",
    }


def classical_gradient_boosting(X_train, X_test, y_train, y_test,
                                random_state: int = 42) -> Dict[str, Any]:
    """CPU: Train and evaluate Gradient Boosting classifier (XGBoost-like)."""
    t0 = time.perf_counter()
    clf = GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                     random_state=random_state)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    metrics = _all_metrics(y_test, y_pred)
    runtime = time.perf_counter() - t0
    return {
        "task": "gradient_boosting", "unit": "CPU",
        **metrics, "predictions": y_pred,
        "runtime": runtime, "energy_j": _cpu_energy(runtime),
        "ops": "GBM(100 trees, d=3) fit -> predict",
    }


def classical_knn(X_train, X_test, y_train, y_test,
                  k: int = 5) -> Dict[str, Any]:
    """CPU: Train and evaluate K-Nearest Neighbors classifier."""
    t0 = time.perf_counter()
    clf = KNeighborsClassifier(n_neighbors=k)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    metrics = _all_metrics(y_test, y_pred)
    runtime = time.perf_counter() - t0
    return {
        "task": "knn_classifier", "unit": "CPU",
        **metrics, "predictions": y_pred,
        "runtime": runtime, "energy_j": _cpu_energy(runtime),
        "ops": f"KNN(k={k}) fit -> predict",
    }


def classical_greedy_maxcut(edges, n_nodes: int) -> Dict[str, Any]:
    """CPU: Greedy MaxCut heuristic for network segmentation."""
    t0 = time.perf_counter()

    partition = [0] * n_nodes
    for node in range(n_nodes):
        cut_0, cut_1 = 0, 0
        for i, j in edges:
            if i == node:
                other = j
            elif j == node:
                other = i
            else:
                continue
            if partition[other] == 0:
                cut_1 += 1
            else:
                cut_0 += 1
        partition[node] = 0 if cut_0 >= cut_1 else 1

    cut_value = sum(1 for i, j in edges if partition[i] != partition[j])

    runtime = time.perf_counter() - t0

    return {
        "task": "greedy_maxcut",
        "unit": "CPU",
        "cut_value": cut_value, "partition": partition,
        "runtime": runtime,
        "energy_j": _cpu_energy(runtime),
        "ops": "greedy node assignment -> cut evaluation",
    }


def classical_bruteforce_search(n_qubits: int = 4, target: str = "0110") -> Dict[str, Any]:
    """CPU: Brute-force search through all possible states."""
    t0 = time.perf_counter()

    search_space = 2 ** n_qubits
    found = False
    checks = 0
    for i in range(search_space):
        checks += 1
        candidate = format(i, f"0{n_qubits}b")
        if candidate == target:
            found = True
            break

    runtime = time.perf_counter() - t0

    return {
        "task": "bruteforce_search",
        "unit": "CPU",
        "found": found, "checks": checks, "search_space": search_space,
        "runtime": runtime,
        "energy_j": _cpu_energy(runtime),
        "ops": f"linear scan {search_space} states",
    }


# ═══════════════════════════════════════════════════════════════
# TASK 3: Control Plane / Result Aggregation
# ═══════════════════════════════════════════════════════════════

def aggregate_results(cpu_results: dict, gpu_results: dict,
                      qpu_results: dict) -> Dict[str, Any]:
    """CPU: Aggregate and compare results from all three units."""
    t0 = time.perf_counter()

    summary = {
        "cpu": {k: v for k, v in cpu_results.items() if k != "predictions"},
        "gpu": {k: v for k, v in gpu_results.items()
                if not isinstance(v, np.ndarray)},
        "qpu": {k: v for k, v in qpu_results.items()
                if not isinstance(v, np.ndarray)},
    }

    total_energy = (cpu_results.get("energy_j", 0) +
                    gpu_results.get("energy_j", 0) +
                    qpu_results.get("energy_j", 0))
    total_runtime = (cpu_results.get("runtime", 0) +
                     gpu_results.get("runtime", 0) +
                     qpu_results.get("runtime", 0))

    runtime = time.perf_counter() - t0

    return {
        "task": "result_aggregation",
        "unit": "CPU",
        "summary": summary,
        "total_energy_j": total_energy + _cpu_energy(runtime),
        "total_runtime": total_runtime + runtime,
        "aggregation_runtime": runtime,
        "aggregation_energy_j": _cpu_energy(runtime),
    }
