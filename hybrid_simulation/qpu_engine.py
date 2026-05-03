"""QPU Engine — handles quantum circuit execution for all three experiments.

In the hybrid architecture, the QPU is responsible for:
  1. Quantum kernel evaluation (ZZ feature map circuits for QSVM)
  2. QAOA variational circuits (cost + mixer layers for MaxCut)
  3. Grover search circuits (oracle + diffusion iterations)
  4. Quantum state preparation and measurement
"""

import time
import numpy as np
from typing import Dict, Any, List, Tuple

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.circuit.library import ZZFeatureMap
from scipy.optimize import minimize


# ── Power model for QPU ──────────────────────────────────────
# Superconducting QPU: ~20 kW total system (including dilution fridge)
# But actual gate operations consume far less per operation
QPU_SYSTEM_WATTS = 20000     # Full cryogenic system
QPU_GATE_ENERGY_J = 1e-19   # ~attojoule per gate (theoretical)
QPU_PUE = 1.1               # QPU facilities are highly optimized

SHOTS = 2000
BACKEND = AerSimulator()


def _qpu_energy(runtime: float, n_gates: int = 0) -> Tuple[float, float]:
    """Estimate QPU energy: (simulated, projected_real_hw)."""
    simulated = runtime * 6000 * 1.2  # Simulator on classical HW
    # Real QPU: system power for circuit duration + gate energy
    real_circuit_time = n_gates * 50e-9  # ~50ns per gate average
    real_hw = QPU_SYSTEM_WATTS * real_circuit_time * QPU_PUE
    return simulated, max(real_hw, 0.001)


# ═══════════════════════════════════════════════════════════════
# TASK 1: Quantum Kernel Evaluation (QSVM)
# ═══════════════════════════════════════════════════════════════

def quantum_kernel_entry(x1: np.ndarray, x2: np.ndarray) -> float:
    """QPU: Compute one quantum kernel entry k(x1, x2).

    Uses ZZ feature map: |0⟩ → U(x1)|0⟩, then measures overlap with U(x2).
    k(x1, x2) = |⟨0|U†(x2)U(x1)|0⟩|²
    """
    n_features = len(x1)
    qc = QuantumCircuit(n_features)

    # U(x1): encode first data point
    for i in range(n_features):
        qc.h(i)
        qc.rz(2 * x1[i], i)
    for i in range(n_features - 1):
        qc.cx(i, i + 1)
        qc.rz(2 * (np.pi - x1[i]) * (np.pi - x1[i + 1]), i + 1)
        qc.cx(i, i + 1)

    # U†(x2): encode second data point (inverse)
    for i in range(n_features - 2, -1, -1):
        qc.cx(i, i + 1)
        qc.rz(-2 * (np.pi - x2[i]) * (np.pi - x2[i + 1]), i + 1)
        qc.cx(i, i + 1)
    for i in range(n_features - 1, -1, -1):
        qc.rz(-2 * x2[i], i)
        qc.h(i)

    qc.measure_all()

    result = BACKEND.run(qc, shots=SHOTS).result()
    counts = result.get_counts()
    zero_state = "0" * n_features
    return counts.get(zero_state, 0) / SHOTS


def compute_quantum_kernel_matrix(X_train: np.ndarray,
                                  X_test: np.ndarray = None) -> Dict[str, Any]:
    """QPU: Compute full quantum kernel matrix for QSVM.

    Each entry requires a separate circuit execution on the QPU.
    """
    t0 = time.perf_counter()

    if X_test is None:
        X_test = X_train

    n_train = len(X_train)
    n_test = len(X_test)
    kernel = np.zeros((n_test, n_train))
    n_circuits = 0

    for i in range(n_test):
        for j in range(n_train):
            kernel[i, j] = quantum_kernel_entry(X_test[i], X_train[j])
            n_circuits += 1

    runtime = time.perf_counter() - t0
    n_gates_per_circuit = 4 * len(X_train[0]) * 3  # approximate
    total_gates = n_circuits * n_gates_per_circuit
    sim_energy, real_energy = _qpu_energy(runtime, total_gates)

    return {
        "task": "quantum_kernel_matrix",
        "unit": "QPU",
        "kernel_matrix": kernel,
        "shape": kernel.shape,
        "n_circuits": n_circuits,
        "total_gates": total_gates,
        "runtime": runtime,
        "energy_j": sim_energy,
        "energy_real_hw_j": real_energy,
        "ops": f"{n_circuits} ZZ kernel circuits × {SHOTS} shots",
    }


# ═══════════════════════════════════════════════════════════════
# TASK 2: QAOA Circuit Execution
# ═══════════════════════════════════════════════════════════════

