"""Classical RBF SVM baseline for cybersecurity anomaly detection."""

import numpy as np
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from typing import Dict, Tuple


def train_and_evaluate(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> Tuple[Dict[str, float], np.ndarray]:
    """Train classical RBF SVM and return metrics + confusion matrix."""
    svm = SVC(kernel="rbf", gamma="scale")
    svm.fit(X_train, y_train)
    y_pred = svm.predict(X_test)

    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred),
    }
    cm = confusion_matrix(y_test, y_pred)
    return metrics, cm
