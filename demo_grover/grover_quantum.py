"""Grover's search algorithm implementation for key search."""

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit import transpile
from qiskit_aer import AerSimulator
from typing import Tuple, List
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def build_oracle(n_qubits: int, marked_state: int) -> QuantumCircuit:
    """Build Grover oracle that flips the phase of |marked_state>.

    Uses X gates to select the target state, then a multi-controlled Z
    gate (implemented as H-MCX-H on the last qubit).
    """
    qc = QuantumCircuit(n_qubits, name="Oracle")
    binary = format(marked_state, f"0{n_qubits}b")

    # Flip qubits where the marked state has bit '0'
    for i, bit in enumerate(binary):
        if bit == "0":
            qc.x(i)

    # Multi-controlled Z gate
    if n_qubits == 1:
        qc.z(0)
    else:
        qc.h(n_qubits - 1)
        qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        qc.h(n_qubits - 1)

    # Undo the X flips
    for i, bit in enumerate(binary):
        if bit == "0":
            qc.x(i)

    return qc


def build_diffusion(n_qubits: int) -> QuantumCircuit:
    """Build Grover diffusion operator (inversion about the mean).

    Implements 2|s><s| - I where |s> is the uniform superposition.
    """
    qc = QuantumCircuit(n_qubits, name="Diffusion")
    qc.h(range(n_qubits))
    qc.x(range(n_qubits))

    if n_qubits == 1:
        qc.z(0)
    else:
        qc.h(n_qubits - 1)
        qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
        qc.h(n_qubits - 1)

    qc.x(range(n_qubits))
    qc.h(range(n_qubits))
    return qc


def optimal_iterations(n_qubits: int) -> int:
    """Calculate the optimal number of Grover iterations: floor(pi/4 * sqrt(N))."""
    N = 2 ** n_qubits
    return max(1, int(np.floor(np.pi / 4.0 * np.sqrt(N))))


def run_grover(
    n_qubits: int = config.GROVER_QUBITS,
    marked_state: int = None,
    num_iterations: int = None,
    shots: int = config.SHOTS,
) -> Tuple[float, int, str]:
    """Run Grover's algorithm for a single search.

    Returns:
        (success_probability, marked_state_int, marked_state_binary)
    """
    rng = np.random.RandomState(config.RANDOM_STATE)
    if marked_state is None:
        marked_state = rng.randint(0, 2 ** n_qubits)
    if num_iterations is None:
        num_iterations = optimal_iterations(n_qubits)

    oracle = build_oracle(n_qubits, marked_state)
    diffusion = build_diffusion(n_qubits)

    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))

    for _ in range(num_iterations):
        qc.compose(oracle, inplace=True)
        qc.compose(diffusion, inplace=True)

    qc.measure_all()

    backend = AerSimulator()
    qc_t = transpile(qc, backend)
    result = backend.run(qc_t, shots=shots).result()
    counts = result.get_counts()

    # Qiskit uses little-endian bit ordering in measurement strings
    target_bitstring = format(marked_state, f"0{n_qubits}b")[::-1]
    success_count = counts.get(target_bitstring, 0)
    success_prob = success_count / shots

    return success_prob, marked_state, format(marked_state, f"0{n_qubits}b")


def run_grover_varying_iterations(
    n_qubits: int = config.GROVER_QUBITS,
    max_iter_mult: int = 3,
    shots: int = config.SHOTS,
) -> Tuple[List[int], List[float]]:
    """Run Grover for varying iteration counts to show oscillation.

    Returns:
        (iteration_counts, success_probabilities)
    """
    rng = np.random.RandomState(config.RANDOM_STATE)
    marked_state = rng.randint(0, 2 ** n_qubits)
    opt_iter = optimal_iterations(n_qubits)
    max_iter = max(opt_iter * max_iter_mult, 8)

    iterations = list(range(1, max_iter + 1))
    probabilities = []
    for n_iter in iterations:
        prob, _, _ = run_grover(n_qubits, marked_state, n_iter, shots)
        probabilities.append(prob)

    return iterations, probabilities
