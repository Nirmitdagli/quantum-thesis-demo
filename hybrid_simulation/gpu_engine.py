"""GPU Engine — handles parallel matrix operations, batch ML, and kernel computation.

In the hybrid architecture, the GPU is responsible for:
  1. Parallel kernel matrix computation (vectorized dot products, RBF kernels)
  2. Batch neural network feature extraction (simulated dense layers)
  3. Large-scale matrix operations (similarity matrices, PCA)
  4. Accelerated training loops (gradient descent on feature embeddings)

Note: We simulate GPU behavior using NumPy vectorized operations and
concurrent.futures to demonstrate the parallel speedup pattern.
Real GPU would use CUDA/cuDNN via PyTorch or TensorFlow.
"""

import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Tuple


# ── Power model for GPU ──────────────────────────────────────
GPU_TDP_WATTS = 300          # Typical data center GPU (A100 / H100)
GPU_UTILIZATION = 0.85       # High utilization during matrix ops
GPU_PUE = 1.2


def _gpu_energy(runtime: float) -> float:
    """Estimate GPU energy in joules."""
    return runtime * GPU_TDP_WATTS * GPU_UTILIZATION * GPU_PUE


# ═══════════════════════════════════════════════════════════════
# TASK 1: Parallel Kernel Matrix Computation
# ═══════════════════════════════════════════════════════════════

def compute_rbf_kernel_matrix(X: np.ndarray, Y: np.ndarray = None,
                              gamma: float = 1.0) -> Dict[str, Any]:
    """GPU: Compute RBF kernel matrix using vectorized operations.

    K(x, y) = exp(-gamma * ||x - y||^2)
    This is massively parallel — each element is independent.
    """
    t0 = time.perf_counter()

    if Y is None:
        Y = X

    # Vectorized pairwise squared distances (GPU-style parallel)
    X_sq = np.sum(X ** 2, axis=1).reshape(-1, 1)
    Y_sq = np.sum(Y ** 2, axis=1).reshape(1, -1)
    distances = X_sq + Y_sq - 2 * X @ Y.T

    kernel_matrix = np.exp(-gamma * distances)

    runtime = time.perf_counter() - t0

    return {
        "task": "rbf_kernel_matrix",
        "unit": "GPU",
        "kernel_matrix": kernel_matrix,
        "shape": kernel_matrix.shape,
        "runtime": runtime,
        "energy_j": _gpu_energy(runtime),
        "ops": f"parallel RBF kernel {kernel_matrix.shape[0]}x{kernel_matrix.shape[1]}",
        "flops_estimate": 3 * X.shape[0] * Y.shape[0] * X.shape[1],
    }


def compute_cosine_similarity_matrix(X: np.ndarray) -> Dict[str, Any]:
    """GPU: Compute cosine similarity matrix (parallel dot products)."""
    t0 = time.perf_counter()

    norms = np.linalg.norm(X, axis=1, keepdims=True)
    X_normalized = X / (norms + 1e-10)
    similarity = X_normalized @ X_normalized.T

    runtime = time.perf_counter() - t0

    return {
        "task": "cosine_similarity",
        "unit": "GPU",
        "similarity_matrix": similarity,
        "shape": similarity.shape,
        "runtime": runtime,
        "energy_j": _gpu_energy(runtime),
        "ops": f"parallel cosine sim {similarity.shape[0]}x{similarity.shape[1]}",
    }


# ═══════════════════════════════════════════════════════════════
# TASK 2: Neural Network Feature Extraction (Simulated)
# ═══════════════════════════════════════════════════════════════

def neural_feature_extraction(X: np.ndarray, hidden_dims: tuple = (64, 32, 16),
                              random_state: int = 42) -> Dict[str, Any]:
    """GPU: Simulate a neural network forward pass for feature extraction.

    Represents what a GPU does in hybrid pipelines — extract deep features
    before passing to the quantum kernel. Layers:
      Input → Dense(64, ReLU) → Dense(32, ReLU) → Dense(16, tanh) → Output
    """
    t0 = time.perf_counter()

    rng = np.random.RandomState(random_state)
    activations = [X]
    current = X

    layer_info = []
    for i, dim in enumerate(hidden_dims):
        W = rng.randn(current.shape[1], dim) * np.sqrt(2.0 / current.shape[1])
        b = np.zeros(dim)
        z = current @ W + b

        if i < len(hidden_dims) - 1:
            current = np.maximum(0, z)  # ReLU
            act_name = "ReLU"
        else:
            current = np.tanh(z)        # tanh for final (bounded for quantum encoding)
            act_name = "tanh"

        layer_info.append({
            "layer": i + 1,
            "input_dim": z.shape[1] - dim + current.shape[1],
            "output_dim": dim,
            "activation": act_name,
            "params": W.size + b.size,
        })
        activations.append(current)

    runtime = time.perf_counter() - t0

    total_params = sum(l["params"] for l in layer_info)

    return {
        "task": "neural_feature_extraction",
        "unit": "GPU",
        "features": current,
        "output_shape": current.shape,
        "layers": layer_info,
        "total_params": total_params,
        "runtime": runtime,
        "energy_j": _gpu_energy(runtime),
        "ops": f"forward pass {len(hidden_dims)} layers, {total_params} params",
    }


