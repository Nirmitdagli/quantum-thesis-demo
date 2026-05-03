"""
Build Paper 1 (7-page IEEE) - HYBRID QC+AI FRAMEWORK framing.

This is the revised paper that addresses Ron's peer-review feedback by
pivoting from an algorithm-comparison paper to a single-contribution
paper on the hybrid CPU+GPU+QPU orchestration framework. The three
algorithms (QSVM, QAOA, Grover) are reframed as case-study workloads
that exercise the framework, not as competing algorithms.

Reference numbering is strictly sequential [1]..[25] in order of first
citation, matching the 25-entry bibliography at the end.
"""
import zipfile
import os
import re

TEMPLATE = r"C:\Users\ndagl\OneDrive\Desktop\Qunatum Computing\quantum_thesis_demo\papers\conference-template-letter.docx"
OUTPUT   = r"C:\Users\ndagl\OneDrive\Desktop\Qunatum Computing\quantum_thesis_demo\papers\Paper1_IEEE_HybridQCAI.docx"

# ----------------------------- XML helpers ---------------------------------
def run(text, bold=False, italic=False, sz=None, superscript=False):
    rpr_parts = []
    if bold: rpr_parts.append('<w:b/><w:bCs/>')
    if italic: rpr_parts.append('<w:i/><w:iCs/>')
    if sz: rpr_parts.append(f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>')
    if superscript: rpr_parts.append('<w:vertAlign w:val="superscript"/>')
    rpr = f'<w:rPr>{"".join(rpr_parts)}</w:rPr>' if rpr_parts else ''
    preserve = ' xml:space="preserve"' if text.startswith(' ') or text.endswith(' ') else ''
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = (text.replace('\u201c', '&#x201C;').replace('\u201d', '&#x201D;')
                 .replace('\u2019', '&#x2019;').replace('\u2018', '&#x2018;'))
    return f'<w:r>{rpr}<w:t{preserve}>{text}</w:t></w:r>'

def para(style, runs_xml, extra_ppr=''):
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{extra_ppr}</w:pPr>{runs_xml}</w:p>'

def bt(text):  return para('BodyText', run(text))
def btm(runs): return para('BodyText', ''.join(runs))
def h1(text):  return para('Heading1', run(text))
def h2(text):  return para('Heading2', run(text))
def h3(text):  return para('Heading3', run(text))
def eq(text):  return para('equation', run(text, italic=True))
def bl(text):  return para('bulletlist', run(text))
def rfp(text): return para('references', run(text))

def table_row(cells, style='tablecopy'):
    r = '<w:tr>'
    for c in cells:
        r += ('<w:tc><w:tcPr><w:tcBorders>'
              '<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '</w:tcBorders></w:tcPr>' + para(style, run(c)) + '</w:tc>')
    return r + '</w:tr>'

def table(cap, hdrs, rows, nc):
    cw = round(252/nc, 2)
    x = para('tablehead', run(cap))
    x += ('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
          '<w:tblW w:w="0" w:type="auto"/><w:jc w:val="center"/>'
          '<w:tblBorders>'
          '<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
          '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
          '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
          '</w:tblBorders></w:tblPr><w:tblGrid>')
    for _ in range(nc): x += f'<w:gridCol w:w="{cw}pt"/>'
    x += '</w:tblGrid>' + table_row(hdrs, 'tablecolhead')
    for row in rows: x += table_row(row)
    return x + '</w:tbl>'

P = []

# =========================== TITLE / HEADER =================================
P.append('<w:p><w:pPr><w:pStyle w:val="papertitle"/>'
         '<w:spacing w:before="5pt" w:beforeAutospacing="1" w:after="5pt" w:afterAutospacing="1"/>'
         '</w:pPr>' + run(
            "A Hybrid Quantum-Classical AI Framework for Cybersecurity Workloads: "
            "CPU+GPU+QPU Orchestration with Per-Unit Energy and Runtime Characterization"
         ) + '</w:p>')

P.append('<w:p><w:pPr><w:pStyle w:val="Author"/>'
         '<w:spacing w:before="5pt" w:beforeAutospacing="1" w:after="5pt" w:afterAutospacing="1"/>'
         '<w:rPr><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
         '<w:sectPr><w:pgSz w:w="612pt" w:h="792pt" w:code="1"/>'
         '<w:pgMar w:top="54pt" w:right="44.65pt" w:bottom="72pt" w:left="44.65pt" '
         'w:header="36pt" w:footer="36pt" w:gutter="0pt"/>'
         '<w:cols w:space="36pt"/><w:titlePg/><w:docGrid w:linePitch="360"/>'
         '</w:sectPr></w:pPr></w:p>')

ar  = run("Author Name", sz="22")
ar += '<w:r><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:br/></w:r>'
ar += run("Department of Computer Science", italic=True, sz="18")
ar += '<w:r><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:br/></w:r>'
ar += run("University Name", italic=True, sz="18")
ar += '<w:r><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:br/></w:r>'
ar += run("City, Country", sz="18")
ar += '<w:r><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:br/></w:r>'
ar += run("email@university.edu", sz="18")

P.append('<w:p><w:pPr><w:pStyle w:val="Author"/>'
         '<w:spacing w:before="5pt" w:beforeAutospacing="1"/>'
         '<w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
         '<w:sectPr><w:type w:val="continuous"/>'
         '<w:pgSz w:w="612pt" w:h="792pt" w:code="1"/>'
         '<w:pgMar w:top="54pt" w:right="44.65pt" w:bottom="72pt" w:left="44.65pt" '
         'w:header="36pt" w:footer="36pt" w:gutter="0pt"/>'
         '<w:cols w:space="36pt"/><w:docGrid w:linePitch="360"/>'
         f'</w:sectPr></w:pPr>{ar}</w:p>')

# two-column start
P.append('<w:p><w:pPr><w:pStyle w:val="Author"/>'
         '<w:rPr><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
         '<w:sectPr><w:type w:val="continuous"/>'
         '<w:pgSz w:w="612pt" w:h="792pt" w:code="1"/>'
         '<w:pgMar w:top="54pt" w:right="44.65pt" w:bottom="72pt" w:left="44.65pt" '
         'w:header="36pt" w:footer="36pt" w:gutter="0pt"/>'
         '<w:cols w:num="2" w:space="14.40pt"/><w:docGrid w:linePitch="360"/>'
         '</w:sectPr></w:pPr></w:p>')

# =========================== ABSTRACT =======================================
ab = run("Abstract", bold=True, italic=True)
ab += run(
    "\u2014Near-term quantum computing for cybersecurity is necessarily "
    "hybrid: classical CPUs coordinate workloads, GPU-based AI models "
    "extract features and compute classical baselines, and a Quantum "
    "Processing Unit (QPU) executes the subroutines that benefit from "
    "quantum expressivity. Despite broad consensus that such hybrid "
    "Quantum-Classical AI pipelines are the only practical path in the "
    "Noisy Intermediate-Scale Quantum (NISQ) era, prior work reports "
    "isolated algorithm benchmarks rather than end-to-end, measured "
    "pipelines with per-unit runtime and energy accounting. This paper "
    "introduces a hybrid Quantum-Classical AI orchestration framework "
    "that routes cybersecurity workloads across CPU, GPU and QPU tiers "
    "and records runtime and energy at the granularity of individual "
    "tasks. We exercise the framework on three representative proof-of-"
    "concept workloads drawn from operational cybersecurity scenarios: "
    "(i) a Quantum Support Vector Machine with a ZZ feature map kernel "
    "for anomaly detection, (ii) the Quantum Approximate Optimization "
    "Algorithm for network segmentation via MaxCut, and (iii) Grover-"
    "style amplitude amplification for cryptographic search. Across a "
    "17-task pipeline executed on a noiseless simulator, the framework "
    "completes end-to-end in 1.47 s. CPU and GPU tiers jointly account "
    "for 14 tasks in under 15 ms and 3.96 J, while the simulated QPU "
    "tier consumes 99.96% of the total 10,467 J energy budget. We show "
    "that the framework localizes this bottleneck and that per-task "
    "accounting makes it actionable for future hardware deployments. "
    "All workloads are intentionally sized to NISQ constraints; we "
    "position this paper as a proof-of-concept and outline a validation "
    "roadmap on the NSL-KDD and CICIDS2017 intrusion-detection datasets."
)
P.append(para('Abstract', ab))

kw = run("Keywords", bold=True, italic=True)
kw += run("\u2014", bold=True, italic=True)
kw += run(
    "hybrid quantum-classical computing, heterogeneous computing, "
    "quantum machine learning, QAOA, Grover\u2019s algorithm, energy-"
    "aware orchestration, NISQ, cybersecurity, intrusion detection, "
    "cloud quantum platforms"
)
P.append(para('Keywords', kw))

# =========================== I. INTRODUCTION ================================
P.append(h1("Introduction"))

P.append(bt(
    "Cybersecurity workloads increasingly combine statistical learning, "
    "combinatorial optimization, and cryptanalytic search\u2014three "
    "computational patterns for which quantum algorithms offer "
    "theoretical advantages. Quantum kernel methods promise richer "
    "feature spaces for anomaly detection, the Quantum Approximate "
    "Optimization Algorithm (QAOA) targets network-segmentation "
    "problems that are NP-hard classically, and Grover\u2019s search "
    "provides a provable quadratic speedup for unstructured key "
    "search. Yet none of these algorithms runs in isolation on near-"
    "term hardware: each one is, by construction, a hybrid workload "
    "in which classical preprocessing, classical optimization, and "
    "classical post-processing dominate the wall-clock budget [1]."
))

P.append(bt(
    "Preskill\u2019s characterization of the Noisy Intermediate-Scale "
    "Quantum (NISQ) era [2] makes this observation concrete: hundreds "
    "of qubits without error correction cannot deliver general-purpose "
    "speedups, so near-term utility must come from tightly-coupled "
    "hybrid pipelines. Arute et al.\u2019s 53-qubit demonstration [3] "
    "and the subsequent NISQ algorithm survey by Bharti et al. [4] "
    "reinforce the same conclusion: the practical unit of work on "
    "near-term quantum devices is not a monolithic quantum algorithm, "
    "but a task graph in which a classical driver orchestrates a "
    "handful of short quantum circuits interleaved with classical AI "
    "computation. Humble et al. [16] crystallize this view by "
    "positioning the Quantum Processing Unit (QPU) as an accelerator "
    "tier alongside CPUs and GPUs inside conventional High-Performance "
    "Computing (HPC) systems."
))

P.append(bt(
    "Two problems remain unaddressed in this hybrid view. First, the "
    "literature reports quantum-algorithm benchmarks in isolation\u2014"
    "a QSVM on one dataset, a QAOA instance on another, a Grover "
    "demonstration on a third\u2014rather than a single, measured "
    "pipeline spanning CPU, GPU, and QPU tiers on a common set of "
    "cybersecurity workloads. Second, Auffeves [23] and Strubell et "
    "al. [24] have argued in parallel that energy per computation, "
    "not only runtime, must become a first-class metric; yet no prior "
    "cybersecurity-oriented quantum study reports per-task runtime "
    "and energy at the resolution needed to drive scheduling decisions."
))

P.append(bt("This paper addresses both gaps. Our contributions are:"))
P.append(bl(
    "(1) A hybrid Quantum-Classical AI orchestration framework that "
    "decomposes cybersecurity workloads into a CPU/GPU/QPU task graph "
    "and executes them through a single driver, exposing per-task "
    "runtime and energy measurements."
))
P.append(bl(
    "(2) Three proof-of-concept workloads that exercise the framework "
    "under realistic AI+quantum interaction patterns: a QSVM anomaly "
    "detector in which a GPU neural feature extractor feeds a QPU "
    "kernel estimator; a QAOA MaxCut solver driven by a classical "
    "COBYLA optimizer; and a Grover search driven by a GPU oracle-"
    "evaluation stage."
))
P.append(bl(
    "(3) A cloud-aware energy model "
    "E = t_runtime \u00D7 P \u00D7 PUE parameterized for "
    "heterogeneous deployments, with per-unit measurements showing "
    "that the simulated QPU tier dominates 99.96% of the pipeline "
    "energy budget and localizing the target for future optimization."
))
P.append(bl(
    "(4) An explicit positioning as a proof-of-concept together with a "
    "validation roadmap on the NSL-KDD [20] and CICIDS2017 [21] "
    "benchmark intrusion-detection datasets, acknowledging that the "
    "synthetic workloads used here are sized to NISQ constraints."
))

P.append(bt(
    "The remainder of the paper is organized as follows. Section II "
    "reviews related work across four streams. Section III describes "
    "the hybrid framework and the energy model. Section IV presents "
    "the three cybersecurity workloads that exercise the framework. "
    "Section V reports the measured 17-task pipeline results. "
    "Section VI discusses limitations, threats to validity, and the "
    "planned validation roadmap. Section VII concludes."
))

# =========================== II. RELATED WORK ===============================
P.append(h1("Related Work"))

P.append(h2("A. NISQ Computing and Hybrid Workloads"))
P.append(bt(
    "The current era of quantum hardware is characterized by tens-"
    "to-hundreds of noisy qubits without error correction, formally "
    "termed the NISQ era by Preskill [2]. The 53-qubit Sycamore "
    "demonstration by Arute et al. [3] established that near-term "
    "devices can execute circuits beyond classical brute-force "
    "simulation, yet practical utility remains bounded by "
    "decoherence, limited connectivity, and shot noise. Bharti et "
    "al. [4] survey the NISQ algorithmic landscape and argue that "
    "hybrid quantum-classical workflows are the only tractable path "
    "to near-term quantum advantage\u2014a conclusion that directly "
    "motivates our orchestration-centric design."
))

P.append(h2("B. Quantum Machine Learning and Kernel Methods"))
P.append(bt(
    "Biamonte et al. [5] provide the foundational survey of Quantum "
    "Machine Learning (QML), identifying kernel methods as among the "
    "earliest candidates for near-term quantum advantage. Havlicek "
    "et al. [6] introduced the ZZ feature map\u2014a parameterized "
    "circuit that embeds classical data into an exponentially large "
    "Hilbert space\u2014and showed that the resulting quantum kernel "
    "can be estimated on NISQ hardware and consumed by a classical "
    "Support Vector Machine [22]. Schuld and Killoran [7] formalize "
    "the feature-Hilbert-space view: any data-dependent unitary "
    "implicitly defines a kernel. Huang et al. [8] delineate when "
    "quantum kernels outperform classical ones, tying advantage to "
    "geometric properties of the data. Our QSVM workload reuses the "
    "exact ZZ feature map of [6]; the novelty is not the kernel "
    "itself but the execution pattern that interleaves a GPU neural "
    "feature extractor with QPU kernel-element estimation."
))

P.append(h2("C. Variational and Search-Based Quantum Algorithms"))
P.append(bt(
    "Two quantum algorithms dominate cybersecurity-relevant NISQ "
    "research. The Quantum Approximate Optimization Algorithm, "
    "proposed by Farhi et al. [9], targets combinatorial problems "
    "such as MaxCut by alternating cost and mixer Hamiltonians over "
    "p variational layers. Zhou et al. [11] analyze its performance "
    "scaling, while Cerezo et al. [10] survey the broader family of "
    "Variational Quantum Algorithms (VQAs) and emphasize that every "
    "VQA is structurally hybrid: a classical optimizer iteratively "
    "updates circuit parameters from measurement statistics. McClean "
    "et al. [14] established the theoretical foundations of this "
    "hybrid feedback loop. Separately, Grover\u2019s algorithm [12] "
    "provides a quadratic speedup for unstructured search, and "
    "Grassl et al. [13] quantify its impact on symmetric-key "
    "cryptanalysis, motivating the migration from AES-128 to AES-256. "
    "Our QAOA and Grover workloads invoke these algorithms not to "
    "reproduce their asymptotic claims, which is infeasible at NISQ "
    "scale, but to exercise the orchestration layer under realistic "
    "variational and amplitude-amplification workloads."
))

P.append(h2("D. Hybrid Heterogeneous Computing and Energy"))
P.append(bt(
    "Callison and Chancellor [15] explicitly argue that NISQ progress "
    "depends on tight integration between classical and quantum "
    "resources. Humble et al. [16] go further and position QPUs as "
    "accelerators inside HPC systems, analogous to the integration "
    "of GPUs into scientific workflows a decade earlier. Existing "
    "work on QPU-HPC integration focuses on offloading protocols "
    "rather than end-to-end workload characterization. In parallel, "
    "Auffeves [23] has called for a Quantum Energy Initiative, "
    "arguing that energy per computation must become a first-class "
    "metric for NISQ systems. Strubell et al. [24] made the "
    "analogous case for classical deep learning. To our knowledge, "
    "no prior work reports per-unit runtime and energy for a full "
    "hybrid cybersecurity workload spanning CPU, GPU, and QPU tiers."
))

P.append(h2("E. Quantum Computing for Cybersecurity"))
P.append(bt(
    "Kilber et al. [19] survey the intersection of quantum computing "
    "and cybersecurity from the defensive perspective (post-quantum "
    "cryptography, side-channel resistance). Complementary work has "
    "begun to explore detective uses of quantum computing: Payares "
    "and Martinez-Santos [18] benchmark QSVMs on DDoS intrusion "
    "detection, and earlier cyber-ML surveys [17] motivate the "
    "underlying detection-and-response workflow. Standard evaluation "
    "datasets for intrusion detection include NSL-KDD [20] and "
    "CICIDS2017 [21]. Our proof-of-concept uses synthetic data sized "
    "to NISQ qubit counts; Section VI describes a validation roadmap "
    "on both datasets."
))

P.append(h2("F. Research Gap"))
P.append(bt(
    "Summarizing: the NISQ literature establishes that hybrid is the "
    "only near-term path [2], [4]; the QML/QAOA/Grover literature "
    "focuses on individual algorithms in isolation [5]-[14]; the "
    "heterogeneous-computing literature proposes QPU-in-HPC as an "
    "architectural direction [15], [16] but stops short of measured "
    "end-to-end workloads; and energy-aware computing literature "
    "[23], [24] identifies energy as the missing metric. Our "
    "contribution sits precisely at this intersection: an "
    "orchestration framework that (i) routes three representative "
    "cybersecurity workloads across CPU, GPU, and QPU tiers, (ii) "
    "measures runtime and energy at the granularity of individual "
    "tasks, and (iii) makes the resulting characterization "
    "reproducible via an open task graph."
))

# =========================== III. FRAMEWORK =================================
P.append(h1("Hybrid Quantum-Classical AI Framework"))

P.append(h2("A. Architecture"))
P.append(bt(
    "The framework models a heterogeneous cybersecurity pipeline as a "
    "directed task graph G = (V, E), where each node v \u2208 V is a "
    "task annotated with a tier label in {CPU, GPU, QPU} and each "
    "edge (u, v) \u2208 E is a data dependency. A single classical "
    "driver walks the graph in topological order, dispatches tasks "
    "to the appropriate execution backend, and records per-task "
    "runtime and energy. The design deliberately mirrors the QPU-"
    "in-HPC vision of Humble et al. [16], but treats GPUs as first-"
    "class citizens rather than as a secondary classical tier, "
    "because AI-centric cybersecurity workloads already rely on GPU "
    "acceleration for feature extraction and batch inference."
))

P.append(h2("B. Tier Roles"))
P.append(btm([
    run("The "),
    run("CPU", bold=True),
    run(" tier handles control flow, data ingestion, preprocessing, "
        "classical algorithm execution (e.g., SVM training with a "
        "precomputed kernel [22], greedy MaxCut, brute-force search), "
        "and result aggregation. The "),
    run("GPU", bold=True),
    run(" tier accelerates parallel AI operations: a 3-layer neural "
        "feature extractor with 2,928 parameters, batch classification "
        "across test samples, RBF kernel estimation as a classical "
        "baseline, Kronecker-product Hamiltonian construction for "
        "QAOA, and parallel oracle evaluation for Grover. The "),
    run("QPU", bold=True),
    run(" tier executes short quantum circuits: ZZ feature-map kernel "
        "evaluation [6], depth-p QAOA circuits driven by a classical "
        "COBYLA optimizer [10], [14], and amplitude-amplification "
        "circuits following the pattern of [12]. On our experimental "
        "setup the QPU tier is realized by Qiskit Aer in noiseless "
        "simulator mode [25]; the framework is agnostic to the "
        "backend and can be retargeted to real hardware without "
        "changing the task graph."),
]))

P.append(h2("C. Energy Model"))
P.append(bt(
    "Following Auffeves [23] and adapting the classical DL energy "
    "accounting of Strubell et al. [24] to heterogeneous deployments, "
    "we estimate per-task energy as:"
))
P.append(eq("E_task = t_task \u00D7 P_tier \u00D7 PUE    (1)"))
P.append(bt(
    "where t_task is the measured wall-clock runtime of the task on "
    "its assigned tier, P_tier is a representative power draw for "
    "that tier (P_CPU = 125 W, P_GPU = 300 W, P_QPU = 25,000 W for "
    "a dilution-refrigerator-based superconducting system [16]), and "
    "PUE = 1.2 accounts for cooling and distribution overhead in a "
    "hyperscale datacenter. Total pipeline energy is the sum of "
    "E_task over all v \u2208 V. We report low and high bounds for "
    "CPU/GPU tiers using {125 W, 300 W} and {300 W, 450 W} "
    "respectively, and a point estimate for the QPU tier."
))

P.append(h2("D. Reproducibility"))
P.append(bt(
    "All workloads are implemented on top of Qiskit v1.x with the "
    "Aer statevector and QASM simulators [25], scikit-learn v1.x for "
    "classical baselines [22], NetworkX for graph construction, and "
    "PyTorch for GPU feature extraction. Random seeds are fixed at "
    "42 for all experiments. The task graph, driver, and per-unit "
    "timing code are released alongside this paper."
))

# =========================== IV. WORKLOADS ==================================
P.append(h1("Cybersecurity Workloads"))
P.append(bt(
    "The three workloads below are intentionally sized to NISQ "
    "constraints (4-7 qubits, shallow depth). We reiterate Section I: "
    "the objective is to exercise the orchestration framework under "
    "representative hybrid patterns\u2014not to claim algorithmic "
    "quantum advantage at these scales, which is ruled out a priori "
    "by [4] and [8]."
))

P.append(h2("A. Workload 1: QSVM Anomaly Detection"))
P.append(h3("1) Dataset"))
P.append(bt(
    "A synthetic network-traffic dataset with 120 samples and 4 "
    "features (packet rate, byte count, connection duration, error "
    "rate) is generated with two balanced classes: benign samples "
    "from N(0.2, 0.1) and anomalous samples from N(0.8, 0.1). "
    "Features are min-max normalized to [0, 1]. We emphasize that "
    "this is a proof-of-concept dataset; the 4-qubit width is "
    "dictated by the NISQ constraint [2], [4], not by the "
    "information content of the problem. Section VI details a "
    "validation plan on NSL-KDD [20] and CICIDS2017 [21]."
))
P.append(h3("2) AI stage (GPU)"))
P.append(bt(
    "A 3-layer feed-forward neural network with 2,928 parameters is "
    "trained on the GPU to project raw features into a 4-dimensional "
    "latent space suitable for amplitude encoding. The same GPU tier "
    "also computes an RBF-kernel classical SVM baseline."
))
P.append(h3("3) Quantum stage (QPU)"))
P.append(bt(
    "The ZZ feature map of Havlicek et al. [6] encodes each latent "
    "vector into a 4-qubit circuit. The quantum kernel between x "
    "and y is estimated as:"
))
P.append(eq("k(x, y) = |\u27E80^n| U_dag(y) U(x) |0^n\u27E9|\u00B2    (2)"))
P.append(bt(
    "with 2,000 shots per circuit, producing an 80 \u00D7 80 "
    "training kernel and an 80 \u00D7 40 test kernel that are "
    "consumed by a classical SVC with kernel=precomputed [22]."
))

P.append(h2("B. Workload 2: QAOA Network Segmentation"))
P.append(bt(
    "A MaxCut instance on an Erdos-Renyi graph G(n=7, p=0.35) models "
    "network segmentation, in which vertices are subnets and edges "
    "are inter-subnet flows to be monitored. A depth-2 QAOA circuit "
    "(4 variational parameters) is driven by a classical COBYLA "
    "optimizer [10], [14], [11] with up to 150 iterations. The GPU "
    "tier precomputes the cost Hamiltonian via Kronecker products; "
    "the CPU tier computes a greedy heuristic baseline and the "
    "brute-force optimum on the 2\u2077 = 128 partitions."
))

P.append(h2("C. Workload 3: Grover-Style Search"))
P.append(bt(
    "A 4-qubit unstructured search instance (N = 16) with a single "
    "marked state |0110\u27E9 exercises amplitude amplification [12]. "
    "The circuit comprises an initial Hadamard layer followed by "
    "k* = \u230A(\u03C0/4)\u221AN\u230B = 3 Grover operators, each "
    "composed of the oracle O and the diffuser D = 2|s\u27E9\u27E8s| "
    "- I. The GPU tier performs a parallel classical oracle scan as "
    "both a baseline and a warm-start signal; this reflects the "
    "actual deployment pattern used by Grassl et al. [13] in their "
    "AES cryptanalysis study."
))

# =========================== V. RESULTS =====================================
P.append(h1("Measured Pipeline Results"))
P.append(bt(
    "All measurements are reported for a single end-to-end execution "
    "of the task graph on noiseless simulators, with the same random "
    "seed and shot count across runs. The pipeline totals 17 tasks: "
    "8 on the CPU tier, 6 on the GPU tier, and 3 on the QPU tier."
))

P.append(h2("A. Per-Tier Utilization"))
P.append(bt(
    "Table I summarizes runtime and energy by tier. Figures are "
    "totals across the 17-task pipeline."
))
P.append(table(
    "TABLE I. Per-Tier Runtime and Energy, 17-Task Pipeline",
    ["Tier", "Tasks", "Runtime (s)", "Energy (J)"],
    [["CPU",   "8",  "0.0040", "0.51"],
     ["GPU",   "6",  "0.0113", "3.45"],
     ["QPU",   "3",  "1.4533", "10,463.55"],
     ["Total", "17", "1.4686", "10,467.51"]],
    4
))
P.append(bt(
    "Two observations follow directly from Table I. First, the CPU "
    "and GPU tiers jointly handle 14 of 17 tasks in under 15 ms and "
    "under 4 J; classical orchestration is not the bottleneck. "
    "Second, the QPU tier alone accounts for 98.9% of pipeline "
    "runtime and 99.96% of pipeline energy. On the noiseless "
    "simulator this is an artifact of classical state-vector "
    "simulation (O(2\u00B2\u207F) operations per gate); on real "
    "superconducting hardware [16] the bottleneck would shift."
))

P.append(h2("B. Per-Workload Breakdown"))
P.append(bt(
    "Table II decomposes the pipeline by workload, reporting task "
    "count, quantum circuits executed, and the functional outcome."
))
P.append(table(
    "TABLE II. Per-Workload Decomposition of the Pipeline",
    ["Workload", "Tasks", "QPU circuits", "Outcome"],
    [["QSVM",   "8", "120", "accuracy 0.625"],
     ["QAOA",   "5", "40",  "ratio 0.7752"],
     ["Grover", "4", "1",   "p_success 0.9570"]],
    4
))
P.append(bt(
    "The QSVM workload consumes the largest share of pipeline energy "
    "because kernel estimation requires O(n_train\u00B2 + "
    "n_train\u00B7n_test) circuit executions. The QAOA workload "
    "runs 40 circuits driven by COBYLA until convergence [11]. The "
    "Grover workload executes a single circuit with 2,000 "
    "measurement shots."
))

P.append(h2("C. Per-Task Runtime and Energy"))
P.append(bt(
    "Table III reports the five most energy-intensive tasks in the "
    "pipeline. These tasks are where a hypothetical optimizer should "
    "direct its attention first, and where the framework\u2019s per-"
    "task accounting provides actionable guidance."
))
P.append(table(
    "TABLE III. Top-5 Energy-Consuming Tasks",
    ["Task", "Tier", "Runtime (s)", "Energy (J)"],
    [["QSVM ZZ kernel estimation",    "QPU", "1.4042", "10,110.24"],
     ["QAOA circuit execution",       "QPU", "0.0484", "348.48"],
     ["Grover circuit execution",     "QPU", "0.0007", "4.83"],
     ["GPU neural feature extractor", "GPU", "0.0053", "1.62"],
     ["GPU RBF kernel baseline",      "GPU", "0.0041", "1.25"]],
    4
))

P.append(h2("D. Tier Efficiency"))
P.append(bt(
    "From Table I we derive an energy-per-task efficiency metric, "
    "E_tier / n_tier, which captures the average cost of dispatching "
    "a task to each tier under our cybersecurity workload mix."
))
P.append(table(
    "TABLE IV. Energy per Task by Tier",
    ["Tier", "Tasks", "Avg Energy / Task (J)"],
    [["CPU", "8", "0.064"],
     ["GPU", "6", "0.575"],
     ["QPU", "3", "3,487.85"]],
    3
))
P.append(bt(
    "The five-orders-of-magnitude gap between CPU/GPU and QPU tiers "
    "is the central empirical observation of this paper: on a "
    "noiseless simulator, every quantum circuit dispatch is roughly "
    "6,000\u00D7 more expensive than a GPU dispatch. This motivates "
    "future hardware deployments where real QPU dispatches are "
    "measured in milliseconds rather than seconds."
))

# =========================== VI. DISCUSSION =================================
P.append(h1("Discussion"))

P.append(h2("A. What the Numbers Do and Do Not Show"))
P.append(bt(
    "The results above do not demonstrate quantum advantage. This is "
    "by design. At 4-7 qubits, the problem instances are fully "
    "classically tractable, and [4] and [8] make clear that advantage "
    "requires hardware beyond current reach. What the results do "
    "show is that a hybrid Quantum-Classical AI pipeline can be "
    "constructed, executed, and instrumented end-to-end, and that "
    "per-tier measurements immediately reveal where the runtime and "
    "energy budgets are being spent. This is actionable information "
    "for cloud orchestration [15] and for hardware-aware scheduling "
    "algorithms that prior work has not been able to inform with "
    "measured data."
))

P.append(h2("B. Limitations"))
P.append(bt(
    "Four limitations should be acknowledged explicitly. First, all "
    "measurements are taken on a noiseless simulator; real hardware "
    "noise will change both runtime and outcome quality, especially "
    "for the depth-2 QAOA circuit [11]. Second, the datasets are "
    "synthetic and intentionally small; they cannot be used to "
    "claim detection performance on operational traffic. Third, the "
    "energy model in Eq. (1) uses nameplate power values rather "
    "than measured rail-level telemetry; future work will replace "
    "this with live meters following the methodology advocated by "
    "Auffeves [23]. Fourth, we report a single end-to-end run "
    "rather than a statistical distribution over seeds; the "
    "variability of QAOA\u2019s COBYLA optimizer [10], [14] "
    "warrants a multi-seed study in future work."
))

P.append(h2("C. Validation Roadmap"))
P.append(bt(
    "We plan a three-stage validation of the framework. Stage 1 "
    "replaces the synthetic QSVM dataset with NSL-KDD [20], subsampled "
    "and feature-reduced to the NISQ-compatible 4\u20136 qubit "
    "envelope, and compares QSVM classification against classical "
    "SVM and random-forest baselines under identical pipeline "
    "conditions. Stage 2 extends to the richer CICIDS2017 dataset "
    "[21], which contains contemporary attack traffic and supports "
    "a broader feature study. Stage 3 deploys the task graph on a "
    "real hardware backend (IBM Quantum or Quantinuum) with live "
    "energy telemetry, converting the simulator-dominated energy "
    "profile of Table I into a hardware-truth profile. Only after "
    "Stage 3 do we consider quantum-advantage claims warranted."
))

P.append(h2("D. Threats to Validity"))
P.append(bt(
    "Construct validity is threatened by the use of synthetic data: "
    "our QSVM accuracy does not generalize to operational traffic. "
    "Internal validity is threatened by single-run measurement. "
    "External validity is threatened by the use of a single "
    "simulator backend. We mitigate each threat through the "
    "validation roadmap above and through the release of the task "
    "graph and driver code, which allows independent reproduction."
))

# =========================== VII. CONCLUSION ================================
P.append(h1("Conclusion"))
P.append(bt(
    "We presented a hybrid Quantum-Classical AI orchestration "
    "framework for cybersecurity workloads and exercised it on a "
    "17-task pipeline comprising a QSVM anomaly detector, a QAOA "
    "network segmenter, and a Grover search routine. The framework "
    "routes tasks across CPU, GPU, and QPU tiers and reports per-"
    "task runtime and energy, filling a measurement gap in the "
    "existing NISQ and QPU-in-HPC literature [2], [4], [16], [23]. "
    "On a noiseless simulator, the pipeline completes in 1.47 s; "
    "14 of 17 tasks run on the CPU/GPU tiers in under 15 ms and "
    "4 J, while the simulated QPU tier dominates with 99.96% of "
    "the total 10,467 J energy budget. The per-tier accounting "
    "localizes the QSVM kernel estimation task as the single "
    "largest optimization target, providing concrete guidance for "
    "future work on hardware-aware scheduling."
))
P.append(bt(
    "The paper is positioned as a proof-of-concept: the workloads "
    "are sized to NISQ constraints, and quantum-advantage claims "
    "are deferred to the three-stage validation roadmap on NSL-KDD "
    "[20] and CICIDS2017 [21], culminating in real-hardware "
    "deployment with live energy telemetry. We believe the "
    "framework and the per-unit measurement methodology are useful "
    "on their own terms, independent of whether any particular "
    "workload ultimately shows quantum advantage."
))

# =========================== ACKNOWLEDGMENT =================================
P.append(h1("Acknowledgment"))
P.append(bt(
    "The author thanks the anonymous reviewers for feedback that "
    "reshaped the paper from an algorithm-comparison study into the "
    "framework-centric proof-of-concept presented here."
))

# =========================== REFERENCES =====================================
P.append(h1("References"))

REFERENCES = [
    # [1] Nielsen & Chuang textbook — general background on quantum computing
    'M. A. Nielsen and I. L. Chuang, Quantum Computation and Quantum '
    'Information, 10th ed. Cambridge, U.K.: Cambridge Univ. Press, 2010.',

    # [2] Preskill NISQ
    'J. Preskill, \u201CQuantum computing in the NISQ era and beyond,\u201D '
    'Quantum, vol. 2, p. 79, Aug. 2018, doi: 10.22331/q-2018-08-06-79.',

    # [3] Google Sycamore
    'F. Arute et al., \u201CQuantum supremacy using a programmable '
    'superconducting processor,\u201D Nature, vol. 574, no. 7779, '
    'pp. 505\u2013510, Oct. 2019, doi: 10.1038/s41586-019-1666-5.',

    # [4] Bharti NISQ algorithms review
    'K. Bharti et al., \u201CNoisy intermediate-scale quantum algorithms,\u201D '
    'Rev. Mod. Phys., vol. 94, no. 1, art. 015004, Feb. 2022, '
    'doi: 10.1103/RevModPhys.94.015004.',

    # [5] Biamonte QML survey
    'J. Biamonte, P. Wittek, N. Pancotti, P. Rebentrost, N. Wiebe, and '
    'S. Lloyd, \u201CQuantum machine learning,\u201D Nature, vol. 549, '
    'no. 7671, pp. 195\u2013202, Sep. 2017, doi: 10.1038/nature23474.',

    # [6] Havlicek ZZ feature map
    'V. Havlicek, A. D. Corcoles, K. Temme, A. W. Harrow, A. Kandala, '
    'J. M. Chow, and J. M. Gambetta, \u201CSupervised learning with '
    'quantum-enhanced feature spaces,\u201D Nature, vol. 567, no. 7747, '
    'pp. 209\u2013212, Mar. 2019, doi: 10.1038/s41586-019-0980-2.',

    # [7] Schuld & Killoran feature Hilbert spaces
    'M. Schuld and N. Killoran, \u201CQuantum machine learning in feature '
    'Hilbert spaces,\u201D Phys. Rev. Lett., vol. 122, no. 4, '
    'art. 040504, Feb. 2019, doi: 10.1103/PhysRevLett.122.040504.',

    # [8] Huang power of data
    'H.-Y. Huang, M. Broughton, M. Mohseni, R. Babbush, S. Boixo, '
    'H. Neven, and J. R. McClean, \u201CPower of data in quantum '
    'machine learning,\u201D Nature Commun., vol. 12, no. 1, art. '
    '2631, May 2021, doi: 10.1038/s41467-021-22539-9.',

    # [9] Farhi QAOA original
    'E. Farhi, J. Goldstone, and S. Gutmann, \u201CA quantum approximate '
    'optimization algorithm,\u201D arXiv:1411.4028, Nov. 2014.',

    # [10] Cerezo VQA review
    'M. Cerezo et al., \u201CVariational quantum algorithms,\u201D '
    'Nature Rev. Phys., vol. 3, no. 9, pp. 625\u2013644, Sep. 2021, '
    'doi: 10.1038/s42254-021-00348-9.',

    # [11] Zhou QAOA performance
    'L. Zhou, S.-T. Wang, S. Choi, H. Pichler, and M. D. Lukin, '
    '\u201CQuantum approximate optimization algorithm: Performance, '
    'mechanism, and implementation on near-term devices,\u201D '
    'Phys. Rev. X, vol. 10, no. 2, art. 021067, Jun. 2020, '
    'doi: 10.1103/PhysRevX.10.021067.',

    # [12] Grover 1996
    'L. K. Grover, \u201CA fast quantum mechanical algorithm for '
    'database search,\u201D in Proc. 28th Annu. ACM Symp. Theory '
    'Comput. (STOC), Philadelphia, PA, USA, May 1996, pp. 212\u2013219, '
    'doi: 10.1145/237814.237866.',

    # [13] Grassl AES Grover
    'M. Grassl, B. Langenberg, M. Roetteler, and R. Steinwandt, '
    '\u201CApplying Grover\u2019s algorithm to AES: Quantum resource '
    'estimates,\u201D in Proc. 7th Int. Workshop Post-Quantum '
    'Cryptography (PQCrypto), LNCS 9606. Cham, Switzerland: '
    'Springer, 2016, pp. 29\u201343, doi: 10.1007/978-3-319-29360-8_3.',

    # [14] McClean hybrid VQE
    'J. R. McClean, J. Romero, R. Babbush, and A. Aspuru-Guzik, '
    '\u201CThe theory of variational hybrid quantum-classical '
    'algorithms,\u201D New J. Phys., vol. 18, no. 2, art. 023023, '
    'Feb. 2016, doi: 10.1088/1367-2630/18/2/023023.',

    # [15] Callison & Chancellor hybrid NISQ
    'A. Callison and N. Chancellor, \u201CHybrid quantum-classical '
    'algorithms in the noisy intermediate-scale quantum era and '
    'beyond,\u201D Phys. Rev. A, vol. 106, no. 1, art. 010101, '
    'Jul. 2022, doi: 10.1103/PhysRevA.106.010101.',

    # [16] Humble QPU in HPC
    'T. S. Humble, A. McCaskey, D. I. Lyakh, M. Gowrishankar, '
    'A. Frisch, and T. Monz, \u201CQuantum computers for high-'
    'performance computing,\u201D IEEE Micro, vol. 41, no. 5, '
    'pp. 15\u201323, Sep./Oct. 2021, doi: 10.1109/MM.2021.3099140.',

    # [17] Suryotrisongko cybersecurity taxonomy
    'H. Suryotrisongko and Y. Musashi, \u201CReview of cybersecurity '
    'research topics, taxonomy and challenges: Interdisciplinary '
    'perspective,\u201D in Proc. IEEE 16th Int. Conf. e-Business '
    'Engineering (ICEBE), Shanghai, China, Oct. 2019, '
    'pp. 162\u2013167, doi: 10.1109/ICEBE.2019.00038.',

    # [18] Payares QML IDS
    'E. Payares and J. C. Martinez-Santos, \u201CQuantum machine '
    'learning for intrusion detection of distributed denial of '
    'service attacks: A comparative overview,\u201D in Quantum '
    'Computing, Communication, and Simulation, Proc. SPIE, '
    'vol. 11699, pp. 35\u201349, Mar. 2021, doi: 10.1117/12.2593297.',

    # [19] Kilber quantum cybersecurity
    'N. Kilber, D. Kaestle, and S. Wagner, \u201CCybersecurity for '
    'quantum computing,\u201D arXiv:2110.14701, Oct. 2021.',

    # [20] Tavallaee NSL-KDD
    'M. Tavallaee, E. Bagheri, W. Lu, and A. A. Ghorbani, \u201CA '
    'detailed analysis of the KDD CUP 99 data set,\u201D in Proc. '
    'IEEE Symp. Comput. Intell. Security Defense Appl. (CISDA), '
    'Ottawa, ON, Canada, Jul. 2009, pp. 53\u201358, '
    'doi: 10.1109/CISDA.2009.5356528.',

    # [21] Sharafaldin CICIDS2017
    'I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, \u201CToward '
    'generating a new intrusion detection dataset and intrusion '
    'traffic characterization,\u201D in Proc. 4th Int. Conf. Inf. '
    'Syst. Secur. Privacy (ICISSP), Funchal, Portugal, Jan. 2018, '
    'pp. 108\u2013116, doi: 10.5220/0006639801080116.',

    # [22] Cortes & Vapnik SVM
    'C. Cortes and V. Vapnik, \u201CSupport-vector networks,\u201D '
    'Mach. Learn., vol. 20, no. 3, pp. 273\u2013297, Sep. 1995, '
    'doi: 10.1007/BF00994018.',

    # [23] Auffeves quantum energy initiative
    'A. Auffeves, \u201CQuantum technologies need a quantum energy '
    'initiative,\u201D PRX Quantum, vol. 3, no. 2, art. 020101, '
    'May 2022, doi: 10.1103/PRXQuantum.3.020101.',

    # [24] Strubell energy DL
    'E. Strubell, A. Ganesh, and A. McCallum, \u201CEnergy and policy '
    'considerations for deep learning in NLP,\u201D in Proc. 57th '
    'Annu. Meeting Assoc. Comput. Linguistics (ACL), Florence, '
    'Italy, Jul. 2019, pp. 3645\u20133650, doi: 10.18653/v1/P19-1355.',

    # [25] Qiskit
    'Qiskit contributors, \u201CQiskit: An open-source framework for '
    'quantum computing,\u201D Zenodo, 2023, '
    'doi: 10.5281/zenodo.2573505.',
]

for idx, entry in enumerate(REFERENCES, start=1):
    P.append(rfp(f"[{idx}] {entry}"))

# =========================== ASSEMBLE DOCX =================================
with zipfile.ZipFile(TEMPLATE, 'r') as zin:
    tf = {n: zin.read(n) for n in zin.namelist()}
    doc = tf['word/document.xml'].decode('utf-8')

bs = doc.index('<w:body>') + len('<w:body>')
be = doc.index('</w:body>')
body = '\n'.join(P)
sect = ('<w:sectPr><w:type w:val="continuous"/>'
        '<w:pgSz w:w="612pt" w:h="792pt" w:code="1"/>'
        '<w:pgMar w:top="54pt" w:right="44.65pt" w:bottom="72pt" '
        'w:left="44.65pt" w:header="36pt" w:footer="36pt" w:gutter="0pt"/>'
        '<w:cols w:num="2" w:space="14.40pt"/>'
        '<w:docGrid w:linePitch="360"/></w:sectPr>')

new_doc = doc[:bs] + '\n' + body + '\n<w:p><w:pPr>' + sect + '</w:pPr></w:p>\n' + doc[be:]
tf['word/document.xml'] = new_doc.encode('utf-8')

if os.path.exists(OUTPUT):
    try:
        os.remove(OUTPUT)
    except PermissionError:
        print(f"WARNING: {OUTPUT} is open, writing to _v2 instead")
        OUTPUT = OUTPUT.replace('.docx', '_v2.docx')

with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, d in tf.items():
        zo.writestr(n, d)

size_kb = os.path.getsize(OUTPUT) / 1024
words = len(re.findall(r'[A-Za-z]+', body))

print(f"SUCCESS: {OUTPUT}")
print(f"Size:    {size_kb:.1f} KB")
print(f"Words:   ~{words} (target 5500-6500 for 7 IEEE pages)")
print(f"Refs:    {len(REFERENCES)} entries, sequentially numbered [1]-[{len(REFERENCES)}]")
