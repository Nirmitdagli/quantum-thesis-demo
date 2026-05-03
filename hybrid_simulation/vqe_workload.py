"""VQE Workload — Variational Quantum Eigensolver for H2 molecule.

This is the MOLECULAR SIMULATION workload (Workload 2).
Contrast: cybersecurity QSVM workload (Workload 1) where classical wins.

For H2 at internuclear distance 0.735 Angstrom, after parity transformation
and qubit reduction, the Hamiltonian collapses to 2 qubits:

  H = c0 II + c1 IZ + c2 ZI + c3 ZZ + c4 XX

where coefficients (in Hartree) are:
  c0 = -1.0523732,  c1 =  0.39793742,  c2 = -0.39793742
  c3 = -0.0112801,  c4 =  0.18093119

The exact ground-state energy is E_min = -1.857275 Hartree.

This is a textbook H2 example used in Peruzzo et al. (2014), Kandala et al.
(2017), and the standard Qiskit tutorial. Numbers come from
Bravyi-Kitaev / parity-reduced JW mapping at R = 0.735 A.
"""

import time
import numpy as np
from typing import Dict, Any, List
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from scipy.optimize import minimize


# ---- H2 Hamiltonian coefficients (Hartree, R=0.735 A, parity-reduced) ----
H2_COEFFS = {
    "II":  -1.0523732,
    "IZ":   0.39793742,
    "ZI":  -0.39793742,
    "ZZ":  -0.0112801,
    "XX":   0.18093119,
}
H2_EXACT_ENERGY = -1.857275  # Hartree, exact ground state

SHOTS = 4000
BACKEND = AerSimulator()

# Power model (matches qpu_engine.py)
QPU_SYSTEM_WATTS = 20000
QPU_PUE = 1.1


def _qpu_energy(runtime: float) -> float:
    """Match qpu_engine.py simulator energy model."""
    return runtime * 6000 * 1.2


# ============================================================
# CLASSICAL BASELINE: Exact diagonalization
# ============================================================

def classical_exact_diagonalization() -> Dict[str, Any]:
    """CPU: Exact ground-state energy of H2 via NumPy diagonalisation.

    For 2 qubits, the Hamiltonian is a 4x4 matrix. We construct it as
    sum of Pauli operators and diagonalise.
    """
    t0 = time.perf_counter()

    I = np.eye(2)
    X = np.array([[0, 1], [1, 0]])
    Z = np.array([[1, 0], [0, -1]])

    H = (H2_COEFFS["II"] * np.kron(I, I)
       + H2_COEFFS["IZ"] * np.kron(I, Z)
       + H2_COEFFS["ZI"] * np.kron(Z, I)
       + H2_COEFFS["ZZ"] * np.kron(Z, Z)
       + H2_COEFFS["XX"] * np.kron(X, X))

    eigenvalues = np.linalg.eigvalsh(H)
    ground_state = float(eigenvalues[0])

    runtime = time.perf_counter() - t0

    # CPU energy (matches cpu_engine.py)
    cpu_energy = runtime * 150 * 0.7 * 1.2

    return {
        "task": "exact_diagonalization",
        "unit": "CPU",
        "ground_state_energy": ground_state,
        "exact_reference": H2_EXACT_ENERGY,
        "energy_error_hartree": abs(ground_state - H2_EXACT_ENERGY),
        "hilbert_dim": 4,
        "runtime": runtime,
        "energy_j": cpu_energy,
        "ops": "build 4x4 Hamiltonian -> diagonalize",
    }


# ============================================================
# QUANTUM: VQE pipeline
# ============================================================

def _ansatz(params: np.ndarray) -> QuantumCircuit:
    """Hardware-efficient ansatz: 2 qubits, RY rotations + CNOT entangler.

    Standard Qiskit-tutorial-style ansatz used in Kandala et al. (2017).
    Depth 2: [RY-RY-CNOT-RY-RY] -> 4 trainable params.
    """
    qc = QuantumCircuit(2)
    qc.ry(params[0], 0)
    qc.ry(params[1], 1)
    qc.cx(0, 1)
    qc.ry(params[2], 0)
    qc.ry(params[3], 1)
    return qc


