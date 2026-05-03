"""HERO Workload-Aware Tier Allocation + Pareto Selection.

Implements the decision logic described in Algorithm 1 of the paper.
The thresholds are calibrated from the measurements we report in
Section VII (Results) and the scaling theory in Section VIII.
"""

import numpy as np
from typing import List, Dict, Any


# Workload categories
MOLECULAR_SIM = "molecular_simulation"
CLASSICAL_ML  = "classical_ml"
COMBINATORIAL = "combinatorial_optimization"

# Thresholds (justified in paper)
N_CLASSICAL_QUBIT_WALL = 30   # classical state-vector RAM wall (~16 GB)
D_LOW  = 100                   # CPU dominates below this feature dim
D_HIGH = 10_000                # GPU sweet spot ends here
N_GREEDY_OK = 50               # combinatorial classical ok below this size


def allocate_tier(workload_type: str, problem_size: int = 0,
                  feature_dim: int = 0) -> str:
    """Decide which tier to send the workload to.

    Returns one of: "CPU", "GPU", "QPU", "MEASURE_WITH_HERO".

    Implements the allocation rule from Algorithm 1, Step 1.
    """
    if workload_type == MOLECULAR_SIM:
        return "QPU" if problem_size > N_CLASSICAL_QUBIT_WALL else "CPU"

    if workload_type == CLASSICAL_ML:
        if feature_dim < D_LOW:
            return "CPU"
        if feature_dim < D_HIGH:
            return "GPU"
        return "MEASURE_WITH_HERO"

    if workload_type == COMBINATORIAL:
        return "CPU" if problem_size < N_GREEDY_OK else "QPU"

    return "MEASURE_WITH_HERO"


def is_dominated(method, candidates):
    """True iff some other candidate dominates *method* on
    (cost, energy, latency, -accuracy).

    Domination = no worse on any axis, strictly better on at least one.
    Lower is better for cost / energy / latency; higher is better for accuracy.
    """
    for other in candidates:
        if other is method:
            continue
        not_worse = (other["cost"]    <= method["cost"]
                 and other["energy"]  <= method["energy"]
                 and other["latency"] <= method["latency"]
                 and other.get("accuracy", 0) >= method.get("accuracy", 0))
        strictly_better = (other["cost"]    <  method["cost"]
                       or  other["energy"]  <  method["energy"]
                       or  other["latency"] <  method["latency"]
                       or  other.get("accuracy", 0) > method.get("accuracy", 0))
        if not_worse and strictly_better:
            return True
    return False


def pareto_optimal(methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return Pareto-optimal subset on (cost, energy, latency).

    Implements Algorithm 1, Step 4.
    Each *method* must have keys: name, cost, energy, latency.
    """
    return [m for m in methods if not is_dominated(m, methods)]


def best_by_weights(methods: List[Dict[str, Any]],
                    alpha: float = 1.0,
                    beta: float = 1.0,
                    gamma: float = 1.0,
                    delta: float = 0.0) -> Dict[str, Any]:
    """Select the recommended method given user weights (Algorithm 1, Step 5).

    Score = alpha*cost + beta*energy + gamma*latency - delta*accuracy
    Lower score is better. Operates over Pareto-optimal set only.
    """
    P = pareto_optimal(methods)
    # Normalize per-axis to [0,1] so weights are interpretable
    def col(k): return np.array([m[k] for m in P], dtype=float)
    cost_n = (col("cost")    - col("cost").min())    / (np.ptp(col("cost"))    + 1e-12)
    en_n   = (col("energy")  - col("energy").min())  / (np.ptp(col("energy"))  + 1e-12)
    lat_n  = (col("latency") - col("latency").min()) / (np.ptp(col("latency")) + 1e-12)
    acc    = col("accuracy") if "accuracy" in P[0] else np.zeros(len(P))
    score  = alpha*cost_n + beta*en_n + gamma*lat_n - delta*acc
    return P[int(np.argmin(score))]


if __name__ == "__main__":
    # Demo: allocation
    print("=== Allocation Rule Demo ===")
    cases = [
        ("Cybersecurity IDS, 4 features",   CLASSICAL_ML,  0,    4),
        ("Image classification, 2048 dim",  CLASSICAL_ML,  0, 2048),
        ("NLP transformer, 50000 tokens",   CLASSICAL_ML,  0, 50_000),
        ("H2 molecule, 4 qubits",           MOLECULAR_SIM, 4,    0),
        ("FeMoco enzyme, 100 qubits",       MOLECULAR_SIM, 100,  0),
        ("Network MaxCut, 12 nodes",        COMBINATORIAL, 12,   0),
        ("Network MaxCut, 200 nodes",       COMBINATORIAL, 200,  0),
    ]
    for name, t, n, d in cases:
        print(f"  {name:<40} -> {allocate_tier(t, n, d)}")

    # Demo: Pareto
    print("\n=== Pareto Selection Demo (cybersecurity workload) ===")
    methods = [
        {"name": "SVM",   "cost": 9.9e-7, "energy": 0.64,    "latency": 0.005, "accuracy": 0.975},
        {"name": "RF",    "cost": 4.9e-5, "energy": 22.09,   "latency": 0.175, "accuracy": 0.997},
        {"name": "GBM",   "cost": 1.0e-4, "energy": 45.99,   "latency": 0.365, "accuracy": 0.996},
        {"name": "KNN",   "cost": 4.5e-4, "energy": 204.58,  "latency": 1.624, "accuracy": 0.994},
        {"name": "QSVM",  "cost": 2.10,   "energy": 8314.87, "latency": 1.155, "accuracy": 0.875},
    ]
    P = pareto_optimal(methods)
    print(f"  Pareto-optimal set: {[m['name'] for m in P]}")
    print(f"  Dominated:          {[m['name'] for m in methods if m not in P]}")

    print("\n=== Best by weights ===")
    print(f"  cost-only:    {best_by_weights(methods, 1, 0, 0)['name']}")
    print(f"  energy-only:  {best_by_weights(methods, 0, 1, 0)['name']}")
    print(f"  latency-only: {best_by_weights(methods, 0, 0, 1)['name']}")
    print(f"  balanced:     {best_by_weights(methods, 1, 1, 1)['name']}")
    print(f"  acc-priority: {best_by_weights(methods, 1, 1, 1, delta=10)['name']}")
