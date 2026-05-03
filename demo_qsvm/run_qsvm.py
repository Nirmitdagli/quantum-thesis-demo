"""Run QSVM vs Classical SVM experiment for anomaly detection."""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from utils.timing import Timer
from utils.energy import estimate_energy
from utils.dataset import generate_anomaly_dataset
from utils.logger import log_result
from demo_qsvm import qsvm_quantum, svm_classical


def plot_confusion_matrix(cm: np.ndarray, title: str, filepath: str) -> None:
    """Save confusion matrix as a publication-quality heatmap."""
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=[0, 1],
        yticks=[0, 1],
        xticklabels=["Normal", "Anomaly"],
        yticklabels=["Normal", "Anomaly"],
        xlabel="Predicted Label",
        ylabel="True Label",
        title=title,
    )
    for i in range(2):
        for j in range(2):
            color = "white" if cm[i, j] > cm.max() / 2 else "black"
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color=color, fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()


def plot_accuracy_comparison(
    q_metrics: dict, c_metrics: dict, filepath: str
) -> None:
    """Bar chart comparing QSVM vs Classical SVM classification metrics."""
    labels = ["Accuracy", "Precision", "Recall", "F1 Score"]
    q_vals = [q_metrics[k] for k in ["accuracy", "precision", "recall", "f1"]]
    c_vals = [c_metrics[k] for k in ["accuracy", "precision", "recall", "f1"]]

    x = np.arange(len(labels))
    width = 0.3

    fig, ax = plt.subplots(figsize=(8, 5))
    bars_q = ax.bar(x - width / 2, q_vals, width,
                    label="Quantum SVM (ZZ Kernel)", color="#4C72B0")
    bars_c = ax.bar(x + width / 2, c_vals, width,
                    label="Classical SVM (RBF)", color="#DD8452")

    for bars in [bars_q, bars_c]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                    f"{h:.3f}", ha="center", va="bottom", fontsize=9)

    ax.set_ylabel("Score")
    ax.set_title("QSVM vs Classical SVM — Cybersecurity Anomaly Detection")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.15)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150)
    plt.close()


def run() -> dict:
    """Execute the full QSVM experiment and return results dictionary."""
    os.makedirs(config.PLOTS_DIR, exist_ok=True)

    print("\n" + "=" * 60)
    print("  EXPERIMENT 1: QSVM Cybersecurity Anomaly Detection")
    print("=" * 60)

    X_train, X_test, y_train, y_test = generate_anomaly_dataset()
    num_qubits = X_train.shape[1]
    print(f"  Dataset: {len(X_train)} train, {len(X_test)} test, "
          f"{num_qubits} features/qubits")

    # --- Quantum SVM ---
    print("\n  [Quantum SVM — ZZ Feature Map Kernel]")
    with Timer("QSVM") as qt:
        q_metrics, q_cm = qsvm_quantum.train_and_evaluate(
            X_train, X_test, y_train, y_test
        )
    q_energy = estimate_energy(qt.elapsed)
    print(f"    Accuracy:  {q_metrics['accuracy']:.4f}")
    print(f"    Precision: {q_metrics['precision']:.4f}")
    print(f"    Recall:    {q_metrics['recall']:.4f}")
    print(f"    F1 Score:  {q_metrics['f1']:.4f}")
    print(f"    Runtime:   {qt.elapsed:.2f}s")
    print(f"    Energy:    {q_energy[0]:.1f} – {q_energy[1]:.1f} J")

    # --- Classical SVM ---
    print("\n  [Classical SVM — RBF Kernel]")
    with Timer("Classical SVM") as ct:
        c_metrics, c_cm = svm_classical.train_and_evaluate(
            X_train, X_test, y_train, y_test
        )
    c_energy = estimate_energy(ct.elapsed)
    print(f"    Accuracy:  {c_metrics['accuracy']:.4f}")
    print(f"    Precision: {c_metrics['precision']:.4f}")
    print(f"    Recall:    {c_metrics['recall']:.4f}")
    print(f"    F1 Score:  {c_metrics['f1']:.4f}")
    print(f"    Runtime:   {ct.elapsed:.4f}s")
    print(f"    Energy:    {c_energy[0]:.4f} – {c_energy[1]:.4f} J")

    # --- Plots ---
    plot_confusion_matrix(
        q_cm, "QSVM Confusion Matrix",
        os.path.join(config.PLOTS_DIR, "confusion_matrix_qsvm.png"),
    )
    plot_confusion_matrix(
        c_cm, "Classical SVM Confusion Matrix",
        os.path.join(config.PLOTS_DIR, "confusion_matrix_classical.png"),
    )
    plot_accuracy_comparison(
        q_metrics, c_metrics,
        os.path.join(config.PLOTS_DIR, "accuracy_comparison_qsvm.png"),
    )
    print("  Plots saved.")

    # --- Log ---
    log_result("QSVM", "Quantum SVM", "statevector", num_qubits, 0,
               q_metrics["accuracy"], q_metrics["f1"], qt.elapsed, *q_energy)
    log_result("QSVM", "Classical SVM", "sklearn", num_qubits, 0,
               c_metrics["accuracy"], c_metrics["f1"], ct.elapsed, *c_energy)

    return {
        "quantum": {"metrics": q_metrics, "runtime": qt.elapsed, "energy": q_energy},
        "classical": {"metrics": c_metrics, "runtime": ct.elapsed, "energy": c_energy},
    }


if __name__ == "__main__":
    run()