def _measure_pauli(ansatz: QuantumCircuit, pauli: str) -> float:
    """Measure expectation value of a 2-qubit Pauli string in the ansatz state."""
    qc = ansatz.copy()
    # Apply basis change for X measurements
    for i, p in enumerate(pauli):
        if p == "X":
            qc.h(i)
        # Z is the default measurement basis
    qc.measure_all()

    result = BACKEND.run(qc, shots=SHOTS).result()
    counts = result.get_counts()

    expectation = 0.0
    for bitstring, count in counts.items():
        # Qiskit returns reversed bit order
        bits = bitstring[::-1]
        sign = 1
        for i, p in enumerate(pauli):
            if p != "I" and bits[i] == "1":
                sign *= -1
        expectation += sign * count / SHOTS
    return expectation


def _h2_expectation(params: np.ndarray) -> float:
    """Compute <H> for H2 given ansatz parameters."""
    ansatz = _ansatz(params)
    energy = H2_COEFFS["II"]  # II expectation = 1
    energy += H2_COEFFS["IZ"] * _measure_pauli(ansatz, "IZ")
    energy += H2_COEFFS["ZI"] * _measure_pauli(ansatz, "ZI")
    energy += H2_COEFFS["ZZ"] * _measure_pauli(ansatz, "ZZ")
    energy += H2_COEFFS["XX"] * _measure_pauli(ansatz, "XX")
    return energy


def run_vqe_h2(random_state: int = 42, maxiter: int = 60) -> Dict[str, Any]:
    """QPU: Run VQE for H2 ground state.

    Returns measured ground state energy, error vs exact, and convergence trace.
    """
    t0 = time.perf_counter()

    rng = np.random.RandomState(random_state)
    init_params = rng.uniform(0, 2 * np.pi, 4)

    convergence = []
    n_circuits = [0]  # mutable counter

    def cost(params):
        n_circuits[0] += 4  # 4 Pauli measurements per evaluation
        e = _h2_expectation(params)
        convergence.append(e)
        return e

    result = minimize(cost, init_params, method="COBYLA",
                      options={"maxiter": maxiter, "rhobeg": 0.3})

    final_energy = float(result.fun)
    runtime = time.perf_counter() - t0
    sim_energy = _qpu_energy(runtime)

    return {
        "task": "vqe_h2_ground_state",
        "unit": "QPU",
        "ground_state_energy": final_energy,
        "exact_reference": H2_EXACT_ENERGY,
        "energy_error_hartree": abs(final_energy - H2_EXACT_ENERGY),
        "convergence": convergence,
        "n_iterations": len(convergence),
        "n_circuits": n_circuits[0],
        "n_qubits": 2,
        "runtime": runtime,
        "energy_j": sim_energy,
        "ops": f"VQE H2, COBYLA, {n_circuits[0]} Pauli measurements",
    }


if __name__ == "__main__":
    print("=== Classical exact diagonalization ===")
    cls = classical_exact_diagonalization()
    print(f"Ground state: {cls['ground_state_energy']:.6f} Hartree")
    print(f"Error vs exact: {cls['energy_error_hartree']:.2e} Hartree")
    print(f"Runtime: {cls['runtime']*1000:.3f} ms")
    print(f"Energy: {cls['energy_j']:.6f} J")

    print("\n=== Quantum VQE ===")
    vqe = run_vqe_h2()
    print(f"Ground state: {vqe['ground_state_energy']:.6f} Hartree")
    print(f"Error vs exact: {vqe['energy_error_hartree']:.4f} Hartree")
    print(f"Iterations: {vqe['n_iterations']}")
    print(f"Circuits: {vqe['n_circuits']}")
    print(f"Runtime: {vqe['runtime']:.3f} s")
    print(f"Energy: {vqe['energy_j']:.2f} J")
