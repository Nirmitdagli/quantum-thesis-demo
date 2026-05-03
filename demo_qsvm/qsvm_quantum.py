"""Quantum SVM with ZZ feature map kernel for cybersecurity anomaly detection."""

import numpy as np
from qiskit.circuit import QuantumCircuit
from qiskit.quantum_info import Statevector
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from typing import Dict, Tuple


def build_zz_feature_map(x: np.ndarray) -> QuantumCircuit:
    """Build a ZZFeatureMap-style circuit encoding data point x.

    Applies Hadamard + phase encoding on each qubit, then
    ZZ entanglement between all pairs.
    """
    n = len(x)
    qc = QuantumCircuit(n)
    # First-order encoding
    for i in range(n):
        qc.h(i)
        qc.p(2.0 * x[i], i)
    # Second-order ZZ entanglement
    for i in range(n):
        for j in range(i + 1, n):
            qc.cx(i, j)
            qc.p(2.0 * (np.pi - x[i]) * (np.pi - x[j]), j)
            qc.cx(i, j)
    return qc


def kernel_entry(x: np.ndarray, y: np.ndarray) -> float:
    """Compute quantum kernel entry k(x, y).

    k(x, y) = |<0^n| U_dag(y) U(x) |0^n>|^2
    which is the probability of measuring |0...0> after
    applying U(x) followed by U_dag(y).
    """
    fm_x = build_zz_feature_map(x)
    fm_y = build_zz_feature_map(y)
    qc = fm_x.compose(fm_y.inverse())
    sv = Statevector(qc)
    return float(np.abs(sv[0]) ** 2)


def compute_kernel_matrix(X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
    """Compute the quantum kernel Gram matrix between X1 and X2."""
    n1, n2 = len(X1), len(X2)
    K = np.zeros((n1, n2))
    for i in range(n1):
        for j in range(n2):
            K[i, j] = kernel_entry(X1[i], X2[j])
    return K


def train_and_evaluate(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> Tuple[Dict[str, float], np.ndarray]:
    """Train quantum kernel SVM and return metrics + confusion matrix."""
    print("    Computing training kernel matrix...")
    K_train = compute_kernel_matrix(X_train, X_train)

    print("    Computing test kernel matrix...")
    K_test = compute_kernel_matrix(X_test, X_train)

    svm = SVC(kernel="precomputed")
    svm.fit(K_train, y_train)
    y_pred = svm.predict(K_test)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
    }
    cm = confusion_matrix(y_test, y_pred)
    return metrics, cm
