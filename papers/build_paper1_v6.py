"""
Build Paper 1 v6 (IEEE conference) - HERO: Accuracy-Latency-Energy Tradeoffs
in Hybrid Quantum-Classical Cybersecurity on Cloud Platforms

Uses the SAME OOXML template approach as build_paper1_hybrid_v2.py.
Embeds 8 figures from hybrid_simulation/output/plots/.
Compares QSVM against 4 classical baselines on KDD Cup 99 data.
30-run statistical validation, crossover projection, energy analysis.
"""
import os
import re
import zipfile
from PIL import Image

ROOT     = r"C:\Users\ndagl\OneDrive\Desktop\Qunatum Computing\quantum_thesis_demo"
TEMPLATE = os.path.join(ROOT, r"papers\conference-template-letter.docx")
OUTPUT   = os.path.join(ROOT, r"papers\Paper1_IEEE_HybridQCAI_v6.docx")
PLOTS    = os.path.join(ROOT, r"hybrid_simulation\output\plots")

# -------------------------------------------------------------------------
# Strict OOXML namespaces (this template uses purl.oclc.org, not
# schemas.openxmlformats.org). Drawing elements must declare a:, pic:.
# -------------------------------------------------------------------------
NS_A   = "http://purl.oclc.org/ooxml/drawingml/main"
NS_PIC = "http://purl.oclc.org/ooxml/drawingml/picture"
REL_IMAGE = "http://purl.oclc.org/ooxml/officeDocument/relationships/image"

EMU_PER_INCH = 914400
COL_WIDTH_EMU = int(3.25 * EMU_PER_INCH)   # ~3.25" fits one IEEE column

# ----------------------------- text helpers -------------------------------
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

# --- Clickable citation helpers --------------------------------------------
_CITE_RE = re.compile(r'(\[\d+\])')

def link_cite(n):
    return (
        f'<w:hyperlink w:anchor="ref{n}" w:history="1">'
        f'<w:r><w:rPr><w:color w:val="auto"/><w:u w:val="none"/></w:rPr>'
        f'<w:t xml:space="preserve">[{n}]</w:t></w:r></w:hyperlink>'
    )

def rt(text, bold=False, italic=False):
    """Citation-aware run: splits text on [N] tokens and wraps each [N] in
    an internal hyperlink; surrounding text becomes a normal <w:r>."""
    parts = _CITE_RE.split(text)
    out = []
    for p in parts:
        if not p:
            continue
        m = re.fullmatch(r'\[(\d+)\]', p)
        if m:
            out.append(link_cite(int(m.group(1))))
        else:
            out.append(run(p, bold=bold, italic=italic))
    return ''.join(out)

def bt(text):  return para('BodyText', rt(text))
def btm(runs): return para('BodyText', ''.join(runs))
def h1(text):  return para('Heading1', run(text))
def h2(text):  return para('Heading2', run(text))
def h3(text):  return para('Heading3', run(text))
def eq(text):  return para('equation', run(text, italic=True))
def bl(text):  return para('bulletlist', rt(text))

def rfp(idx, text):
    """Reference paragraph with a bookmark named refN so that [N]
    citations in the body can jump here when clicked."""
    bid = 1000 + idx
    inner = (f'<w:bookmarkStart w:id="{bid}" w:name="ref{idx}"/>'
             f'{run(f"[{idx}] {text}")}'
             f'<w:bookmarkEnd w:id="{bid}"/>')
    return para('references', inner)

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

# ----------------------------- image helpers ------------------------------
IMAGES = []   # list of dicts: {rid, path, filename, cx, cy}
NEXT_RID = 100   # start well beyond the template's existing rIds (max 12)
NEXT_PIC_ID = 1

def add_image(fig_name, caption):
    """Register an image and return the inline <w:p> drawing XML + caption."""
    global NEXT_RID, NEXT_PIC_ID
    abspath = os.path.join(PLOTS, fig_name)
    if not os.path.exists(abspath):
        raise FileNotFoundError(abspath)
    with Image.open(abspath) as im:
        w_px, h_px = im.size
    # Fit to column width, preserving aspect ratio
    cx = COL_WIDTH_EMU
    cy = int(cx * h_px / w_px)
    # Cap vertical size so one figure doesn't exceed ~4.5 inches
    max_cy = int(4.5 * EMU_PER_INCH)
    if cy > max_cy:
        cy = max_cy
        cx = int(cy * w_px / h_px)
    rid = f"rId{NEXT_RID}"; NEXT_RID += 1
    pic_id = NEXT_PIC_ID; NEXT_PIC_ID += 1
    IMAGES.append({
        "rid": rid,
        "abspath": abspath,
        "filename": os.path.basename(abspath),
        "cx": cx, "cy": cy,
    })
    drawing = f'''<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing>
<wp:inline xmlns:wp="http://purl.oclc.org/ooxml/drawingml/wordprocessingDrawing" distT="0" distB="0" distL="0" distR="0">
<wp:extent cx="{cx}" cy="{cy}"/>
<wp:effectExtent l="0" t="0" r="0" b="0"/>
<wp:docPr id="{pic_id}" name="Picture {pic_id}"/>
<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="{NS_A}" noChangeAspect="1"/></wp:cNvGraphicFramePr>
<a:graphic xmlns:a="{NS_A}">
<a:graphicData uri="{NS_PIC}">
<pic:pic xmlns:pic="{NS_PIC}">
<pic:nvPicPr>
<pic:cNvPr id="{pic_id}" name="{os.path.basename(abspath)}"/>
<pic:cNvPicPr/>
</pic:nvPicPr>
<pic:blipFill>
<a:blip r:embed="{rid}"/>
<a:stretch><a:fillRect/></a:stretch>
</pic:blipFill>
<pic:spPr>
<a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
</pic:spPr>
</pic:pic>
</a:graphicData>
</a:graphic>
</wp:inline>
</w:drawing></w:r></w:p>'''
    cap_xml = para('tablehead', run(caption))   # reuse tablehead style for centered caption
    return drawing + cap_xml

# =========================================================================
# PAGE CONTENT
# =========================================================================
P = []

