# HERO — Hybrid Quantum-AI Models for Cybersecurity on Cloud Platforms

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![Qiskit](https://img.shields.io/badge/quantum-Qiskit-purple.svg)](https://qiskit.org/)

> **Master's Thesis (May 2026)** by **Nirmit Dagli** at **Quinnipiac University**, Department of Computer Science.
> Advisor: Prof. Taskin · Committee: Prof. Kruti, Prof. Lin

A measurement framework for hybrid quantum-classical AI workloads on heterogeneous cloud platforms — **CPU + GPU + QPU** — with case studies in cybersecurity intrusion detection and molecular simulation.

---

## 🌐 Live Demos

| Resource | URL |
|---|---|
| **Companion Website** | https://nirmitdagli.github.io/quantum-thesis-demo/ |
| **Live Interactive Simulator** | https://nirmitdagli.github.io/quantum-thesis-demo/simulator.html |
| **Thesis PDF** | [`thesis/Thesis_Nirmit_Dagli_HERO.pdf`](thesis/Thesis_Nirmit_Dagli_HERO.pdf) |
| **Conference Paper (ISAIA 2026 submission)** | [`papers/HERO-S_ISAIA_main.pdf`](papers/HERO-S_ISAIA_main.pdf) |

---

## 🔑 Headline Findings

Two contrasting verdicts from 30-seed validation:

| Workload | Best classical | Best quantum | Energy gap |
|---|---|---|---|
| **Cybersecurity (KDD Cup 99)** | Random Forest, F1 = 0.998 | QSVM, F1 = 0.667 | **Classical wins by ~13,000×** |
| **Molecular sim (H₂ via VQE)** | Exact diagonalisation, 0.04 J | VQE, 29,833 J | Classical wins for H₂; **quantum wins at n > 50 qubits** (classical RAM wall) |

For cybersecurity workloads, classical Random Forest on a CPU costs **\$1.99 per million classifications**. The same workload on a quantum kernel via AWS Braket Rigetti costs **\$2,100,000 per million classifications**.

---

## 🚀 Quick Start (5 minutes)

```bash
git clone https://github.com/Nirmitdagli/quantum-thesis-demo.git
cd quantum-thesis-demo
pip install -r requirements.txt
python -m hybrid_simulation.run_hybrid
```

The full pipeline (5–10 minutes on a developer laptop) runs:

- 30-seed QSVM kernel evaluation on KDD Cup 99
- 30-seed QAOA MaxCut on synthetic graphs
- 30-seed Grover search benchmark
- 30-seed VQE for H₂ molecular ground state
- Multi-method classical baselines (SVM, RF, Gradient Boosting, KNN)
- Cloud-cost computation across AWS / IBM / Azure pricing

Outputs are written to `hybrid_simulation/output/`:

- `classifier_comparison.csv`, `multirun_stats.csv`, `vqe_multirun.csv`, `cloud_costs.csv`
- `plots/` — 15 publication-quality PNG figures
- `hybrid_summary.txt` — human-readable summary

---

## 🏗 Repository Structure

```
quantum_thesis_demo/
├── hybrid_simulation/        # HERO simulator
│   ├── data_loader.py        # KDD Cup 99 preprocessing
│   ├── cpu_engine.py         # SVM, RF, GBM, KNN baselines
│   ├── gpu_engine.py         # parallel kernels, neural features
│   ├── qpu_engine.py         # QSVM, QAOA, Grover (Qiskit Aer)
│   ├── vqe_workload.py       # VQE for H₂ molecular ground state
│   ├── orchestrator.py       # full pipeline + multi-run loops
│   ├── allocation_rule.py    # Algorithm 1 + Pareto selection
│   ├── cloud_costs.py        # 2026 AWS / IBM / Azure pricing
│   ├── visualize.py          # 15 publication figures
│   └── run_hybrid.py         # one-command entry point
├── papers/                   # IEEE conference paper (HERO-S)
├── thesis/                   # Master's thesis source + DOCX/PDF
├── website/                  # static companion website + live simulator
├── requirements.txt
└── LICENSE                   # MIT
```

---

## 📊 Algorithm 1 — Workload-Aware Tier Allocation

```
Input:  Workload W (type, size n, feature dim d), runs N=30
Output: Recommended tier t*, metrics, Pareto set

STEP 1 — ALLOCATE TIER
  if MOLECULAR_SIM:   t = QPU if n > 30 else CPU
  if CLASSICAL_ML:    t = CPU if d < 100 else (GPU if d < 10⁴ else MEASURE)
  if COMBINATORIAL:   t = CPU if n < 50 else QPU

STEP 2 — MEASURE on each tier (N=30 runs for statistics)
STEP 3 — AGGREGATE mean ± std for accuracy, latency, energy, cost
STEP 4 — PARETO SELECTION on (cost, energy, latency, -accuracy)
STEP 5 — ARGMIN over Pareto with user weights → t*
```

---

## 📚 Citation

If you use HERO in your work, please cite:

```bibtex
@mastersthesis{dagli2026hero,
  author  = {Dagli, Nirmit},
  title   = {Hybrid Quantum-AI Models for Cybersecurity on Cloud Platforms:
             Accuracy, Latency, and Energy},
  school  = {Quinnipiac University},
  year    = {2026},
  month   = {May},
  url     = {https://github.com/Nirmitdagli/quantum-thesis-demo}
}
```

---

## 📜 License

[MIT](LICENSE) — free to use, modify, and distribute. Contributions welcome via issues / pull requests.
