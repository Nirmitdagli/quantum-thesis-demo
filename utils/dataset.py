"""Synthetic dataset generation for cybersecurity anomaly detection."""

import os
import sys
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from typing import Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def generate_anomaly_dataset(
    n_samples: int = config.DATASET_SIZE,
    n_features: int = 4,
    random_state: int = config.RANDOM_STATE,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate synthetic cybersecurity anomaly detection dataset.

    Normal traffic samples are centered near 0.2.
    Anomaly samples are centered near 0.8.
    Features are scaled to [0, 1] with MinMaxScaler.

    Returns:
        (X_train, X_test, y_train, y_test)
    """
    rng = np.random.RandomState(random_state)

    n_normal = n_samples // 2
    n_anomaly = n_samples - n_normal

    X_normal = rng.normal(loc=0.2, scale=0.1, size=(n_normal, n_features))
    X_anomaly = rng.normal(loc=0.8, scale=0.1, size=(n_anomaly, n_features))

    X = np.vstack([X_normal, X_anomaly])
    y = np.array([0] * n_normal + [1] * n_anomaly)

    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y,
        test_size=config.TEST_RATIO,
        random_state=random_state,
        stratify=y,
    )
    return X_train, X_test, y_train, y_test