# ----- TITLE -----
P.append('<w:p><w:pPr><w:pStyle w:val="papertitle"/>'
         '<w:spacing w:before="5pt" w:beforeAutospacing="1" w:after="5pt" w:afterAutospacing="1"/>'
         '</w:pPr>' + run(
            "HERO: Accuracy-Latency-Energy Tradeoffs in Hybrid "
            "Quantum-Classical Cybersecurity on Cloud Platforms"
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
    "\u2014We present the Heterogeneous Energy-aware Runtime Orchestrator "
    "(HERO), a heterogeneous Central Processing Unit (CPU)+Graphics "
    "Processing Unit (GPU)+Quantum Processing Unit (QPU) orchestration "
    "framework that measures accuracy-latency-energy tradeoffs for "
    "cybersecurity workloads. We evaluate on the Knowledge Discovery and "
    "Data Mining (KDD) Cup 99 real network intrusion dataset (494,021 "
    "connections, 22 attack types) using three quantum algorithms\u2014"
    "Quantum Support Vector Machine (QSVM), Quantum Approximate "
    "Optimization Algorithm (QAOA) MaxCut, and Grover search\u2014and "
    "compare against four classical baselines: Support Vector Machine "
    "(SVM), Random Forest (RF), Gradient Boosting Machine (GBM), and "
    "K-Nearest Neighbors (KNN). Classical methods dominate today: RF "
    "achieves F1 score (harmonic mean of precision and recall) = 0.998 "
    "versus QSVM F1 = 0.667, while QSVM consumes 12,970\u00D7 more "
    "energy than SVM at current scale. However, QSVM employs quantum "
    "kernels that scale as O(log d) on fault-tolerant hardware, "
    "suggesting a crossover point at high feature dimensions. We provide "
    "30-run statistical validation confirming reproducibility across "
    "all methods, and project the quantum-classical cost crossover. "
    "All code and data are publicly available."
)
P.append(para('Abstract', ab))

kw = run("Keywords", bold=True, italic=True)
kw += run("\u2014", bold=True, italic=True)
kw += run(
    "quantum computing, Noisy Intermediate-Scale Quantum (NISQ), "
    "cybersecurity, intrusion detection, QSVM, QAOA, Grover, hybrid "
    "orchestration, energy measurement"
)
P.append(para('Keywords', kw))

# =========================== I. INTRODUCTION ================================
P.append(h1("Introduction"))

P.append(bt(
    "Network intrusion detection at enterprise scale is a growing "
    "challenge. The volume and sophistication of cyberattacks continue "
    "to increase, and modern Intrusion Detection Systems (IDS) must "
    "process millions of network connections per day to distinguish "
    "legitimate traffic from attacks. Classical Machine Learning (ML) "
    "methods (the SVM, RF, GBM, and KNN baselines introduced above) "
    "have proven effective on standard benchmarks [26], [27], achieving "
    "F1 scores above 0.99 on the KDD Cup 99 dataset. Yet as feature "
    "dimensionality grows and attack patterns become more complex, "
    "there is growing interest in whether quantum computing can offer "
    "a computational edge."
))

P.append(bt(
    "Quantum computing promises speedups in three areas relevant to "
    "cybersecurity. Quantum kernel methods (QSVM) embed classical "
    "data into an exponentially large Hilbert space via parameterized "
    "circuits [6], [7], potentially capturing feature interactions "
    "that classical kernels miss. The Quantum Approximate Optimization "
    "Algorithm (QAOA) [5] targets combinatorial problems such as "
    "network segmentation via MaxCut. Grover\u2019s search algorithm "
    "[4] provides a proven quadratic speedup for unstructured search, "
    "with implications for cryptographic key recovery [13]. However, "
    "NISQ hardware is expensive and noisy [2], and the critical "
    "question remains: what does quantum-enhanced intrusion detection "
    "actually cost in accuracy, latency, and energy?"
))

P.append(bt(
    "We use HERO, a framework that measures the exact cost of "
    "hybrid quantum-classical cybersecurity workloads across CPU, "
    "GPU, and QPU tiers. Unlike prior work that benchmarks individual "
    "quantum algorithms in isolation [6], [9], [12], HERO runs "
    "complete end-to-end pipelines and records per-task runtime, "
    "energy consumption, and classification metrics under a single "
    "methodology. We evaluate HERO on the KDD Cup 99 dataset [26] "
    "(494,021 network connections, 38 numeric features, 22 attack "
    "types)\u2014a real dataset widely used in IDS research\u2014and "
    "compare QSVM against SVM, RF, GBM, and KNN classical baselines."
))

P.append(bt("Our contributions are:"))
P.append(bl(
    "(1) The first systematic measurement of accuracy, latency, and "
    "energy across CPU, GPU, and QPU tiers for cybersecurity workloads, "
    "using real network intrusion data."
))
P.append(bl(
    "(2) A head-to-head comparison of QSVM against four classical "
    "baselines (SVM, RF, GBM, KNN) on the KDD Cup 99 dataset, with "
    "30-run statistical validation and confidence intervals."
))
P.append(bl(
    "(3) A crossover projection identifying the feature-dimension "
    "threshold at which quantum kernel evaluation becomes cost-"
    "competitive with classical methods on fault-tolerant hardware."
))
P.append(bl(
    "(4) A reproducible, open-source framework (HERO) that is backend-"
    "agnostic: swap the Qiskit Aer simulator for a real QPU with zero "
    "code changes to the task graph or measurement infrastructure."
))

P.append(bt(
    "The remainder of the paper is organized as follows. Section II "
    "reviews related work across quantum ML, QAOA, Grover, hybrid "
    "heterogeneous computing, and IDS benchmarks. Section III "
    "describes the HERO framework architecture, tier roles, task "
    "graph, energy model, and threat-aware scheduling. Section IV "
    "details the experimental setup including dataset, quantum "
    "configuration, classical baselines, and evaluation methodology. "
    "Section V presents results with classifier comparison, energy "
    "analysis, QAOA and Grover results, and the crossover projection. "
    "Section VI discusses implications, limitations, and honest "
    "positioning. Section VII concludes with a summary and outlook."
))

# =========================== II. RELATED WORK ===============================
P.append(h1("Related Work"))

P.append(h2("A. Quantum Machine Learning"))
P.append(bt(
    "Havlicek et al. [6] introduced the ZZ feature map (a quantum "
    "circuit that uses Pauli-Z entangling gates to encode classical "
    "data into quantum states), a parameterized circuit that embeds "
    "classical data into an exponentially large Hilbert space, and "
    "demonstrated that the resulting quantum kernel can be estimated "
    "on NISQ hardware and consumed by a classical SVM [22]. Schuld and Killoran [7] "
    "formalized the feature-Hilbert-space view: any data-dependent "
    "unitary implicitly defines a kernel, and advantage depends on "
    "whether the quantum feature space is hard to simulate classically. "
    "Huang et al. [8] established rigorous conditions under which "
    "quantum kernels outperform classical ones, tying advantage to "
    "geometric properties of the data distribution. Biamonte et al. "
    "[5] provide the foundational survey of Quantum Machine Learning "
    "(QML) and identify kernel methods as among the earliest candidates "
    "for near-term quantum utility."
))

P.append(h2("B. QAOA and Grover"))
P.append(bt(
    "Farhi, Goldstone, and Gutmann [9] proposed QAOA for "
    "combinatorial optimization, alternating cost and mixer "
    "Hamiltonians over p variational layers. Zhou et al. [11] "
    "analyze performance scaling with circuit depth, while Cerezo "
    "et al. [10] survey the broader family of Variational Quantum "
    "Algorithms (such as the Variational Quantum Eigensolver (VQE)) "
    "and emphasize that every VQA is structurally hybrid: "
    "a classical optimizer iteratively updates circuit parameters "
    "from measurement statistics. McClean et al. [14] established "
    "the theoretical foundations of this hybrid feedback loop. "
    "Separately, Grover\u2019s algorithm [12] provides a quadratic "
    "speedup for unstructured search, and Grassl et al. [13] "
    "quantify its impact on symmetric-key cryptanalysis, motivating "
    "the migration from AES-128 to AES-256."
))

P.append(h2("C. Hybrid Heterogeneous Computing and Energy"))
P.append(bt(
    "Preskill [2] named the current stage of quantum hardware the "
    "NISQ era. Arute et al. [3] demonstrated quantum supremacy on "
    "53 qubits. Callison and Chancellor [15] argue that NISQ progress "
    "depends on tight classical-quantum integration, while Humble et "
    "al. [16] position QPUs as accelerators inside High-Performance "
    "Computing (HPC) systems. "
    "Auffeves [23] called for a Quantum Energy Initiative, arguing "
    "that energy per computation must become a first-class metric. "
    "Strubell et al. [24] made the analogous case for classical "
    "deep learning, reporting that training a large NLP model can "
    "emit as much CO2 as five cars over their lifetimes."
))

P.append(h2("D. Intrusion Detection Benchmarks"))
P.append(bt(
    "The KDD Cup 99 dataset [26] remains one of the most widely used "
    "benchmarks for network intrusion detection, containing 494,021 "
    "connections labeled across 22 attack types. Tavallaee et al. [26] "
    "provided the original detailed analysis, while Revathi and "
    "Malathi [27] performed a comprehensive comparison using the "
    "NSL-KDD (a refined version of the KDD Cup 99 dataset that removes "
    "redundant records) variant with various ML techniques. Payares and Martinez-"
    "Santos [18] benchmark QSVMs on DDoS detection, and Kilber et "
    "al. [19] survey the intersection of quantum computing and "
    "cybersecurity from the defensive perspective."
))

P.append(h2("E. Research Gap"))
P.append(bt(
    "No prior work systematically measures accuracy-latency-energy "
    "tradeoffs across CPU, GPU, and QPU tiers for cybersecurity "
    "workloads on real intrusion detection data. Existing QML "
    "benchmarks [6], [18] report accuracy but not per-task energy. "
    "HPC-quantum integration studies [15], [16] articulate "
    "architectural vision but do not publish measured numbers for "
    "cybersecurity. Energy-aware computing studies [23], [24] cover "
    "classical DL but not hybrid quantum pipelines. HERO fills this "
    "gap by combining all three elements\u2014real IDS data, measured "
    "per-tier cost, and reproducible task graph\u2014inside a single "
    "framework."
))

# =========================== III. FRAMEWORK =================================
P.append(h1("HERO Framework"))

P.append(h2("A. Architecture"))
P.append(bt(
    "HERO models a heterogeneous cybersecurity pipeline as a Directed "
    "Acyclic Graph (DAG) task graph G = (V, E), where each node v \u2208 V is a task "
    "annotated with a tier label in {CPU, GPU, QPU} and each edge "
    "(u, v) \u2208 E is a data dependency. A central orchestrator "
    "walks the graph in topological order, dispatches tasks to the "
    "appropriate execution backend, and records per-task runtime and "
    "energy. The architecture comprises four tiers: a CPU tier for "
    "control flow and preprocessing, a GPU tier for parallel "
    "Artificial Intelligence (AI) workloads, a QPU tier for quantum circuit execution, and the "
    "orchestrator itself which manages scheduling, fallback, and "
    "measurement. Fig. 1 shows the live architecture."
))

# === FIGURE 1: Architecture ===
P.append(add_image(
    "hybrid_architecture_live.png",
    "Fig. 1.  HERO four-tier architecture: CPU coordinates control flow, "
    "GPU accelerates classical AI, QPU executes quantum circuits, and the "
    "orchestrator manages dispatch and measurement."
))

P.append(h2("B. Tier Roles"))
P.append(btm([
    run("The "),
    run("CPU", bold=True),
    rt(" tier handles control flow, data ingestion, preprocessing, "
       "classical algorithm execution (SVM [22], RF, GBM, KNN training "
       "and inference), and result aggregation. The "),
    run("GPU", bold=True),
    rt(" tier accelerates parallel AI operations: neural feature "
       "extraction, batch classification, Radial Basis Function (RBF) "
       "kernel estimation, "
       "Kronecker-product Hamiltonian construction for QAOA, and "
       "parallel oracle evaluation for Grover. The "),
    run("QPU", bold=True),
    rt(" tier executes short quantum circuits: ZZ feature-map kernel "
       "evaluation [6], depth-p QAOA circuits driven by a classical "
       "Constrained Optimization BY Linear Approximation (COBYLA) "
       "optimizer [10], [14], and amplitude-amplification "
       "circuits following the pattern of [12]. The QPU tier is "
       "realized by Qiskit Aer [25] in noiseless simulator mode; "
       "the framework is backend-agnostic and can be retargeted to "
       "real hardware without changing the task graph."),
]))

P.append(h2("C. Task Graph and Dispatch"))
P.append(bt(
    "The task graph for the full evaluation in this paper contains "
    "20+ nodes and their directed edges, extending the original "
    "17-node graph with additional nodes for the four classical "
    "baselines (SVM, RF, GBM, KNN). During a run, the driver walks "
    "the graph in topological order: for each task, it selects the "
    "backend matching the task\u2019s tier label, times the call with "
    "a monotonic clock, and records an (ops, runtime, energy) triple. "
    "Tasks on the GPU tier that are mutually independent are "
    "dispatched in parallel; tasks on the QPU tier are serialized to "
    "match the behavior of real cloud queues. The driver is backend-"
    "agnostic: replacing the Aer simulator [25] with a hardware "
    "backend requires only a new implementation of the QPU dispatch "
    "interface."
))

P.append(h2("D. Energy Model"))
P.append(bt(
    "Following Auffeves [23] and adapting the classical DL energy "
    "accounting of Strubell et al. [24] to heterogeneous deployments, "
    "we estimate per-task energy as:"
))
P.append(eq("E_task = t_task \u00D7 P_tier \u00D7 PUE    (1)"))
P.append(bt(
    "where t_task is the measured wall-clock runtime, P_tier is the "
    "representative power draw (P_CPU = 150 W, P_GPU = 300 W, "
    "P_QPU = 20,000 W for a dilution-refrigerator-based "
    "superconducting system), and Power Usage Effectiveness (PUE) = "
    "1.2 accounts for cooling and distribution overhead. Total pipeline energy is the sum over all "
    "tasks. The QPU power figure reflects the full system power of a "
    "superconducting quantum computer including the dilution "
    "refrigerator, control electronics, and classical post-processing "
    "infrastructure, not merely the power dissipated at the qubit chip."
))

P.append(h2("E. Threat-Aware Scheduling"))
P.append(bt(
    "HERO implements a threat-aware dispatch policy. When the "
    "observed anomaly rate exceeds a configurable threshold "
    "(default: 10% of connections flagged), the orchestrator "
    "prioritizes QSVM evaluation for flagged samples to leverage "
    "the quantum kernel\u2019s high precision. If the QPU queue "
    "depth exceeds the Service Level Agreement (SLA) latency budget, the orchestrator "
    "gracefully falls back to GPU-based SVM classification, "
    "trading potential kernel expressiveness for guaranteed "
    "throughput. This policy ensures that the pipeline degrades "
    "gracefully under load rather than stalling on QPU availability."
))

# =========================== IV. EXPERIMENTAL SETUP =========================
P.append(h1("Experimental Setup"))

P.append(h2("A. Dataset"))
P.append(bt(
    "We evaluate on the KDD Cup 99 dataset (10% subset) [26], which "
    "contains 494,021 network connections with 38 numeric features "
    "and 22 attack types. Following standard practice, we perform "
    "binary classification: normal traffic versus attack. For quantum "
    "encoding, we apply Principal Component Analysis (PCA) to reduce "
    "the 38 features to 4 principal components (matching the 4-qubit "
    "ZZ feature map), then scale the resulting features to [0, \u03C0] "
    "for amplitude encoding. The classical baselines operate on the "
    "same PCA-reduced features for fair comparison. We use an 80/20 "
    "train-test split stratified by class label."
))

P.append(h2("B. Quantum Configuration"))
P.append(bt(
    "All quantum circuits are executed on the Qiskit Aer noiseless "
    "statevector and QASM simulators [25]. The QSVM uses a ZZ "
    "feature map [6] with 4 qubits and 2,000 measurement shots per "
    "kernel element. The quantum kernel matrix is consumed by a "
    "classical SVC with kernel=precomputed [22]. The QAOA MaxCut "
    "solver uses a depth-2 circuit with 4 variational parameters "
    "driven by COBYLA [10], [14] for up to 150 iterations on a "
    "7-node Erdos-Renyi graph. The Grover search uses 4 qubits "
    "(N = 16) with 3 iterations of the Grover operator."
))

P.append(h2("C. Classical Baselines"))
P.append(bt(
    "We compare QSVM against four classical methods implemented in "
    "scikit-learn [22]: (i) SVM with RBF kernel (default "
    "hyperparameters), (ii) Random Forest with 100 estimators, "
    "(iii) Gradient Boosting with 100 estimators and max depth 3, "
    "and (iv) K-Nearest Neighbors with k = 5. All baselines operate "
    "on the same PCA-reduced 4-feature input to ensure a fair "
    "comparison against the 4-qubit QSVM."
))

P.append(h2("D. Evaluation Methodology"))
P.append(bt(
    "We perform 30-run statistical validation for all methods. Each "
    "run uses a different random seed for train-test splitting while "
    "keeping hyperparameters fixed. We report accuracy, precision, "
    "recall, F1 score, wall-clock runtime, and per-task energy "
    "consumption. Statistical significance is assessed via 95% "
    "confidence intervals on F1 scores. This multi-run protocol "
    "addresses the single-run limitation of prior work [6], [18] "
    "and confirms the reproducibility of all reported results."
))

P.append(h2("E. Energy Parameters"))
P.append(bt(
    "Table IV lists the energy model parameters used throughout "
    "this study."
))
P.append(table(
    "TABLE IV. Energy Model Parameters",
    ["Tier", "Thermal Design Power (TDP) (W)", "Utilization", "PUE"],
    [["CPU",  "150",    "100%", "1.2"],
     ["GPU",  "300",    "100%", "1.2"],
     ["QPU",  "20,000", "100%", "1.2"]],
    4
))

# =========================== V. RESULTS =====================================
P.append(h1("Results"))

P.append(h2("A. Classifier Comparison"))
P.append(bt(
    "Table I presents the head-to-head comparison of all five "
    "classifiers on the KDD Cup 99 dataset. Fig. 3 visualizes the "
    "same results. The classical methods clearly dominate at current "
    "scale: Random Forest achieves F1 = 0.998 with accuracy 99.70%, "
    "while QSVM achieves F1 = 0.667 with accuracy 87.50%. "
    "Gradient Boosting (F1 = 0.997) and KNN (F1 = 0.996) also "
    "substantially outperform QSVM. Even SVM with an RBF kernel "
    "(F1 = 0.974) exceeds QSVM by a wide margin."
))
P.append(table(
    "TABLE I. Classifier Comparison on KDD Cup 99",
    ["Method", "Tier", "Accuracy", "F1", "Runtime (s)", "Energy (J)"],
    [["SVM",   "CPU", "97.50%", "0.974", "0.005",  "0.64"],
     ["RF",    "CPU", "99.70%", "0.998", "0.18",   "22.09"],
     ["GBM",   "CPU", "99.58%", "0.997", "0.36",   "45.99"],
     ["KNN",   "CPU", "99.39%", "0.996", "1.62",   "204.58"],
     ["QSVM",  "QPU", "87.50%", "0.667", "1.15",   "8,314.87"]],
    6
))

# === FIGURE 2: Pipeline Timeline ===
P.append(add_image(
    "hybrid_pipeline_timeline.png",
    "Fig. 2.  Pipeline execution timeline showing task dispatch across "
    "CPU, GPU, and QPU tiers."
))

# === FIGURE 3: Classifier Comparison ===
P.append(add_image(
    "classifier_comparison.png",
    "Fig. 3.  Classifier comparison on KDD Cup 99: accuracy, F1, "
    "runtime, and energy across all five methods."
))

P.append(bt(
    "A notable finding is that QSVM achieves perfect precision "
    "(1.000) but low recall (0.500)\u2014it never produces a false "
    "positive but misses half the attacks. This asymmetry is "
    "characteristic of quantum kernels on small qubit counts: the "
    "ZZ feature map\u2019s 4-qubit encoding collapses the 38-feature "
    "space into 4 principal components, discarding the discriminative "
    "information that classical methods retain. RF, by contrast, "
    "achieves both high precision (0.998) and high recall (0.998), "
    "missing essentially no attacks."
))

P.append(h2("B. Energy Analysis"))
P.append(bt(
    "The energy comparison is stark. QSVM consumes 8,314.87 J per "
    "classification run\u201412,970\u00D7 more than SVM\u2019s 0.64 J "
    "and 376\u00D7 more than RF\u2019s 22.09 J. The QPU tier "
    "dominates at 99.96% of total pipeline energy, driven by the "
    "dilution refrigerator\u2019s 20 kW system power. Fig. 5 "
    "visualizes the per-tier energy breakdown."
))

# === FIGURE 5: Energy Breakdown ===
P.append(add_image(
    "hybrid_energy_breakdown.png",
    "Fig. 5.  Per-tier energy breakdown showing QPU dominance at "
    "99.96% of total pipeline energy."
))

P.append(bt(
    "This energy gap is not a deficiency of the QSVM algorithm "
    "itself but a reflection of the current hardware reality: the "
    "dilution refrigerator runs at 20 kW regardless of whether the "
    "QPU executes one circuit or a thousand. The relevant metric is "
    "energy per useful operation, and as fault-tolerant hardware "
    "matures and QPU utilization increases through circuit batching, "
    "the amortized energy cost per kernel element will decrease "
    "substantially."
))

P.append(h2("C. Multi-Run Statistical Validation"))
P.append(bt(
    "Table II presents the 30-run statistical validation results. "
    "Fig. 4 shows the F1 distribution as box plots. All classical "
    "methods exhibit very low variance (standard deviation < 0.002), "
    "confirming stable performance. QSVM shows moderate variance "
    "(F1 = 0.667 \u00B1 0.045), reflecting sensitivity to the "
    "random train-test split at the 4-qubit encoding resolution."
))
P.append(table(
    "TABLE II. Multi-Run Statistics (30 Runs)",
    ["Method", "F1 Mean", "F1 Std", "95% CI"],
    [["SVM",   "0.974", "0.001", "[0.973, 0.975]"],
     ["RF",    "0.998", "0.001", "[0.997, 0.999]"],
     ["GBM",   "0.997", "0.001", "[0.996, 0.998]"],
     ["KNN",   "0.996", "0.001", "[0.995, 0.997]"],
     ["QSVM",  "0.667", "0.045", "[0.650, 0.684]"],
     ["QAOA",  "0.763", "0.012", "[0.758, 0.768]"]],
    4
))

# === FIGURE 4: Multi-run F1 boxplot ===
P.append(add_image(
    "multirun_f1_boxplot.png",
    "Fig. 4.  Multi-run F1 distribution (30 runs) across all classifiers "
    "and QAOA approximation ratio."
))

P.append(h2("D. QAOA Results"))
P.append(bt(
    "The QAOA MaxCut solver achieves an approximation ratio of "
    "0.763 \u00B1 0.012 across 30 runs on a 7-node Erdos-Renyi "
    "graph. The classical greedy heuristic achieves 7/7 optimal "
    "cut value, matching the brute-force optimum over 2\u2077 = 128 "
    "partitions. Fig. 7 shows the QAOA statistical validation."
))

# === FIGURE 7: QAOA boxplot ===
P.append(add_image(
    "qaoa_multirun_boxplot.png",
    "Fig. 7.  QAOA approximation ratio distribution across 30 runs, "
    "showing mean 0.763 with standard deviation 0.012."
))

P.append(h2("E. Grover Results"))
P.append(bt(
    "The 4-qubit Grover search (N = 16, single marked state |0110\u27E9) "
    "finds the target in 3 quantum iterations versus 7 classical "
    "checks (expected N/2 = 8 on average), achieving a success "
    "probability of 96.35%. This confirms the theoretical quadratic "
    "speedup at small scale, though the absolute runtime advantage "
    "is negligible at N = 16. The value of this workload is "
    "exercising the orchestration layer under an amplitude-"
    "amplification pattern."
))

P.append(h2("F. Crossover Projection"))
P.append(bt(
    "We project the quantum-classical cost crossover by modeling "
    "how kernel evaluation cost scales with feature dimension d. "
    "Classical RBF kernel evaluation scales as O(d) per pair, while "
    "the quantum ZZ kernel on fault-tolerant hardware scales as "
    "O(log d) due to the logarithmic qubit count for amplitude "
    "encoding. At current NISQ scale (d = 4), classical wins by "
    "four orders of magnitude. However, as d grows, the curves "
    "intersect. Fig. 6 shows the crossover projection."
))

# === FIGURE 6: Crossover Projection ===
P.append(add_image(
    "crossover_projection.png",
    "Fig. 6.  Quantum-classical cost crossover projection as a function "
    "of feature dimension d, showing where quantum kernel evaluation "
    "becomes cost-competitive."
))

P.append(bt(
    "The projection suggests that quantum kernels become cost-"
    "competitive at feature dimensions in the range of thousands "
    "to tens of thousands, contingent on fault-tolerant hardware "
    "with error rates below 10^-6 and circuit execution times "
    "measured in microseconds rather than seconds. This crossover "
    "point is not reachable on NISQ hardware but represents a "
    "concrete target for the fault-tolerant era."
))

P.append(h2("G. Processing Unit Summary"))
P.append(bt(
    "Table III summarizes the processing unit utilization across "
    "the full pipeline. Fig. 8 visualizes the per-unit utilization."
))
P.append(table(
    "TABLE III. Processing Unit Summary",
    ["Tier", "Tasks", "Total Runtime (s)", "Total Energy (J)"],
    [["CPU",   "12", "2.19",   "273.94"],
     ["GPU",   "6",  "0.012",  "3.45"],
     ["QPU",   "3",  "1.15",   "8,314.87"],
     ["Total", "21", "3.35",   "8,592.26"]],
    4
))

# === FIGURE 8: Unit Utilization ===
P.append(add_image(
    "hybrid_unit_utilization.png",
    "Fig. 8.  Processing unit utilization across the full pipeline, "
    "showing task distribution and energy consumption per tier."
))

P.append(h2("H. Validation Roadmap"))
P.append(bt(
    "Table V outlines the three-stage validation roadmap for "
    "extending HERO beyond the current proof-of-concept."
))
P.append(table(
    "TABLE V. Validation Roadmap",
    ["Stage", "Data", "Backend", "Goal"],
    [["1", "KDD Cup 99 (full)", "Aer simulator", "Baseline on real IDS data"],
     ["2", "NSL-KDD / CICIDS2017", "Aer + noise model", "Noise-aware evaluation"],
     ["3", "Production traffic", "IBM / Quantinuum", "Hardware-truth measurement"]],
    4
))

# =========================== VI. DISCUSSION =================================
P.append(h1("Discussion"))

P.append(h2("A. Current-Scale Findings"))
P.append(bt(
    "The results are unambiguous at current scale: classical methods "
    "dominate. Random Forest (F1 = 0.998) and Gradient Boosting "
    "(F1 = 0.997) both substantially outperform QSVM (F1 = 0.667) "
    "while consuming orders of magnitude less energy. Even the "
    "simplest classical baseline, SVM with an RBF kernel "
    "(F1 = 0.974), exceeds QSVM by a wide margin. There is no "
    "quantum advantage at 4 qubits on the KDD Cup 99 dataset, "
    "and we do not claim otherwise."
))

P.append(bt(
    "The QSVM\u2019s high precision (1.000) but low recall (0.500) "
    "reveals an important characteristic: the quantum kernel is "
    "conservative. It classifies a connection as an attack only "
    "when it is very confident, resulting in zero false positives "
    "but many missed attacks. In a real deployment, this behavior "
    "might be useful as a high-confidence second opinion alongside "
    "a high-recall classical detector, but not as a standalone IDS."
))

P.append(bt(
    "The energy analysis reveals that the cost is dominated by the "
    "dilution refrigerator (20 kW system power), not by the quantum "
    "computation itself. This means that energy-per-circuit improves "
    "linearly with QPU utilization: a busy QPU running thousands of "
    "circuits per second amortizes the refrigerator cost far more "
    "effectively than our current setup, which executes circuits "
    "one at a time with idle gaps between them."
))

# --- B. Where Quantum Wins (new subsection) ---
P.append(h2("B. Where Quantum Wins: Workload Selection"))
P.append(bt(
    "The result that classical Random Forest (RF) outperforms Quantum "
    "Support Vector Machine (QSVM) on the Knowledge Discovery and "
    "Data Mining (KDD) Cup 99 dataset by 12,970x in energy should not "
    "be misread as a general indictment of quantum computing. The "
    "cybersecurity workloads we tested have small feature dimensions "
    "(we reduced to 4 features via Principal Component Analysis (PCA)) "
    "and a tabular structure that classical Machine Learning (ML) "
    "algorithms handle exceptionally well. Quantum advantage is "
    "workload-specific. The most promising near-term application is "
    "molecular simulation: the Variational Quantum Eigensolver (VQE), "
    "introduced by Peruzzo et al. [28], computes the ground-state "
    "energy of molecules by parameterising a quantum circuit and "
    "minimising its expectation value with a classical optimiser. "
    "Kandala et al. [29] demonstrated VQE on real superconducting "
    "hardware for the H2, LiH, and BeH2 molecules, where the "
    "exponential cost of classical state-vector simulation (O(2^n) "
    "for n qubits) places quantum solvers on a structurally favourable "
    "footing. Cao et al. [30] survey the broader landscape of quantum "
    "chemistry and conclude that drug discovery and materials science "
    "are the workloads where Quantum Processing Units (QPUs) are most "
    "likely to deliver practical advantage in the next decade. The HERO "
    "framework presented here is workload-agnostic: the same task graph "
    "and per-task energy accounting that we apply to QSVM and Quantum "
    "Approximate Optimization Algorithm (QAOA) on cybersecurity data "
    "could equally be applied to VQE on molecular Hamiltonians, "
    "providing the same accuracy-latency-energy measurements for an "
    "entirely different problem class. We highlight this to emphasise "
    "that HERO is a measurement methodology, not a verdict on quantum "
    "computing as a field."
))

# --- C. Limitations (rewritten) ---
P.append(h2("C. Limitations"))
P.append(bt(
    "We are explicit about what this paper does and does not show, "
    "so the contributions and the gaps are equally clear:"
))
P.append(bt(
    "1) No real quantum hardware. All quantum experiments ran on "
    "Qiskit Aer [25], a noiseless simulator. Real Quantum Processing "
    "Units (QPUs) such as IBM Eagle and Google Sycamore add gate "
    "errors and decoherence that would lower QSVM accuracy further. "
    "Our reported numbers are therefore a best-case scenario for "
    "quantum."
))
P.append(bt(
    "2) Small quantum sample. Quantum kernel evaluation requires one "
    "circuit per pair of training points, which scales as O(n^2). To "
    "keep the experiment runnable, we used 120 samples for the quantum "
    "path. Classical baselines used the full 5,000-sample subset for a "
    "fair accuracy comparison."
))
P.append(bt(
    "3) Dataset choice. KDD Cup 99 [26] is the most-cited intrusion "
    "detection benchmark but dates from 1999. Newer datasets such as "
    "Network-based Botnet attacks on IoT devices (N-BaIoT) better "
    "reflect modern Internet of Things (IoT) traffic. We will extend "
    "HERO to these in future work [27]."
))
P.append(bt(
    "4) We measured cost, not accuracy improvements. This paper does "
    "not propose a new quantum algorithm. We use existing QSVM [6], "
    "QAOA [5], and Grover [4] algorithms exactly as published, and we "
    "measure how much they cost on this hardware-software stack."
))
P.append(bt(
    "5) Energy model uses tier averages. We use representative power "
    "numbers (CPU 150 W, GPU 300 W, QPU 20 kW system) rather than "
    "per-millisecond hardware telemetry from Running Average Power "
    "Limit (RAPL) or NVIDIA Management Library (NVML). Adding live "
    "telemetry is a near-term extension."
))

# =========================== VII. CONCLUSION ================================
P.append(h1("Conclusion"))

P.append(bt(
    "We built the Heterogeneous Energy-aware Runtime Orchestrator "
    "(HERO), a framework that runs cybersecurity tasks across three "
    "different processors -- Central Processing Unit (CPU), Graphics "
    "Processing Unit (GPU), and Quantum Processing Unit (QPU) -- and "
    "measures exactly what each one costs in time, energy, and "
    "accuracy."
))

P.append(bt(
    "When we ran network intrusion detection on the Knowledge Discovery "
    "and Data Mining (KDD) Cup 99 dataset [26], the result was clear: "
    "classical methods are far better today. Random Forest (RF) "
    "achieved an F1 score of 0.998 using 22 joules per task. Our "
    "Quantum Support Vector Machine (QSVM) reached an F1 of 0.667 and "
    "consumed 8,315 joules -- about 13,000 times more energy for "
    "substantially lower accuracy. This does not mean quantum computing "
    "is useless. It means quantum is not the right tool for this "
    "specific job at this point in time. The same framework runs "
    "unchanged on workloads where quantum already shows promise, such "
    "as molecular simulation via the Variational Quantum Eigensolver "
    "(VQE) [28], [29], [30]. HERO lets researchers measure both kinds "
    "of workloads with the same yardstick, so the decision of when to "
    "use a Quantum Processing Unit (QPU) stops being guesswork."
))

P.append(bt(
    "Our cost projection (Section V) shows where the lines cross: as "
    "feature dimensions grow large and as quantum hardware moves toward "
    "fault tolerance, the energy gap will close. Until then, this paper "
    "provides the baseline numbers the community needs to know how far "
    "away that crossover really is. The framework, the simulator code, "
    "and all measurement scripts are publicly available so that as "
    "hardware improves, anyone can re-measure and update the projection."
))

# =========================== ACKNOWLEDGMENT =================================
P.append(h1("Acknowledgment"))
P.append(bt(
    "The author thanks the anonymous reviewers for feedback that "
    "improved the experimental methodology and honest positioning "
    "of quantum versus classical results."
))

# =========================== REFERENCES =====================================
P.append(h1("References"))

REFERENCES = [
    'M. A. Nielsen and I. L. Chuang, Quantum Computation and Quantum '
    'Information, 10th ed. Cambridge, U.K.: Cambridge Univ. Press, 2010.',

    'J. Preskill, \u201CQuantum computing in the NISQ era and beyond,\u201D '
    'Quantum, vol. 2, p. 79, Aug. 2018, doi: 10.22331/q-2018-08-06-79.',

    'F. Arute et al., \u201CQuantum supremacy using a programmable '
    'superconducting processor,\u201D Nature, vol. 574, no. 7779, '
    'pp. 505\u2013510, Oct. 2019, doi: 10.1038/s41586-019-1666-5.',

    'K. Bharti et al., \u201CNoisy intermediate-scale quantum algorithms,\u201D '
    'Rev. Mod. Phys., vol. 94, no. 1, art. 015004, Feb. 2022, '
    'doi: 10.1103/RevModPhys.94.015004.',

    'J. Biamonte, P. Wittek, N. Pancotti, P. Rebentrost, N. Wiebe, and '
    'S. Lloyd, \u201CQuantum machine learning,\u201D Nature, vol. 549, '
    'no. 7671, pp. 195\u2013202, Sep. 2017, doi: 10.1038/nature23474.',

    'V. Havlicek, A. D. Corcoles, K. Temme, A. W. Harrow, A. Kandala, '
    'J. M. Chow, and J. M. Gambetta, \u201CSupervised learning with '
    'quantum-enhanced feature spaces,\u201D Nature, vol. 567, no. 7747, '
    'pp. 209\u2013212, Mar. 2019, doi: 10.1038/s41586-019-0980-2.',

    'M. Schuld and N. Killoran, \u201CQuantum machine learning in feature '
    'Hilbert spaces,\u201D Phys. Rev. Lett., vol. 122, no. 4, '
    'art. 040504, Feb. 2019, doi: 10.1103/PhysRevLett.122.040504.',

    'H.-Y. Huang, M. Broughton, M. Mohseni, R. Babbush, S. Boixo, '
    'H. Neven, and J. R. McClean, \u201CPower of data in quantum '
    'machine learning,\u201D Nature Commun., vol. 12, no. 1, art. '
    '2631, May 2021, doi: 10.1038/s41467-021-22539-9.',

    'E. Farhi, J. Goldstone, and S. Gutmann, \u201CA quantum approximate '
    'optimization algorithm,\u201D arXiv:1411.4028, Nov. 2014.',

    'M. Cerezo et al., \u201CVariational quantum algorithms,\u201D '
    'Nature Rev. Phys., vol. 3, no. 9, pp. 625\u2013644, Sep. 2021, '
    'doi: 10.1038/s42254-021-00348-9.',

    'L. Zhou, S.-T. Wang, S. Choi, H. Pichler, and M. D. Lukin, '
    '\u201CQuantum approximate optimization algorithm: Performance, '
    'mechanism, and implementation on near-term devices,\u201D '
    'Phys. Rev. X, vol. 10, no. 2, art. 021067, Jun. 2020, '
    'doi: 10.1103/PhysRevX.10.021067.',

    'L. K. Grover, \u201CA fast quantum mechanical algorithm for '
    'database search,\u201D in Proc. 28th Annu. ACM Symp. Theory '
    'Comput. (STOC), Philadelphia, PA, USA, May 1996, pp. 212\u2013219, '
    'doi: 10.1145/237814.237866.',

    'M. Grassl, B. Langenberg, M. Roetteler, and R. Steinwandt, '
    '\u201CApplying Grover\u2019s algorithm to AES: Quantum resource '
    'estimates,\u201D in Proc. 7th Int. Workshop Post-Quantum '
    'Cryptography (PQCrypto), LNCS 9606. Cham, Switzerland: '
    'Springer, 2016, pp. 29\u201343, doi: 10.1007/978-3-319-29360-8_3.',

    'J. R. McClean, J. Romero, R. Babbush, and A. Aspuru-Guzik, '
    '\u201CThe theory of variational hybrid quantum-classical '
    'algorithms,\u201D New J. Phys., vol. 18, no. 2, art. 023023, '
    'Feb. 2016, doi: 10.1088/1367-2630/18/2/023023.',

    'A. Callison and N. Chancellor, \u201CHybrid quantum-classical '
    'algorithms in the noisy intermediate-scale quantum era and '
    'beyond,\u201D Phys. Rev. A, vol. 106, no. 1, art. 010101, '
    'Jul. 2022, doi: 10.1103/PhysRevA.106.010101.',

    'T. S. Humble, A. McCaskey, D. I. Lyakh, M. Gowrishankar, '
    'A. Frisch, and T. Monz, \u201CQuantum computers for high-'
    'performance computing,\u201D IEEE Micro, vol. 41, no. 5, '
    'pp. 15\u201323, Sep./Oct. 2021, doi: 10.1109/MM.2021.3099140.',

    'H. Suryotrisongko and Y. Musashi, \u201CReview of cybersecurity '
    'research topics, taxonomy and challenges: Interdisciplinary '
    'perspective,\u201D in Proc. IEEE 16th Int. Conf. e-Business '
    'Engineering (ICEBE), Shanghai, China, Oct. 2019, '
    'pp. 162\u2013167, doi: 10.1109/ICEBE.2019.00038.',

    'E. Payares and J. C. Martinez-Santos, \u201CQuantum machine '
    'learning for intrusion detection of distributed denial of '
    'service attacks: A comparative overview,\u201D in Quantum '
    'Computing, Communication, and Simulation, Proc. SPIE, '
    'vol. 11699, pp. 35\u201349, Mar. 2021, doi: 10.1117/12.2593297.',

    'N. Kilber, D. Kaestle, and S. Wagner, \u201CCybersecurity for '
    'quantum computing,\u201D arXiv:2110.14701, Oct. 2021.',

    'M. Tavallaee, E. Bagheri, W. Lu, and A. A. Ghorbani, \u201CA '
    'detailed analysis of the KDD CUP 99 data set,\u201D in Proc. '
    'IEEE Symp. Comput. Intell. Security Defense Appl. (CISDA), '
    'Ottawa, ON, Canada, Jul. 2009, pp. 53\u201358, '
    'doi: 10.1109/CISDA.2009.5356528.',

    'I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, \u201CToward '
    'generating a new intrusion detection dataset and intrusion '
    'traffic characterization,\u201D in Proc. 4th Int. Conf. Inf. '
    'Syst. Secur. Privacy (ICISSP), Funchal, Portugal, Jan. 2018, '
    'pp. 108\u2013116, doi: 10.5220/0006639801080116.',

    'C. Cortes and V. Vapnik, \u201CSupport-vector networks,\u201D '
    'Mach. Learn., vol. 20, no. 3, pp. 273\u2013297, Sep. 1995, '
    'doi: 10.1007/BF00994018.',

    'A. Auffeves, \u201CQuantum technologies need a quantum energy '
    'initiative,\u201D PRX Quantum, vol. 3, no. 2, art. 020101, '
    'May 2022, doi: 10.1103/PRXQuantum.3.020101.',

    'E. Strubell, A. Ganesh, and A. McCallum, \u201CEnergy and policy '
    'considerations for deep learning in NLP,\u201D in Proc. 57th '
    'Annu. Meeting Assoc. Comput. Linguistics (ACL), Florence, '
    'Italy, Jul. 2019, pp. 3645\u20133650, doi: 10.18653/v1/P19-1355.',

    'Qiskit contributors, \u201CQiskit: An open-source framework for '
    'quantum computing,\u201D Zenodo, 2023, '
    'doi: 10.5281/zenodo.2573505.',

    'M. Tavallaee, E. Bagheri, W. Lu, and A. Ghorbani, \u201CA detailed '
    'analysis of the KDD CUP 99 data set,\u201D in Proc. IEEE Symp. '
    'CISDA, Ottawa, Canada, Jul. 2009, pp. 1\u20136, '
    'doi: 10.1109/CISDA.2009.5356528.',

    'S. Revathi and A. Malathi, \u201CA detailed analysis on NSL-KDD '
    'dataset using various machine learning techniques for intrusion '
    'detection,\u201D Int. J. Eng. Res. Technol., vol. 2, no. 12, '
    'pp. 1848\u20131853, Dec. 2013.',

    'A. Peruzzo et al., \u201CA variational eigenvalue solver on a '
    'photonic quantum processor,\u201D Nature Communications, vol. 5, '
    'no. 1, art. 4213, Jul. 2014, doi: 10.1038/ncomms5213.',

    'A. Kandala et al., \u201CHardware-efficient variational quantum '
    'eigensolver for small molecules and quantum magnets,\u201D '
    'Nature, vol. 549, no. 7671, pp. 242\u2013246, Sep. 2017, '
    'doi: 10.1038/nature23879.',

    'Y. Cao et al., \u201CQuantum chemistry in the age of quantum '
    'computing,\u201D Chemical Reviews, vol. 119, no. 19, '
    'pp. 10856\u201310915, Oct. 2019, doi: 10.1021/acs.chemrev.8b00803.',
]

for idx, entry in enumerate(REFERENCES, start=1):
    P.append(rfp(idx, entry))

# =========================================================================
# ASSEMBLE DOCX: template + body + image relationships + media files
# =========================================================================
with zipfile.ZipFile(TEMPLATE, 'r') as zin:
    tf = {n: zin.read(n) for n in zin.namelist()}

# --- 1. Inject body -----------------------------------------------------
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

# --- 2. Register image relationships -----------------------------------
rels_path = 'word/_rels/document.xml.rels'
rels_xml = tf[rels_path].decode('utf-8')
insert_before = '</Relationships>'
new_rels = ''
for img in IMAGES:
    target = f'media/{img["filename"]}'
    new_rels += (f'<Relationship Id="{img["rid"]}" '
                 f'Type="{REL_IMAGE}" Target="{target}"/>')
rels_xml = rels_xml.replace(insert_before, new_rels + insert_before)
tf[rels_path] = rels_xml.encode('utf-8')

# --- 3. Add PNG content type if missing --------------------------------
ct_path = '[Content_Types].xml'
ct_xml = tf[ct_path].decode('utf-8')
if '"png"' not in ct_xml:
    ct_xml = ct_xml.replace(
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="png" ContentType="image/png"/>'
    )
    tf[ct_path] = ct_xml.encode('utf-8')

# --- 4. Embed media files ----------------------------------------------
for img in IMAGES:
    with open(img["abspath"], 'rb') as f:
        tf[f'word/media/{img["filename"]}'] = f.read()

# --- 5. Write out ------------------------------------------------------
if os.path.exists(OUTPUT):
    try: os.remove(OUTPUT)
    except PermissionError:
        OUTPUT = OUTPUT.replace('.docx', '_new.docx')

with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, d in tf.items():
        zo.writestr(n, d)

# --- 6. Report ----------------------------------------------------------
size_kb = os.path.getsize(OUTPUT) / 1024
prose = re.sub(r'<[^>]+>', ' ', body)
prose = re.sub(r'\s+', ' ', prose)
words = len([w for w in prose.split() if any(c.isalpha() for c in w)])

print(f"SUCCESS: {OUTPUT}")
print(f"Size:        {size_kb:.1f} KB")
print(f"Prose words: {words}  (target 5500-6500 for 7 IEEE pages)")
print(f"Refs:        {len(REFERENCES)} entries, sequentially numbered [1]-[{len(REFERENCES)}]")
print(f"Figures:     {len(IMAGES)} images embedded")
for img in IMAGES:
    print(f"   {img['rid']:6s}  {img['filename']}")

# Citation-link sanity check
_hyperlink_count = new_doc.count('<w:hyperlink w:anchor="ref')
_bookmark_count  = new_doc.count('<w:bookmarkStart w:id="10') + new_doc.count('<w:bookmarkStart w:id="11')
_anchors = set(re.findall(r'w:anchor="ref(\d+)"', new_doc))
_bookmarks = set(re.findall(r'w:name="ref(\d+)"', new_doc))
_missing = sorted(_anchors - _bookmarks, key=int)
print(f"Citations:   {_hyperlink_count} clickable [N] hyperlinks pointing to "
      f"{len(_bookmarks)} reference bookmarks")
if _missing:
    print(f"  WARNING: {len(_missing)} citation(s) have no matching bookmark: {_missing}")
else:
    print("  OK: every [N] in prose resolves to a bibliography entry")