def run_qaoa(edges: list, n_nodes: int, depth: int = 2) -> Dict[str, Any]:
    """QPU: Run QAOA for MaxCut optimization.

    Builds and optimizes a variational quantum circuit with:
    - Cost layer: encodes MaxCut objective
    - Mixer layer: explores solution space
    - COBYLA optimizer tunes (gamma, beta) parameters
    """
    t0 = time.perf_counter()

    convergence = []
    total_circuits = 0

    def qaoa_circuit(params):
        """Build QAOA circuit with given parameters."""
        gammas = params[:depth]
        betas = params[depth:]

        qc = QuantumCircuit(n_nodes)

        # Initial superposition
        for i in range(n_nodes):
            qc.h(i)

        # QAOA layers
        for layer in range(depth):
            # Cost layer
            for i, j in edges:
                qc.cx(i, j)
                qc.rz(2 * gammas[layer], j)
                qc.cx(i, j)
            # Mixer layer
            for i in range(n_nodes):
                qc.rx(2 * betas[layer], i)

        qc.measure_all()
        return qc

    def evaluate(params):
        """Evaluate QAOA expected cut value."""
        nonlocal total_circuits
        qc = qaoa_circuit(params)
        result = BACKEND.run(qc, shots=SHOTS).result()
        counts = result.get_counts()
        total_circuits += 1

        expected_cut = 0
        for bitstring, count in counts.items():
            bits = bitstring[::-1]
            cut = sum(1 for i, j in edges if bits[i] != bits[j])
            expected_cut += cut * count / SHOTS

        convergence.append(expected_cut)
        return -expected_cut  # minimize negative = maximize cut

    # Optimize with COBYLA
    init_params = np.random.RandomState(42).uniform(0, np.pi, 2 * depth)
    opt_result = minimize(evaluate, init_params, method="COBYLA",
                          options={"maxiter": 100, "rhobeg": 0.5})

    best_cut = -opt_result.fun

    # Compute optimal cut by brute force for comparison
    optimal_cut = 0
    for bits in range(2 ** n_nodes):
        bitstring = format(bits, f"0{n_nodes}b")
        cut = sum(1 for i, j in edges if bitstring[i] != bitstring[j])
        optimal_cut = max(optimal_cut, cut)

    approx_ratio = best_cut / optimal_cut if optimal_cut > 0 else 0

    runtime = time.perf_counter() - t0
    n_gates = total_circuits * (len(edges) * 3 + n_nodes) * depth
    sim_energy, real_energy = _qpu_energy(runtime, n_gates)

    return {
        "task": "qaoa_maxcut",
        "unit": "QPU",
        "best_cut": best_cut,
        "optimal_cut": optimal_cut,
        "approx_ratio": approx_ratio,
        "convergence": convergence,
        "total_circuits": total_circuits,
        "total_gates": n_gates,
        "depth": depth,
        "runtime": runtime,
        "energy_j": sim_energy,
        "energy_real_hw_j": real_energy,
        "ops": f"QAOA p={depth}, {total_circuits} circuits, COBYLA optimizer",
    }


# ═══════════════════════════════════════════════════════════════
# TASK 3: Grover Search Circuit
# ═══════════════════════════════════════════════════════════════

def run_grover(n_qubits: int = 4, target: str = "0110") -> Dict[str, Any]:
    """QPU: Run Grover's search algorithm.

    Finds target state in O(sqrt(N)) iterations vs O(N) classical.
    """
    t0 = time.perf_counter()

    N = 2 ** n_qubits
    optimal_iters = int(np.round(np.pi / 4 * np.sqrt(N)))

    # Build Grover circuit
    qc = QuantumCircuit(n_qubits)

    # Initial superposition
    for i in range(n_qubits):
        qc.h(i)

    for _ in range(optimal_iters):
        # Oracle: flip phase of target state
        target_bits = [int(b) for b in target]
        for i, bit in enumerate(target_bits):
            if bit == 0:
                qc.x(i)
        # Multi-controlled Z gate
        if n_qubits == 2:
            qc.cz(0, 1)
        else:
            qc.h(n_qubits - 1)
            qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
            qc.h(n_qubits - 1)
        for i, bit in enumerate(target_bits):
            if bit == 0:
                qc.x(i)

        # Diffusion operator
        for i in range(n_qubits):
            qc.h(i)
            qc.x(i)
        qc.h(n_qubits - 1)
        qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        qc.h(n_qubits - 1)
        for i in range(n_qubits):
            qc.x(i)
            qc.h(i)

    qc.measure_all()

    result = BACKEND.run(qc, shots=SHOTS).result()
    counts = result.get_counts()

    # Reverse bit ordering for Qiskit
    target_reversed = target[::-1]
    success_count = counts.get(target_reversed, 0)
    success_prob = success_count / SHOTS

    # Probability distribution
    prob_dist = {}
    for state, count in counts.items():
        prob_dist[state[::-1]] = count / SHOTS

    runtime = time.perf_counter() - t0
    n_gates = optimal_iters * (n_qubits * 4 + 2 * n_qubits) + n_qubits
    sim_energy, real_energy = _qpu_energy(runtime, n_gates)

    return {
        "task": "grover_search",
        "unit": "QPU",
        "target": target,
        "success_prob": success_prob,
        "optimal_iterations": optimal_iters,
        "search_space": N,
        "top_states": dict(sorted(prob_dist.items(),
                                  key=lambda x: -x[1])[:5]),
        "runtime": runtime,
        "energy_j": sim_energy,
        "energy_real_hw_j": real_energy,
        "ops": f"Grover {optimal_iters} iters on {n_qubits} qubits × {SHOTS} shots",
    }