# ═══════════════════════════════════════════════════════════════
# TASK 3: Batch Parallel Classification
# ═══════════════════════════════════════════════════════════════

def batch_parallel_classify(kernel_matrix: np.ndarray, y_train: np.ndarray,
                            X_test_kernel: np.ndarray) -> Dict[str, Any]:
    """GPU: Batch parallel classification using kernel matrix.

    Uses kernel values as similarity scores for weighted voting —
    simulates what a GPU does when running SVM inference at scale.
    """
    t0 = time.perf_counter()

    predictions = []

    def classify_single(test_idx):
        """Classify a single test sample using kernel-weighted voting."""
        similarities = X_test_kernel[test_idx]
        # Weighted vote: sum similarities for each class
        class_scores = {}
        for i, label in enumerate(y_train):
            class_scores[label] = class_scores.get(label, 0) + similarities[i]
        return max(class_scores, key=class_scores.get)

    # Parallel classification (simulates GPU thread parallelism)
    with ThreadPoolExecutor(max_workers=4) as executor:
        predictions = list(executor.map(classify_single,
                                        range(X_test_kernel.shape[0])))

    predictions = np.array(predictions)
    runtime = time.perf_counter() - t0

    return {
        "task": "batch_classification",
        "unit": "GPU",
        "predictions": predictions,
        "n_classified": len(predictions),
        "runtime": runtime,
        "energy_j": _gpu_energy(runtime),
        "ops": f"parallel classify {len(predictions)} samples",
    }


# ═══════════════════════════════════════════════════════════════
# TASK 4: Matrix Operations for QAOA
# ═══════════════════════════════════════════════════════════════

def compute_qaoa_cost_matrix(adjacency: np.ndarray) -> Dict[str, Any]:
    """GPU: Compute the cost Hamiltonian matrix for QAOA.

    For MaxCut: H_C = sum_{(i,j) in E} (1/2)(I - Z_i Z_j)
    The GPU computes the full operator matrix using Kronecker products.
    """
    t0 = time.perf_counter()

    n = adjacency.shape[0]
    dim = 2 ** n
    H_cost = np.zeros((dim, dim))

    I2 = np.eye(2)
    Z = np.array([[1, 0], [0, -1]])

    for i in range(n):
        for j in range(i + 1, n):
            if adjacency[i][j] == 0:
                continue
            # Build Z_i Z_j operator via Kronecker products
            op = np.array([[1.0]])
            for k in range(n):
                if k == i or k == j:
                    op = np.kron(op, Z)
                else:
                    op = np.kron(op, I2)
            H_cost += 0.5 * (np.eye(dim) - op)

    runtime = time.perf_counter() - t0

    return {
        "task": "qaoa_cost_matrix",
        "unit": "GPU",
        "hamiltonian": H_cost,
        "dimension": dim,
        "n_qubits": n,
        "runtime": runtime,
        "energy_j": _gpu_energy(runtime),
        "ops": f"Kronecker products → {dim}x{dim} Hamiltonian",
    }


# ═══════════════════════════════════════════════════════════════
# TASK 5: Parallel Grover Oracle Evaluation
# ═══════════════════════════════════════════════════════════════

def parallel_oracle_evaluation(n_qubits: int = 4,
                               target: str = "0110") -> Dict[str, Any]:
    """GPU: Evaluate oracle function across all states in parallel.

    In a real hybrid system, the GPU pre-computes oracle truth tables
    and assists in circuit compilation/verification.
    """
    t0 = time.perf_counter()

    search_space = 2 ** n_qubits
    states = np.arange(search_space)

    # Vectorized oracle evaluation (all states at once — GPU parallel)
    target_int = int(target, 2)
    oracle_results = (states == target_int).astype(int)

    # Build oracle unitary matrix
    oracle_matrix = np.eye(search_space)
    oracle_matrix[target_int, target_int] = -1

    # Build diffusion operator matrix
    psi = np.ones(search_space) / np.sqrt(search_space)
    diffusion = 2 * np.outer(psi, psi) - np.eye(search_space)

    runtime = time.perf_counter() - t0

    return {
        "task": "oracle_evaluation",
        "unit": "GPU",
        "oracle_matrix": oracle_matrix,
        "diffusion_matrix": diffusion,
        "target_index": target_int,
        "search_space": search_space,
        "runtime": runtime,
        "energy_j": _gpu_energy(runtime),
        "ops": f"parallel oracle eval {search_space} states + matrix build",
    }
