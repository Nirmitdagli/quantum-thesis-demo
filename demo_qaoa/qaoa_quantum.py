"""QAOA implementation for the MaxCut optimization problem."""

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit import transpile
from qiskit_aer import AerSimulator
from scipy.optimize import minimize
from typing import List, Tuple, Dict
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def generate_random_graph(
    n_nodes: int = config.QAOA_NODES,
    edge_prob: float = config.QAOA_EDGE_PROB,
    random_state: int = config.RANDOM_STATE,
) -> Tuple[int, List[Tuple[int, int]]]:
    """Generate a random Erdos-Renyi graph as (n_nodes, edge_list)."""
    rng = np.random.RandomState(random_state)
    edges = []
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if rng.random() < edge_prob:
                edges.append((i, j))
    # Guarantee at least one edge
    if len(edges) == 0:
        edges.append((0, 1))
    return n_nodes, edges


def build_qaoa_circuit(
    n_qubits: int,
    edges: List[Tuple[int, int]],
    gammas: np.ndarray,
    betas: np.ndarray,
) -> QuantumCircuit:
    """Build a QAOA circuit with p layers for MaxCut.

    Cost layer: ZZ interaction via CNOT-RZ-CNOT on each edge.
    Mixer layer: RX rotation on each qubit.
    """
    p = len(gammas)
    qc = QuantumCircuit(n_qubits)

    # Initial superposition
    qc.h(range(n_qubits))

    for layer in range(p):
        # Cost unitary: exp(-i * gamma * C)
        for i, j in edges:
            qc.cx(i, j)
            qc.rz(gammas[layer], j)
            qc.cx(i, j)
        # Mixer unitary: exp(-i * beta * B) with B = sum(X_i)
        for i in range(n_qubits):
            qc.rx(2.0 * betas[layer], i)

    qc.measure_all()
    return qc


def compute_cut_value(bitstring: str, edges: List[Tuple[int, int]]) -> int:
    """Count edges cut by the given bitstring partition."""
    cut = 0
    for i, j in edges:
        if bitstring[i] != bitstring[j]:
            cut += 1
    return cut


def expected_cut(
    counts: Dict[str, int],
    edges: List[Tuple[int, int]],
    n_qubits: int,
) -> float:
    """Compute expected cut value from measurement outcome counts."""
    total = sum(counts.values())
    exp_val = 0.0
    for bitstring, count in counts.items():
        # Qiskit returns bitstrings in little-endian; reverse for node ordering
        bs = bitstring[::-1]
        exp_val += compute_cut_value(bs, edges) * count / total
    return exp_val


def find_max_cut_brute_force(
    n_qubits: int, edges: List[Tuple[int, int]]
) -> int:
    """Find the optimal MaxCut value by exhaustive enumeration."""
    best = 0
    for k in range(2 ** n_qubits):
        bs = format(k, f"0{n_qubits}b")
        best = max(best, compute_cut_value(bs, edges))
    return best


def run_qaoa(
    n_qubits: int,
    edges: List[Tuple[int, int]],
    depth: int = config.QAOA_DEPTH,
    shots: int = config.SHOTS,
) -> Tuple[float, List[float]]:
    """Run QAOA with COBYLA optimizer.

    Returns:
        (best_expected_cut, convergence_history)
    """
    backend = AerSimulator()
    convergence: List[float] = []

    def objective(params: np.ndarray) -> float:
        gammas = params[:depth]
        betas = params[depth:]
        qc = build_qaoa_circuit(n_qubits, edges, gammas, betas)
        qc_t = transpile(qc, backend)
        result = backend.run(qc_t, shots=shots).result()
        counts = result.get_counts()
        cut_val = expected_cut(counts, edges, n_qubits)
        convergence.append(cut_val)
        return -cut_val  # minimize negative → maximize cut

    x0 = np.random.RandomState(config.RANDOM_STATE).uniform(0, np.pi, 2 * depth)
    minimize(objective, x0, method="COBYLA", options={"maxiter": 150})

    best_cut = max(convergence) if convergence else 0.0
    return best_cut, convergence
