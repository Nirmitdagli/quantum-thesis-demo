"""Data Loader — provides real cybersecurity datasets for the HERO pipeline.

Primary:  KDD Cup 99 (10% subset) — 494K network connections, 22 attack types.
          Binary classification: normal (0) vs attack (1).
          We select top-4 PCA components and scale to [0, pi] for quantum encoding.

For the quantum kernel (QSVM), we use a small stratified subset (n_samples)
because ZZ feature-map kernel evaluation is O(n^2) in circuit count.
Classical baselines run on the FULL dataset for a fair accuracy comparison.

Citation:
  M. Tavallaee, E. Bagheri, W. Lu, and A. Ghorbani, "A detailed analysis
  of the KDD CUP 99 data set," in Proc. IEEE Symp. Comput. Intell. Security
  and Defense Appl. (CISDA), Ottawa, Canada, Jul. 2009, pp. 1-6.
"""

import numpy as np
from sklearn.datasets import fetch_kddcup99
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler, StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split


def load_kdd_data(n_quantum_samples: int = 120, n_classical_samples: int = 5000,
                  n_features_quantum: int = 4, random_state: int = 42):
    """Load KDD Cup 99, return both quantum-sized and classical-sized splits.

    Returns dict with:
      - X_train_q, X_test_q, y_train_q, y_test_q  (small, scaled [0, pi], 4 features)
      - X_train_c, X_test_c, y_train_c, y_test_c  (larger, original scale, 38 features)
      - feature_names, dataset_name, n_total
    """
    # Fetch dataset
    kdd = fetch_kddcup99(percent10=True, random_state=random_state)
    X_raw, y_raw = kdd.data, kdd.target

    # Keep only numeric features (38 of 41)
    numeric_cols = [i for i in range(X_raw.shape[1])
                    if isinstance(X_raw[0, i], (int, float, np.integer, np.floating))]
    X_num = X_raw[:, numeric_cols].astype(np.float64)

    # Binary label: 0 = normal, 1 = attack
    y_bin = np.array([0 if label == b'normal.' else 1 for label in y_raw])

    # Remove NaN / inf
    mask = np.isfinite(X_num).all(axis=1)
    X_num, y_bin = X_num[mask], y_bin[mask]

    # --- Classical subset (larger, for baselines) ---
    n_cl = min(n_classical_samples, len(X_num))
    idx_c = np.random.RandomState(random_state).choice(len(X_num), n_cl, replace=False)
    X_cl, y_cl = X_num[idx_c], y_bin[idx_c]

    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
        X_cl, y_cl, test_size=0.33, random_state=random_state, stratify=y_cl)

    # --- Quantum subset (small, PCA to 4, scale to [0, pi]) ---
    # Balanced sampling: equal normal and attack
    n_per_class = n_quantum_samples // 2
    idx_normal = np.where(y_bin == 0)[0]
    idx_attack = np.where(y_bin == 1)[0]
    rng = np.random.RandomState(random_state)
    sel_n = rng.choice(idx_normal, min(n_per_class, len(idx_normal)), replace=False)
    sel_a = rng.choice(idx_attack, min(n_per_class, len(idx_attack)), replace=False)
    sel = np.concatenate([sel_n, sel_a])
    rng.shuffle(sel)

    X_q_raw, y_q = X_num[sel], y_bin[sel]

    # Standardize before PCA (features have wildly different scales)
    std_scaler = StandardScaler()
    X_q_std = std_scaler.fit_transform(X_q_raw)

    # PCA to n_features_quantum dimensions
    pca = PCA(n_components=n_features_quantum, random_state=random_state)
    X_q_pca = pca.fit_transform(X_q_std)

    # Scale to [0, pi] for quantum encoding
    scaler = MinMaxScaler(feature_range=(0, np.pi))
    X_q_scaled = scaler.fit_transform(X_q_pca)

    X_train_q, X_test_q, y_train_q, y_test_q = train_test_split(
        X_q_scaled, y_q, test_size=0.33, random_state=random_state, stratify=y_q)

    return {
        # Quantum-sized (4 features, [0, pi])
        "X_train_q": X_train_q, "X_test_q": X_test_q,
        "y_train_q": y_train_q, "y_test_q": y_test_q,
        # Classical-sized (38 features, original scale)
        "X_train_c": X_train_c, "X_test_c": X_test_c,
        "y_train_c": y_train_c, "y_test_c": y_test_c,
        # Metadata
        "dataset_name": "KDD Cup 99 (10%)",
        "n_total": len(X_num),
        "n_quantum": len(X_q_scaled),
        "n_classical": n_cl,
        "n_features_original": len(numeric_cols),
        "n_features_quantum": n_features_quantum,
        "pca_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "class_balance_q": {
            "normal": int((y_q == 0).sum()),
            "attack": int((y_q == 1).sum()),
        },
        "class_balance_c": {
            "normal": int((y_cl == 0).sum()),
            "attack": int((y_cl == 1).sum()),
        },
    }


if __name__ == "__main__":
    data = load_kdd_data()
    print(f"Dataset: {data['dataset_name']}")
    print(f"Total samples: {data['n_total']:,}")
    print(f"Quantum split: train={len(data['X_train_q'])}, test={len(data['X_test_q'])}")
    print(f"Classical split: train={len(data['X_train_c'])}, test={len(data['X_test_c'])}")
    print(f"PCA variance explained: {[f'{v:.3f}' for v in data['pca_variance_ratio']]}")
    print(f"Class balance (quantum): {data['class_balance_q']}")
    print(f"Class balance (classical): {data['class_balance_c']}")
