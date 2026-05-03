"""Logging utility for recording experiment results to CSV."""

import os
import sys
import csv
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

FIELDNAMES = [
    "experiment",
    "algorithm",
    "backend",
    "qubits",
    "shots",
    "metric_primary",
    "metric_secondary",
    "runtime_seconds",
    "energy_low",
    "energy_high",
    "timestamp",
]


def log_result(
    experiment: str,
    algorithm: str,
    backend: str,
    qubits: int,
    shots: int,
    metric_primary: float,
    metric_secondary: float,
    runtime_seconds: float,
    energy_low: float,
    energy_high: float,
) -> None:
    """Append one result row to results.csv."""
    file_exists = os.path.isfile(config.RESULTS_CSV)
    with open(config.RESULTS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "experiment": experiment,
            "algorithm": algorithm,
            "backend": backend,
            "qubits": qubits,
            "shots": shots,
            "metric_primary": f"{metric_primary:.6f}",
            "metric_secondary": f"{metric_secondary:.6f}",
            "runtime_seconds": f"{runtime_seconds:.6f}",
            "energy_low": f"{energy_low:.2f}",
            "energy_high": f"{energy_high:.2f}",
            "timestamp": datetime.now().isoformat(),
        })


def clear_results() -> None:
    """Remove existing results file for a fresh run."""
    if os.path.isfile(config.RESULTS_CSV):
        os.remove(config.RESULTS_CSV)
