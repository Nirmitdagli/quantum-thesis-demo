"""
Build Paper 1 v7 (IEEE conference) - HERO: Balancing CPU+GPU+QPU for
Cost-Energy-Latency Optimization in Hybrid Quantum-Classical Cloud Workloads

Two contrasting workloads: cybersecurity (KDD Cup 99) and molecular
simulation (H2 VQE). Cloud-tier cost analysis with April 2026 pricing.
"""
import os
import re
import zipfile
from PIL import Image

ROOT     = r"C:\Users\ndagl\OneDrive\Desktop\Qunatum Computing\quantum_thesis_demo"
TEMPLATE = os.path.join(ROOT, r"papers\conference-template-letter.docx")
OUTPUT   = os.path.join(ROOT, r"papers\Paper1_IEEE_HybridQCAI_v7.docx")
PLOTS    = os.path.join(ROOT, r"hybrid_simulation\output\plots")

# -------------------------------------------------------------------------
# Strict OOXML namespaces
# -------------------------------------------------------------------------
NS_A   = "http://purl.oclc.org/ooxml/drawingml/main"
NS_PIC = "http://purl.oclc.org/ooxml/drawingml/picture"
REL_IMAGE = "http://purl.oclc.org/ooxml/officeDocument/relationships/image"

EMU_PER_INCH = 914400
COL_WIDTH_EMU = int(3.25 * EMU_PER_INCH)

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
    text = (text.replace('“', '&#x201C;').replace('”', '&#x201D;')
                 .replace('’', '&#x2019;').replace('‘', '&#x2018;'))
    return f'<w:r>{rpr}<w:t{preserve}>{text}</w:t></w:r>'

def mono_run(text):
    """Monospace run for algorithm pseudocode lines."""
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return ('<w:r><w:rPr><w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>'
            '<w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
            f'<w:t xml:space="preserve">{text}</w:t></w:r>')

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

def algorithm_box(title, lines):
    """Render an algorithm as a single-column bordered table with monospace lines."""
    x = para('tablehead', run(title))
    x += ('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
          '<w:tblW w:w="0" w:type="auto"/><w:jc w:val="center"/>'
          '<w:tblBorders>'
          '<w:top w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
          '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
          '<w:left w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
          '<w:right w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
          '</w:tblBorders></w:tblPr>'
          '<w:tblGrid><w:gridCol w:w="252pt"/></w:tblGrid>'
          '<w:tr><w:tc><w:tcPr><w:tcBorders>'
          '<w:top w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
          '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
          '<w:left w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
          '<w:right w:val="single" w:sz="8" w:space="0" w:color="auto"/>'
          '</w:tcBorders></w:tcPr>')
    for ln in lines:
        x += f'<w:p><w:pPr><w:pStyle w:val="BodyText"/></w:pPr>{mono_run(ln)}</w:p>'
    x += '</w:tc></w:tr></w:tbl>'
    return x

# ----------------------------- image helpers ------------------------------
IMAGES = []
NEXT_RID = 100
NEXT_PIC_ID = 1

def add_image(fig_name, caption):
    global NEXT_RID, NEXT_PIC_ID
    abspath = os.path.join(PLOTS, fig_name)
    if not os.path.exists(abspath):
        raise FileNotFoundError(abspath)
    with Image.open(abspath) as im:
        w_px, h_px = im.size
    cx = COL_WIDTH_EMU
    cy = int(cx * h_px / w_px)
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
    cap_xml = para('tablehead', run(caption))
    return drawing + cap_xml

# =========================================================================
# PAGE CONTENT
# =========================================================================
P = []

