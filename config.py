"""Global configuration for quantum thesis demo experiments."""

import os

# Quantum simulation parameters
SHOTS = 2000
MAX_QUBITS = 12

# Energy model parameters (thesis model)
# Energy = Runtime x Power x PUE
POWER_LOW_W = 5000       # watts
POWER_HIGH_W = 25000     # watts
PUE = 1.2

# Dataset parameters
DATASET_SIZE = 120
TEST_RATIO = 0.33
RANDOM_STATE = 42

# QAOA parameters
QAOA_NODES = 7
QAOA_EDGE_PROB = 0.35
QAOA_DEPTH = 2

# Grover parameters
GROVER_QUBITS = 4
GROVER_SCALING_RANGE = range(2, 11)  # 2 to 10 qubits for scaling study

# File paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_CSV = os.path.join(PROJECT_DIR, "results.csv")
PLOTS_DIR = os.path.join(PROJECT_DIR, "analysis", "plots")
FINAL_TABLE_CSV = os.path.join(PROJECT_DIR, "final_results_table.csv")
FINAL_SUMMARY_TXT = os.path.join(PROJECT_DIR, "final_summary.txt")
