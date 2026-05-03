# Section II. Related Work (Draft for Paper 1 — Hybrid QC+AI)

Organized into four thematic streams, each closing with the gap our framework addresses.

---

## II-A. Noisy Intermediate-Scale Quantum Computing

The current era of quantum hardware is characterized by tens-to-hundreds of
noisy qubits without error correction, formally termed the **Noisy Intermediate-
Scale Quantum (NISQ)** era by Preskill [2]. Google's 53-qubit Sycamore
demonstration [3] established that near-term devices can execute circuits
beyond classical brute-force simulation, yet the practical utility of such
devices for real applications remains constrained by decoherence, limited
connectivity, and shot noise. Bharti *et al.* [4] survey the algorithmic
landscape of NISQ computing and argue that **hybrid quantum-classical
workflows**—not pure quantum algorithms—are the only tractable path to
near-term quantum advantage. This constraint directly motivates our design:
the quantum co-processor is used only where it offers expressive power
unavailable to classical hardware, while classical resources handle data
preparation, optimization loops, and post-processing.

## II-B. Quantum Machine Learning and Kernel Methods

Biamonte *et al.* [5] provide the foundational survey of Quantum Machine
Learning (QML), identifying kernel methods as one of the earliest candidates
for near-term quantum advantage. The seminal work of Havlíček *et al.* [6]
introduces the **ZZ feature map**—a parameterized circuit that embeds
classical data into an exponentially large Hilbert space—and shows that the
resulting quantum kernel can be estimated on NISQ hardware and used inside a
classical Support Vector Machine [22]. Schuld and Killoran [7] formalize the
"feature Hilbert space" view, proving that any quantum circuit with a
data-dependent unitary implicitly defines a kernel. More recently, Huang
*et al.* [8] delineate *when* quantum kernels outperform classical ones,
showing that advantage depends on geometric properties of the data. Our
QSVM case study uses the exact ZZ feature map of [6], but embeds it in a
heterogeneous pipeline where the GPU computes classical RBF baselines in
parallel with QPU kernel-element estimation—an execution pattern not
analyzed in prior QML work.

## II-C. Variational and Search-Based Quantum Algorithms

Two quantum algorithms dominate cybersecurity-relevant NISQ research.
The **Quantum Approximate Optimization Algorithm (QAOA)**, proposed by
Farhi, Goldstone, and Gutmann [9], targets combinatorial problems such as
MaxCut by alternating cost and mixer Hamiltonians over *p* variational
layers. Zhou *et al.* [11] analyze its performance scaling, and Cerezo
*et al.* [10] survey the broader family of Variational Quantum Algorithms
(VQAs), emphasizing that every VQA is structurally hybrid: a classical
optimizer (e.g., COBYLA) iteratively updates circuit parameters from
measurement statistics. McClean *et al.* [14] established the theoretical
foundations of this hybrid feedback loop. Separately, **Grover's algorithm**
[12] offers a provable quadratic speedup for unstructured search, and
Grassl *et al.* [13] quantify its impact on symmetric-key cryptanalysis,
motivating the post-quantum migration of AES-128 to AES-256. Our QAOA and
Grover case studies invoke these algorithms not to reproduce their
asymptotic claims—infeasible at NISQ scale—but to **exercise the
orchestration layer under realistic variational and amplitude-amplification
workloads**.

## II-D. Hybrid Heterogeneous Computing and Energy Accounting

Callison and Chancellor [15] explicitly argue that NISQ-era progress
depends on tight integration between classical and quantum resources.
Humble *et al.* [16] go further and position quantum processing units as
**accelerators within High-Performance Computing (HPC) systems**, analogous
to how GPUs were integrated into scientific workflows a decade earlier.
This vision—QPUs as one tier of a heterogeneous compute hierarchy—is the
architectural frame for our work. Yet the existing literature focuses on
*offloading protocols* (how to dispatch a circuit) rather than
**end-to-end workload characterization** across a full CPU+GPU+QPU pipeline.
In parallel, Auffèves [23] has called for a **Quantum Energy Initiative**,
arguing that energy per computation, not just runtime, must become a
first-class metric for NISQ systems. Strubell *et al.* [24] made an
analogous case for classical deep learning. No prior work, to our
knowledge, reports **per-unit energy and runtime accounting** for a single
hybrid cybersecurity workload spanning all three tiers.

## II-E. Quantum Computing for Cybersecurity

Kilber *et al.* [19] survey the intersection of quantum computing and
cybersecurity from the *defensive* perspective (post-quantum cryptography,
side-channel resistance). Complementary work has begun to explore *offensive*
and *detective* uses of quantum computing: Payares and Martínez-Santos [18]
benchmark QSVMs on DDoS intrusion detection, and earlier cyber-ML surveys
[17] motivate the underlying detection-and-response workflow. Standard
evaluation datasets for intrusion detection include NSL-KDD [20] and
CICIDS2017 [21]; while our proof-of-concept uses synthetic data sized to
NISQ constraints, Section VI discusses a validation roadmap on both.

## II-F. Research Gap

Summarizing the four streams above:

1. NISQ literature establishes that **hybrid** is the only near-term path.
2. QML, QAOA, and Grover literature focus on **individual algorithms**
   in isolation, typically benchmarked on noiseless simulators.
3. Heterogeneous-computing literature proposes **QPU-in-HPC** as an
   architectural direction but stops short of measured per-unit workloads.
4. Energy-aware computing literature [23], [24] identifies energy as the
   missing metric.

**Our contribution sits precisely at this intersection:** an orchestration
framework that (i) routes three representative cybersecurity workloads
across CPU, GPU, and QPU tiers, (ii) measures runtime and energy at the
granularity of individual tasks, and (iii) makes the resulting
characterization reproducible via open-source code and a documented task
graph. To our knowledge, no prior study reports such an end-to-end
measurement for a cybersecurity pipeline.