# ----- TITLE -----
P.append('<w:p><w:pPr><w:pStyle w:val="papertitle"/>'
         '<w:spacing w:before="5pt" w:beforeAutospacing="1" w:after="5pt" w:afterAutospacing="1"/>'
         '</w:pPr>' + run(
            "HERO: Balancing CPU+GPU+QPU for Cost-Energy-Latency "
            "Optimization in Hybrid Quantum-Classical Cloud Workloads"
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
    "—We present Heterogeneous Energy-aware Runtime Orchestrator "
    "(HERO), a measurement framework that balances Central Processing "
    "Unit (CPU), Graphics Processing Unit (GPU), and Quantum Processing "
    "Unit (QPU) tiers in cloud platforms to optimize the joint objective "
    "of cost, energy, and latency for Quantum-Classical Artificial "
    "Intelligence (AI) workloads. We evaluate HERO on two contrasting "
    "case studies: (i) cybersecurity intrusion detection on the Knowledge "
    "Discovery and Data Mining (KDD) Cup 99 dataset, where Random Forest "
    "(RF) achieves an F1 score (harmonic mean of precision and recall) "
    "of 0.998 compared to Quantum Support Vector Machine (QSVM) at "
    "0.667, with QSVM consuming approximately 10,000× more energy "
    "and costing $2.1M per million classifications versus $1.99 for "
    "classical Support Vector Machine (SVM); and (ii) molecular "
    "ground-state estimation of the H2 molecule via Variational Quantum "
    "Eigensolver (VQE), which achieves chemical accuracy (0.007 Hartree "
    "error) but at 854,000× the classical exact-diagonalization "
    "energy at this scale. We derive a workload-aware tier allocation "
    "rule, validate against four classical baselines (SVM, RF, Gradient "
    "Boosting Machine (GBM), K-Nearest Neighbors (KNN)) over 30 "
    "statistical runs per experiment, and project crossover thresholds "
    "where quantum becomes the only feasible path. The framework, "
    "simulator, and measurement scripts are open-source."
)
P.append(para('Abstract', ab))

kw = run("Keywords", bold=True, italic=True)
kw += run("—", bold=True, italic=True)
kw += run(
    "hybrid quantum-classical computing, cloud platforms, energy "
    "measurement, cost-energy-latency optimization, quantum machine "
    "learning, intrusion detection, molecular simulation, VQE, QSVM, NISQ"
)
P.append(para('Keywords', kw))

# =========================== I. INTRODUCTION ================================
P.append(h1("Introduction"))

P.append(bt(
    "Cloud computing now exposes a heterogeneous menu of Artificial "
    "Intelligence (AI) compute tiers. Central Processing Unit (CPU) "
    "instances such as AWS EC2 c7i, Graphics Processing Unit (GPU) "
    "instances built around the NVIDIA H100, and Quantum Processing "
    "Unit (QPU) services such as IBM Quantum and Amazon Braket are "
    "all on-demand, billed per second [1], [2], [25]. The promise of "
    "Quantum Computing (QC) for cybersecurity [4], [6] and molecular "
    "simulation [28], [29], [30] is real, but the cost—in dollars, "
    "in joules, and in latency—is not yet measured side by side "
    "with classical alternatives."
))

P.append(bt(
    "The practical question facing a cloud architect is therefore "
    "concrete: given a workload, how should it be allocated across "
    "CPU, GPU, and QPU tiers to optimize cost, energy, and latency "
    "jointly? Existing studies typically measure a single workload on "
    "a single tier under a single metric. Quantum kernel benchmarks "
    "report accuracy [6] but not cloud cost. Energy-aware computing "
    "studies [23], [24] cover classical deep learning but not quantum "
    "pipelines. Hybrid Quantum-Classical surveys [5] articulate vision "
    "without measured numbers across two contrasting domains."
))

P.append(bt(
    "Our contribution is HERO, a measurement framework that runs the "
    "same orchestration and accounting machinery across CPU+GPU+QPU on "
    "two structurally different workloads: cybersecurity intrusion "
    "detection and molecular ground-state estimation. From the "
    "resulting measurements we derive a workload-aware tier allocation "
    "rule (Algorithm 1) and project the dimensions and qubit counts at "
    "which quantum becomes either the cheaper or the only feasible "
    "path. The framework, the data, and all measurement scripts are "
    "open-source."
))

P.append(bt(
    "The remainder of this paper is organized as follows. Section II "
    "reviews related work. Section III describes the HERO framework "
    "and energy model. Section IV introduces the two workloads. "
    "Section V details the cloud deployment model and pricing. "
    "Section VI describes the experimental setup. Section VII reports "
    "results. Section VIII presents the cross-workload analysis and "
    "the allocation rule. Sections IX through XI cover discussion, "
    "limitations, and conclusions."
))

# =========================== II. RELATED WORK ===============================
P.append(h1("Related Work"))

P.append(bt(
    "Quantum machine learning research has produced two pillars "
    "directly relevant to this study. Havlicek et al. [6] introduced "
    "the ZZ feature map and demonstrated that the resulting quantum "
    "kernel can be consumed by a classical Support Vector Machine "
    "(SVM) [22]. Schuld and Killoran [7] formalized the feature-"
    "Hilbert-space view, tying potential advantage to data "
    "distributions whose induced kernels are hard to simulate "
    "classically. Biamonte et al. [5] survey the broader Quantum "
    "Machine Learning (QML) landscape."
))

P.append(bt(
    "On the molecular side, Peruzzo et al. [28] introduced the "
    "Variational Quantum Eigensolver (VQE), Kandala et al. [29] "
    "demonstrated VQE on real superconducting hardware for H2, LiH, "
    "and BeH2, and Cao et al. [30] survey the broader landscape of "
    "quantum chemistry and identify drug discovery and materials "
    "science as the workloads where Quantum Processing Units (QPUs) "
    "are most likely to deliver advantage."
))

P.append(bt(
    "Energy as a first-class metric is championed by Auffeves [23] "
    "for quantum platforms and by Strubell et al. [24] for classical "
    "Natural Language Processing (NLP). Cybersecurity benchmarking is "
    "anchored by KDD Cup 99 [26] and its NSL-KDD (NSL-KDD—a "
    "refined version of the KDD Cup 99 dataset that removes redundant "
    "records) successor [27]. Cloud orchestration of heterogeneous "
    "accelerators is discussed by Humble et al. [16] and Callison and "
    "Chancellor [15]."
))

P.append(bt(
    "The gap is plain: no prior work performs joint accuracy-latency-"
    "energy measurements across CPU, GPU, and QPU tiers for two "
    "contrasting workloads under a unified cost model. HERO closes "
    "this gap."
))

# =========================== III. HERO FRAMEWORK ============================
P.append(h1("HERO Framework"))

P.append(h2("A. Architecture"))
P.append(bt(
    "HERO is a four-tier system composed of a central Orchestrator "
    "and three execution backends: CPU, GPU, and QPU. The "
    "Orchestrator walks a Directed Acyclic Graph (DAG) of tasks in "
    "topological order, dispatches each task to the backend "
    "indicated by its tier label, and records per-task runtime, "
    "energy, and (after Section V) cloud cost. The QPU backend in "
    "this study is Qiskit Aer [25] in noiseless mode; the framework "
    "is backend-agnostic and can be retargeted to IBM Quantum or "
    "Amazon Braket [22], [25] without changing the task graph. Fig. "
    "1 shows the live architecture."
))

P.append(add_image(
    "hybrid_architecture_live.png",
    "Fig. 1.  HERO four-tier architecture (CPU, GPU, QPU, "
    "Orchestrator) with example workloads."
))

P.append(h2("B. End-to-End Algorithm"))
P.append(bt(
    "Algorithm 1 specifies the entire HERO pipeline—initial "
    "tier allocation, multi-run measurement, aggregation, Pareto "
    "selection, and final recommendation—as a single procedure."
))

P.append(algorithm_box(
    "Algorithm 1: HERO -- End-to-End Workload Allocation, "
    "Measurement, and Selection",
    [
        "Input:  Workload W (type, size n, feature dim d), runs N=30,",
        "        tiers T={CPU, GPU, QPU}",
        "Output: Recommended tier t*, metrics (accuracy, latency,",
        "        energy, cost)",
        "",
        "STEP 1 -- ALLOCATE TIER",
        " 1: if W.type = MOLECULAR_SIM then t <- QPU if n>30 else CPU",
        " 2: if W.type = CLASSICAL_ML  then t <- CPU if d<100",
        "      else (GPU if d<1e4 else MEASURE)",
        " 3: if W.type = COMBINATORIAL then t <- CPU if n<50 else QPU",
        "",
        "STEP 2 -- MEASURE ON EACH TIER (N runs)",
        " 4: for tier in T do",
        " 5:   for run = 1..N do",
        " 6:     start <- clock(); r <- Dispatch(W, tier);",
        "        end <- clock()",
        " 7:     latency <- end - start",
        " 8:     energy  <- latency x P[tier] x PUE     (Eq. 1)",
        " 9:     cost    <- latency x CloudPrice[tier]  (Table III)",
        "10:     accuracy <- Evaluate(r)",
        "11:     record(W, tier, run, accuracy, latency, energy, cost)",
        "",
        "STEP 3 -- AGGREGATE",
        "12: report mean +/- std for accuracy, latency, energy, cost",
        "",
        "STEP 4 -- PARETO SELECTION",
        "13: P <- emptyset",
        "14: for each method m do",
        "15:   if no other m' dominates m on",
        "        (cost, energy, latency, -accuracy)",
        "16:     then P <- P union {m}",
        "",
        "STEP 5 -- RETURN RECOMMENDATION",
        "17: t* <- argmin over P of",
        "      (alpha*cost + beta*energy + gamma*latency",
        "       - delta*accuracy)",
        "18: return t*, statistics, P",
    ]
))

P.append(h2("C. Energy Model"))
P.append(bt(
    "Following Auffeves [23] and Strubell et al. [24], we estimate "
    "per-task energy as:"
))
P.append(eq("E_task = t_task × P_tier × PUE    (1)"))
P.append(bt(
    "where t_task is the measured wall-clock runtime, P_tier is the "
    "representative power draw (P_CPU = 150 W, P_GPU = 300 W, P_QPU "
    "= 20 kW system power for a dilution-refrigerator-based "
    "superconducting platform), and Power Usage Effectiveness (PUE) "
    "= 1.2 accounts for cooling and distribution overhead."
))

# =========================== IV. WORKLOADS ==================================
P.append(h1("Workloads"))

P.append(h2("A. Workload 1 -- Cybersecurity Intrusion Detection"))
P.append(bt(
    "Workload 1 is binary network intrusion classification on the "
    "KDD Cup 99 dataset (10% subset) [26]: 494,021 connections "
    "labeled across 22 attack types. The quantum method is QSVM "
    "with a 4-qubit ZZ feature map (a quantum circuit using Pauli-Z "
    "entangling gates to encode classical data into quantum states) "
    "[6], evaluated on a Qiskit Aer simulator [25]. Classical "
    "baselines are SVM with a Radial Basis Function (RBF) kernel "
    "[22], Random Forest with 100 estimators, Gradient Boosting "
    "with 100 estimators, and KNN with k = 5. We expect classical "
    "to win on this workload because feature dimension after "
    "Principal Component Analysis (PCA) is small (4 components) and "
    "the data is tabular—the regime in which classical "
    "ensemble methods are known to dominate."
))

P.append(h2("B. Workload 2 -- Molecular Ground-State Estimation"))
P.append(bt(
    "Workload 2 is computing the electronic ground-state energy of "
    "the H2 molecule at an internuclear distance of 0.735 Angstrom. "
    "The quantum method is VQE [28] with a hardware-efficient "
    "ansatz (alternating layers of RY rotations and CNOT "
    "entanglers, 4 trainable parameters) driven by the Constrained "
    "Optimization BY Linear Approximation (COBYLA) classical "
    "optimizer. The classical baseline is exact diagonalization of "
    "the 4×4 Hamiltonian via NumPy linear algebra. Quantum is "
    "interesting here because classical state-vector simulation "
    "scales as O(2^n) in the qubit count: H2 itself is trivial, "
    "but FeMoco-class enzymes (~100 qubits of active space) are "
    "intractable for any classical machine that fits in a data "
    "center [29], [30]."
))

# =========================== V. CLOUD DEPLOYMENT ============================
P.append(h1("Cloud Deployment Model"))

P.append(h2("A. Tier-to-Service Mapping"))
P.append(bt(
    "Table III maps each HERO tier to representative cloud services "
    "and their April 2026 on-demand published pricing. We restrict "
    "ourselves to public list pricing—no spot, no commitment "
    "discounts—so the numbers are reproducible by any reader "
    "with a cloud account [31], [32]."
))

P.append(table(
    "TABLE III. Cloud Service Mapping (April 2026 Pricing)",
    ["HERO Tier", "Cloud Service", "Pricing"],
    [
        ["CPU", "AWS EC2 c7i.4xlarge (16 vCPU)",          "$0.7140 per hour"],
        ["GPU", "AWS g5.xlarge (NVIDIA A10G)",            "$1.006 per hour"],
        ["GPU", "AWS p5.48xlarge (8x NVIDIA H100)",       "$98.32 per hour"],
        ["QPU", "IBM Quantum Eagle (127 qubits)",         "$1.60 per second"],
        ["QPU", "AWS Braket Rigetti Ankaa (84 qubits)",   "$0.30/task + $0.0009/shot"],
        ["QPU", "Azure Quantum Quantinuum H2 (56 qubits)","$12.50 per minute"],
    ],
    3
))

P.append(h2("B. Pricing Model"))
P.append(bt(
    "The per-tier dollar cost of a single task is:"
))
P.append(eq("Cost_task = t_task × CloudPrice[tier]    (2)"))
P.append(bt(
    "Per-million-task cost is computed by linear extrapolation "
    "(Table IV). All figures use 2026 published on-demand prices "
    "from [31] and [32], with no spot instances and no enterprise "
    "commitments."
))

P.append(h2("C. Cost vs Energy Trade-offs"))
P.append(bt(
    "Cloud bills include both compute and electricity—the "
    "provider pays the energy bill and passes it through. Optimizing "
    "for dollars alone, energy alone, or latency alone produces "
    "different tier choices, so the joint optimization in Algorithm "
    "1 (Step 5) is essential."
))

# =========================== VI. EXPERIMENTAL SETUP =========================
P.append(h1("Experimental Setup"))

P.append(h2("A. Hardware"))
P.append(bt(
    "All measurements were taken on a local development machine "
    "instrumented with HERO. Quantum circuits run on Qiskit Aer "
    "[25] in noiseless statevector mode; tier-average power numbers "
    "(Section III-C) are used to compute energy."
))

P.append(h2("B. Multi-Run Protocol"))
P.append(bt(
    "Each (workload, method) combination is executed N = 30 times "
    "with different random seeds. We report mean and standard "
    "deviation. Thirty runs is sufficient for stable confidence "
    "intervals on F1 score and for reliable distributions of "
    "VQE final energies."
))

P.append(h2("C. Software Stack"))
P.append(bt(
    "Python 3.13, Qiskit 1.x [25], scikit-learn [22], NumPy, and "
    "Pillow for figure assembly."
))

# =========================== VII. RESULTS ===================================
P.append(h1("Results"))

P.append(h2("A. Cybersecurity Workload (Workload 1)"))
P.append(bt(
    "Table I reports the head-to-head comparison of all five "
    "methods on Workload 1. Random Forest dominates with F1 = 0.998 "
    "at 27.94 J per run; QSVM achieves F1 = 0.667 at 10,320.51 J "
    "per run—roughly four orders of magnitude more energy for "
    "substantially lower accuracy. Fig. 2 visualizes the bar chart "
    "and Fig. 3 the multi-run F1 distribution."
))

P.append(table(
    "TABLE I. Classifier Comparison on Cybersecurity Workload (KDD Cup 99)",
    ["Method", "Tier", "Acc.", "Prec.", "Rec.", "F1", "Run (s)", "E (J)"],
    [
        ["Classical SVM (RBF)", "CPU", "0.9750", "1.0000", "0.9500", "0.9744", "0.0078",   "0.99"],
        ["Random Forest",       "CPU", "0.9970", "0.9992", "0.9970", "0.9981", "0.2218",  "27.94"],
        ["Gradient Boosting",   "CPU", "0.9958", "0.9985", "0.9962", "0.9974", "0.4871",  "61.38"],
        ["KNN (k=5)",           "CPU", "0.9939", "0.9992", "0.9932", "0.9962", "1.7601", "221.77"],
        ["QSVM (ZZ)",           "QPU", "0.8750", "1.0000", "0.5000", "0.6667", "1.4334", "10320.51"],
    ],
    8
))

P.append(add_image(
    "classifier_comparison.png",
    "Fig. 2.  Classifier comparison on KDD Cup 99 cybersecurity "
    "workload (single run)."
))

P.append(add_image(
    "multirun_f1_boxplot.png",
    "Fig. 3.  Multi-run F1 distribution across 30 runs for each "
    "cybersecurity classifier."
))

P.append(h2("B. Molecular Simulation Workload (Workload 2)"))
P.append(bt(
    "Table II reports the H2 ground-state results. VQE reaches "
    "chemical accuracy (0.007 ± 0.012 Hartree error against "
    "the exact-diagonalization reference) but at 854,000× the "
    "classical energy at this trivial scale. The classical method "
    "wins by a wide margin today; the structural argument for "
    "quantum is the O(2^n) RAM wall that exact diagonalization "
    "hits at roughly 30–50 qubits of active space [29]."
))

P.append(table(
    "TABLE II. VQE H2 Molecular Simulation Results (30 Runs)",
    ["Method", "Tier", "E (Ha)", "Err vs Exact (Ha)", "Runtime", "Energy (J)"],
    [
        ["Exact diagonalization", "CPU", "-1.857275",      "0.000000",      "0.28 ms", "0.035"],
        ["VQE (mean +/- std)",    "QPU", "-1.854 +/- 0.013", "0.007 +/- 0.012", "4.14 s", "29832.68"],
    ],
    6
))

P.append(add_image(
    "vqe_convergence.png",
    "Fig. 4.  VQE convergence to ground state of H2 (left) and "
    "30-run final-energy distribution (right)."
))

P.append(h2("C. Cloud Cost Analysis"))
P.append(bt(
    "Table IV translates the per-task runtimes into per-million-"
    "task cloud cost using the pricing in Table III. For "
    "cybersecurity, classical SVM costs $1.99 per million "
    "classifications versus $2.1M for QSVM—a six-order-of-"
    "magnitude gap. For molecular simulation, classical exact "
    "diagonalization costs $0.06 per million H2 instances versus "
    "$2.142M for VQE. Fig. 5 plots the comparison on a logarithmic "
    "axis."
))

P.append(table(
    "TABLE IV. Cloud Cost per 1 Million Tasks (USD)",
    ["Workload", "CPU", "GPU", "QPU"],
    [
        ["Cybersecurity (QSVM)", "$1.99", "$0.28", "$2,100,000.00"],
        ["Molecular Sim (VQE)",  "$0.06", "$0.28", "$2,142,000.00"],
    ],
    4
))

P.append(add_image(
    "cloud_cost_comparison.png",
    "Fig. 5.  Cloud cost per million tasks across CPU/GPU/QPU "
    "tiers for both workloads (April 2026 pricing)."
))

P.append(h2("D. Multi-Run Statistical Validation"))
P.append(bt(
    "Table V summarizes the 30-run statistics across all methods. "
    "Classical methods are highly stable (std ≈ 0). QAOA, "
    "included as a third quantum example for combinatorial tasks, "
    "achieves an approximation ratio of 0.7641 ± 0.0120 across "
    "30 runs—see Fig. 6."
))

P.append(table(
    "TABLE V. Multi-Run Statistics (30 Runs per Method, F1 Mean +/- Std)",
    ["Method", "Tier", "F1 Mean", "F1 Std", "QAOA Approx Ratio"],
    [
        ["SVM",             "CPU", "0.9744", "0.0000", "-"],
        ["Random Forest",   "CPU", "0.9981", "0.0000", "-"],
        ["Gradient Boost.", "CPU", "0.9974", "0.0000", "-"],
        ["KNN (k=5)",       "CPU", "0.9962", "0.0000", "-"],
        ["QSVM",            "QPU", "0.6667", "0.0000", "-"],
        ["QAOA",            "QPU", "-",      "-",      "0.7641 +/- 0.0120"],
    ],
    5
))

P.append(add_image(
    "qaoa_multirun_boxplot.png",
    "Fig. 6.  QAOA approximation ratio across 30 runs (combinatorial "
    "optimization)."
))

# =========================== VIII. CROSS-WORKLOAD ===========================
P.append(h1("Cross-Workload Analysis"))

P.append(h2("A. Two Contrasting Verdicts"))
P.append(bt(
    "Fig. 7 presents the headline cross-workload comparison. The "
    "two workloads return opposite verdicts under the same "
    "framework. Cybersecurity (low feature dimension, tabular "
    "data) is decisively classical: SVM and RF dominate by roughly "
    "10,000× in energy and six orders of magnitude in dollars. "
    "Molecular simulation is also classical at H2 scale today, but "
    "the classical method scales as O(2^n) in qubit count while "
    "VQE scales polynomially—so beyond roughly 30–50 "
    "qubits of active space the classical option simply does not "
    "fit in any data-center RAM [29]. The same framework, two "
    "contrasting verdicts: that contrast is the value."
))

P.append(add_image(
    "cross_workload_comparison.png",
    "Fig. 7.  Two contrasting verdicts: cybersecurity (classical "
    "wins by ~10,000x) vs molecular simulation (quantum needed at "
    "scale)."
))

P.append(h2("B. Pareto Frontier"))
P.append(bt(
    "Fig. 8 shows the Pareto frontier on the cybersecurity "
    "workload. SVM and Random Forest are jointly Pareto-optimal "
    "across the (cost, energy, latency, -accuracy) objective set: "
    "no other method dominates them on all four axes. Algorithm 1 "
    "Step 4 returns this dominated set automatically. For "
    "molecular simulation, classical exact diagonalization Pareto-"
    "dominates VQE for n < 30 qubits; quantum dominates for n > 50 "
    "because no classical implementation exists at that scale."
))

P.append(add_image(
    "pareto_frontier.png",
    "Fig. 8.  Pareto frontier on cybersecurity workload—SVM "
    "and Random Forest are Pareto-optimal."
))

P.append(h2("C. Workload-Aware Allocation Rule"))
P.append(bt(
    "Fig. 9 visualizes the workload-aware allocation rule encoded "
    "in Algorithm 1, Step 1. The thresholds are: N_classical = 30 "
    "qubits for molecular simulation (RAM wall), d_low = 100 "
    "features (CPU regime), d_high = 10,000 features (GPU "
    "regime), and n_classical = 50 nodes for combinatorial "
    "optimization. These numbers are the boundaries at which "
    "either classical performance breaks down or quantum becomes "
    "the only feasible option."
))

P.append(add_image(
    "allocation_decision_tree.png",
    "Fig. 9.  HERO workload-aware allocation rule (Algorithm 1, "
    "Step 1)—visual decision tree."
))

P.append(bt(
    "Fig. 10 projects the cost crossover for cybersecurity kernels: "
    "on fault-tolerant hardware, the quantum kernel’s O(log d) "
    "scaling overtakes classical RBF’s O(d) at feature "
    "dimensions in the thousands—a target for the post-NISQ "
    "era."
))

P.append(add_image(
    "crossover_projection.png",
    "Fig. 10.  Quantum-classical cost crossover projection for "
    "cybersecurity kernels."
))

# =========================== IX. DISCUSSION =================================
P.append(h1("Discussion"))

P.append(h2("A. Where Quantum Wins, Where Classical Wins"))
P.append(bt(
    "Quantum wins on workloads with intrinsically quantum structure: "
    "molecular Hamiltonians whose state spaces grow as 2^n with the "
    "number of qubits [28], [29], [30], or combinatorial graphs "
    "large enough that classical heuristics break down. Classical "
    "wins on tabular data with small feature dimensions, where "
    "decades of optimization in scikit-learn [22] and gradient-"
    "boosted ensembles cannot be matched by a 4-qubit kernel. The "
    "crossover is mathematical, not aspirational."
))

P.append(h2("B. Implications for Cloud Architects"))
P.append(bt(
    "Two practical lessons follow. First, do not pay for QPU when "
    "GPU does the job more cheaply—the cybersecurity numbers "
    "in Table IV are unambiguous. Second, do plan to pay for QPU "
    "when the classical RAM wall is approaching, as it is for any "
    "molecular simulation beyond ~30 qubits of active space [29]. "
    "Use HERO to measure your specific workload before committing "
    "to a tier or a vendor."
))

# =========================== X. LIMITATIONS =================================
P.append(h1("Limitations"))

P.append(bt(
    "1) No real quantum hardware. All quantum experiments ran on "
    "Qiskit Aer [25], a noiseless simulator. Real Quantum Processing "
    "Units (QPUs) add gate errors and decoherence that would lower "
    "QSVM and VQE accuracy further."
))
P.append(bt(
    "2) Small quantum samples. QSVM kernel evaluation scales as "
    "O(n^2) circuits per training set, so we used 120 samples for "
    "the quantum path; H2 itself is only 2 active electrons and 4 "
    "qubits."
))
P.append(bt(
    "3) Dataset choice. KDD Cup 99 [26] dates from 1999. Future "
    "work will extend HERO to Network-based Botnet attacks on IoT "
    "devices (N-BaIoT) and to NSL-KDD [27]."
))
P.append(bt(
    "4) We measure cost, not new algorithms—we use existing "
    "QSVM [6], QAOA [5], Grover [4], and VQE [28] exactly as "
    "published, and measure their cost on this stack."
))
P.append(bt(
    "5) Energy model uses tier averages, not Running Average Power "
    "Limit (RAPL) or NVIDIA Management Library (NVML) telemetry. "
    "Live telemetry is a near-term extension."
))
P.append(bt(
    "6) Cloud pricing snapshot. The pricing in Table III is a "
    "snapshot from April 2026 [31], [32]; vendor competition will "
    "change these numbers, and the framework allows the analysis to "
    "be re-run as prices move."
))

# =========================== XI. CONCLUSION =================================
P.append(h1("Conclusion"))

P.append(bt(
    "We built Heterogeneous Energy-aware Runtime Orchestrator "
    "(HERO), a measurement framework for cloud Quantum-Artificial "
    "Intelligence (AI) workloads that records cost, energy, and "
    "latency across CPU, GPU, and QPU tiers under a single "
    "methodology."
))

P.append(bt(
    "We tested HERO on two contrasting workloads. For cybersecurity "
    "intrusion detection on KDD Cup 99 [26], classical methods win "
    "by approximately 10,000× in energy ($1.99 versus $2.1M "
    "per million classifications). For molecular ground-state "
    "estimation of H2 via the Variational Quantum Eigensolver (VQE) "
    "[28], classical exact diagonalization wins today by 854,000×, "
    "but only quantum scales beyond roughly 30 qubits of active "
    "space because the classical option requires O(2^n) RAM."
))

P.append(bt(
    "From these measurements HERO derives a workload-aware "
    "allocation rule (Algorithm 1) that maps workload type and size "
    "to the optimal cloud tier. The same framework works for any "
    "workload, so researchers and cloud architects can re-measure "
    "as hardware improves and prices change. The key insight is "
    "that quantum is neither always better nor always worse: the "
    "right question is which tier for which workload, and that is "
    "the question HERO answers."
))

# =========================== ACKNOWLEDGMENT =================================
P.append(h1("Acknowledgment"))
P.append(bt(
    "The author thanks the anonymous reviewers for feedback that "
    "improved the experimental methodology and the cross-workload "
    "framing of the results."
))

# =========================== REFERENCES =====================================
P.append(h1("References"))

REFERENCES = [
    'M. A. Nielsen and I. L. Chuang, Quantum Computation and Quantum '
    'Information, 10th ed. Cambridge, U.K.: Cambridge Univ. Press, 2010.',

    'J. Preskill, “Quantum computing in the NISQ era and beyond,” '
    'Quantum, vol. 2, p. 79, Aug. 2018, doi: 10.22331/q-2018-08-06-79.',

    'F. Arute et al., “Quantum supremacy using a programmable '
    'superconducting processor,” Nature, vol. 574, no. 7779, '
    'pp. 505–510, Oct. 2019, doi: 10.1038/s41586-019-1666-5.',

    'K. Bharti et al., “Noisy intermediate-scale quantum algorithms,” '
    'Rev. Mod. Phys., vol. 94, no. 1, art. 015004, Feb. 2022, '
    'doi: 10.1103/RevModPhys.94.015004.',

    'J. Biamonte, P. Wittek, N. Pancotti, P. Rebentrost, N. Wiebe, and '
    'S. Lloyd, “Quantum machine learning,” Nature, vol. 549, '
    'no. 7671, pp. 195–202, Sep. 2017, doi: 10.1038/nature23474.',

    'V. Havlicek, A. D. Corcoles, K. Temme, A. W. Harrow, A. Kandala, '
    'J. M. Chow, and J. M. Gambetta, “Supervised learning with '
    'quantum-enhanced feature spaces,” Nature, vol. 567, no. 7747, '
    'pp. 209–212, Mar. 2019, doi: 10.1038/s41586-019-0980-2.',

    'M. Schuld and N. Killoran, “Quantum machine learning in feature '
    'Hilbert spaces,” Phys. Rev. Lett., vol. 122, no. 4, '
    'art. 040504, Feb. 2019, doi: 10.1103/PhysRevLett.122.040504.',

    'H.-Y. Huang, M. Broughton, M. Mohseni, R. Babbush, S. Boixo, '
    'H. Neven, and J. R. McClean, “Power of data in quantum '
    'machine learning,” Nature Commun., vol. 12, no. 1, art. '
    '2631, May 2021, doi: 10.1038/s41467-021-22539-9.',

    'E. Farhi, J. Goldstone, and S. Gutmann, “A quantum approximate '
    'optimization algorithm,” arXiv:1411.4028, Nov. 2014.',

    'M. Cerezo et al., “Variational quantum algorithms,” '
    'Nature Rev. Phys., vol. 3, no. 9, pp. 625–644, Sep. 2021, '
    'doi: 10.1038/s42254-021-00348-9.',

    'L. Zhou, S.-T. Wang, S. Choi, H. Pichler, and M. D. Lukin, '
    '“Quantum approximate optimization algorithm: Performance, '
    'mechanism, and implementation on near-term devices,” '
    'Phys. Rev. X, vol. 10, no. 2, art. 021067, Jun. 2020, '
    'doi: 10.1103/PhysRevX.10.021067.',

    'L. K. Grover, “A fast quantum mechanical algorithm for '
    'database search,” in Proc. 28th Annu. ACM Symp. Theory '
    'Comput. (STOC), Philadelphia, PA, USA, May 1996, pp. 212–219, '
    'doi: 10.1145/237814.237866.',

    'M. Grassl, B. Langenberg, M. Roetteler, and R. Steinwandt, '
    '“Applying Grover’s algorithm to AES: Quantum resource '
    'estimates,” in Proc. 7th Int. Workshop Post-Quantum '
    'Cryptography (PQCrypto), LNCS 9606. Cham, Switzerland: '
    'Springer, 2016, pp. 29–43, doi: 10.1007/978-3-319-29360-8_3.',

    'J. R. McClean, J. Romero, R. Babbush, and A. Aspuru-Guzik, '
    '“The theory of variational hybrid quantum-classical '
    'algorithms,” New J. Phys., vol. 18, no. 2, art. 023023, '
    'Feb. 2016, doi: 10.1088/1367-2630/18/2/023023.',

    'A. Callison and N. Chancellor, “Hybrid quantum-classical '
    'algorithms in the noisy intermediate-scale quantum era and '
    'beyond,” Phys. Rev. A, vol. 106, no. 1, art. 010101, '
    'Jul. 2022, doi: 10.1103/PhysRevA.106.010101.',

    'T. S. Humble, A. McCaskey, D. I. Lyakh, M. Gowrishankar, '
    'A. Frisch, and T. Monz, “Quantum computers for high-'
    'performance computing,” IEEE Micro, vol. 41, no. 5, '
    'pp. 15–23, Sep./Oct. 2021, doi: 10.1109/MM.2021.3099140.',

    'H. Suryotrisongko and Y. Musashi, “Review of cybersecurity '
    'research topics, taxonomy and challenges: Interdisciplinary '
    'perspective,” in Proc. IEEE 16th Int. Conf. e-Business '
    'Engineering (ICEBE), Shanghai, China, Oct. 2019, '
    'pp. 162–167, doi: 10.1109/ICEBE.2019.00038.',

    'E. Payares and J. C. Martinez-Santos, “Quantum machine '
    'learning for intrusion detection of distributed denial of '
    'service attacks: A comparative overview,” in Quantum '
    'Computing, Communication, and Simulation, Proc. SPIE, '
    'vol. 11699, pp. 35–49, Mar. 2021, doi: 10.1117/12.2593297.',

    'N. Kilber, D. Kaestle, and S. Wagner, “Cybersecurity for '
    'quantum computing,” arXiv:2110.14701, Oct. 2021.',

    'M. Tavallaee, E. Bagheri, W. Lu, and A. A. Ghorbani, “A '
    'detailed analysis of the KDD CUP 99 data set,” in Proc. '
    'IEEE Symp. Comput. Intell. Security Defense Appl. (CISDA), '
    'Ottawa, ON, Canada, Jul. 2009, pp. 53–58, '
    'doi: 10.1109/CISDA.2009.5356528.',

    'I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, “Toward '
    'generating a new intrusion detection dataset and intrusion '
    'traffic characterization,” in Proc. 4th Int. Conf. Inf. '
    'Syst. Secur. Privacy (ICISSP), Funchal, Portugal, Jan. 2018, '
    'pp. 108–116, doi: 10.5220/0006639801080116.',

    'C. Cortes and V. Vapnik, “Support-vector networks,” '
    'Mach. Learn., vol. 20, no. 3, pp. 273–297, Sep. 1995, '
    'doi: 10.1007/BF00994018.',

    'A. Auffeves, “Quantum technologies need a quantum energy '
    'initiative,” PRX Quantum, vol. 3, no. 2, art. 020101, '
    'May 2022, doi: 10.1103/PRXQuantum.3.020101.',

    'E. Strubell, A. Ganesh, and A. McCallum, “Energy and policy '
    'considerations for deep learning in NLP,” in Proc. 57th '
    'Annu. Meeting Assoc. Comput. Linguistics (ACL), Florence, '
    'Italy, Jul. 2019, pp. 3645–3650, doi: 10.18653/v1/P19-1355.',

    'Qiskit contributors, “Qiskit: An open-source framework for '
    'quantum computing,” Zenodo, 2023, '
    'doi: 10.5281/zenodo.2573505.',

    'M. Tavallaee, E. Bagheri, W. Lu, and A. Ghorbani, “A detailed '
    'analysis of the KDD CUP 99 data set,” in Proc. IEEE Symp. '
    'CISDA, Ottawa, Canada, Jul. 2009, pp. 1–6, '
    'doi: 10.1109/CISDA.2009.5356528.',

    'S. Revathi and A. Malathi, “A detailed analysis on NSL-KDD '
    'dataset using various machine learning techniques for intrusion '
    'detection,” Int. J. Eng. Res. Technol., vol. 2, no. 12, '
    'pp. 1848–1853, Dec. 2013.',

    'A. Peruzzo et al., “A variational eigenvalue solver on a '
    'photonic quantum processor,” Nature Communications, vol. 5, '
    'no. 1, art. 4213, Jul. 2014, doi: 10.1038/ncomms5213.',

    'A. Kandala et al., “Hardware-efficient variational quantum '
    'eigensolver for small molecules and quantum magnets,” '
    'Nature, vol. 549, no. 7671, pp. 242–246, Sep. 2017, '
    'doi: 10.1038/nature23879.',

    'Y. Cao et al., “Quantum chemistry in the age of quantum '
    'computing,” Chemical Reviews, vol. 119, no. 19, '
    'pp. 10856–10915, Oct. 2019, doi: 10.1021/acs.chemrev.8b00803.',

    'Amazon Web Services, “Amazon Braket pricing,” AWS, 2026. '
    '[Online]. Available: https://aws.amazon.com/braket/pricing/',

    'IBM Corporation, “IBM Quantum pricing,” IBM, 2026. '
    '[Online]. Available: https://www.ibm.com/quantum/pricing',
]

for idx, entry in enumerate(REFERENCES, start=1):
    P.append(rfp(idx, entry))

# =========================================================================
# ASSEMBLE DOCX
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

_table_count = body.count('<w:tbl>')

print(f"SUCCESS: {OUTPUT}")
print(f"Size:        {size_kb:.1f} KB")
print(f"Prose words: {words}")
print(f"Refs:        {len(REFERENCES)} entries, sequentially numbered [1]-[{len(REFERENCES)}]")
print(f"Figures:     {len(IMAGES)} images embedded")
print(f"Tables:      {_table_count} (includes algorithm box)")
for img in IMAGES:
    print(f"   {img['rid']:6s}  {img['filename']}")

# Citation-link sanity check
_hyperlink_count = new_doc.count('<w:hyperlink w:anchor="ref')
_anchors = set(re.findall(r'w:anchor="ref(\d+)"', new_doc))
_bookmarks = set(re.findall(r'w:name="ref(\d+)"', new_doc))
_missing = sorted(_anchors - _bookmarks, key=int)
print(f"Citations:   {_hyperlink_count} clickable [N] hyperlinks pointing to "
      f"{len(_bookmarks)} reference bookmarks")
if _missing:
    print(f"  WARNING: {len(_missing)} citation(s) have no matching bookmark: {_missing}")
else:
    print("  OK: every [N] in prose resolves to a bibliography entry")
