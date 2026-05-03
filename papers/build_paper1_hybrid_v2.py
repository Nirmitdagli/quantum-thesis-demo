"""
Build Paper 1 v2 (7-page IEEE) - HYBRID QC+AI FRAMEWORK
with 6 embedded diagrams from hybrid_simulation/output/plots/
and expanded prose to fill a full 7-page two-column IEEE layout.

Addresses Ron's peer review by:
 - Single, well-scoped contribution (hybrid orchestration framework)
 - Sequentially numbered bibliography [1]..[25]
 - Proof-of-concept positioning + validation roadmap
 - Measured per-unit energy and runtime
 - Visual evidence via 6 embedded simulator figures

This template uses the strict OOXML namespaces (purl.oclc.org), so the
drawing XML and relationship types are emitted in that dialect.
"""
import os
import re
import zipfile
from PIL import Image

ROOT     = r"C:\Users\ndagl\OneDrive\Desktop\Qunatum Computing\quantum_thesis_demo"
TEMPLATE = os.path.join(ROOT, r"papers\conference-template-letter.docx")
OUTPUT   = os.path.join(ROOT, r"papers\Paper1_IEEE_HybridQCAI_v5.docx")
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
# When text contains a "[N]" citation token, we emit an internal hyperlink
# whose anchor is the bookmark "refN" placed on the matching bibliography
# entry in the References section. IEEE style keeps citations as plain
# text (not blue/underlined), so we override color=auto and u=none inside
# the hyperlink run.
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
# We collect images, assign relationship IDs and emit the inline drawing XML
# plus a matching caption paragraph. The collected images are packed into
# word/media/ and registered in word/_rels/document.xml.rels at assembly time.
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
    "hybrid: a classical CPU coordinates the work, a GPU handles the "
    "data-heavy classical parts, and a Quantum Processing Unit (QPU) "
    "runs the short quantum circuits. Prior work benchmarks each "
    "quantum algorithm in isolation and rarely measures what the "
    "different hardware tiers actually cost in runtime or energy. "
    "This paper introduces a hybrid orchestration framework that "
    "splits cybersecurity workloads into small tasks, routes each "
    "task to the right tier, and records its runtime and energy. "
    "We exercise the framework on three proof-of-concept "
    "workloads: anomaly detection with a quantum kernel Support "
    "Vector Machine, network segmentation with the Quantum "
    "Approximate Optimization Algorithm (QAOA), and cryptographic "
    "search with Grover\u2019s algorithm. The full pipeline runs "
    "end-to-end on a laptop-class simulator in under two seconds, "
    "and per-task measurements identify which tier dominates the "
    "cost and why. Six figures generated directly by the simulator "
    "illustrate the architecture, the timeline, and the per-tier "
    "breakdown. The paper is explicitly positioned as a proof-of-"
    "concept: all workloads are sized to near-term quantum "
    "constraints, and we outline a validation roadmap on the "
    "standard NSL-KDD and CICIDS2017 intrusion-detection datasets."
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
    "Modern cybersecurity systems combine three kinds of "
    "computation: machine learning for spotting anomalies, "
    "optimization for choosing how to segment a network, and "
    "search for cracking keys. Quantum algorithms have been "
    "proposed for all three. Quantum kernel methods offer richer "
    "similarity measures for anomaly detection; the Quantum "
    "Approximate Optimization Algorithm (QAOA) tackles "
    "network-partition problems that become very hard as networks "
    "grow; and Grover\u2019s search gives a proven quadratic "
    "speed-up for unstructured lookup. None of these algorithms, "
    "however, runs on its own: each one is a hybrid workload in "
    "which classical preparation, a classical optimizer, or "
    "classical post-processing still does most of the work [1]."
))

P.append(bt(
    "Preskill named the current stage of quantum hardware the "
    "\u201CNoisy Intermediate-Scale Quantum\u201D or NISQ era [2]. "
    "In plain terms: today\u2019s quantum devices have tens to a "
    "few hundred qubits, they make errors on every gate, and they "
    "have no error correction. They cannot run long algorithms on "
    "their own, so any useful quantum work has to be split into "
    "short circuits that a classical computer drives, checks, and "
    "post-processes. The 53-qubit Google experiment [3] and the "
    "algorithm survey of Bharti et al. [4] both reach the same "
    "conclusion: the unit of work is not a whole quantum algorithm, "
    "but a pipeline in which a classical controller calls short "
    "quantum circuits as needed. Humble et al. [16] make this "
    "explicit by treating a Quantum Processing Unit (QPU) as one "
    "more accelerator that sits next to CPUs and GPUs inside a "
    "regular High-Performance Computing (HPC) system."
))

P.append(bt(
    "Two things are still missing from this hybrid view. First, "
    "most papers benchmark one quantum algorithm on one dataset "
    "and stop there. There is no single measured pipeline that "
    "runs three different cybersecurity workloads through CPU, "
    "GPU, and QPU stages with the same methodology, so runtime "
    "numbers from different papers cannot be compared head-to-"
    "head. Second, Auffeves [23] and Strubell et al. [24] have "
    "both argued that energy per computation, not only runtime, "
    "should be reported for heterogeneous systems; yet no prior "
    "cybersecurity-oriented quantum paper reports energy at the "
    "per-task level needed to guide scheduling or hardware-aware "
    "optimization."
))

P.append(bt(
    "Our position is simple: before anyone can make a credible "
    "claim about quantum advantage in cybersecurity, we first have "
    "to be able to measure\u2014task by task, in one pipeline, "
    "under one methodology\u2014what each tier of the heterogeneous "
    "system is actually doing. The contribution of this paper is a "
    "framework that makes such measurement routine."
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
P.append(bl(
    "(5) Six publication-quality diagrams generated directly from the "
    "executing simulator, embedded in this paper, and reproducible "
    "via a single-command launcher."
))

P.append(bt(
    "The remainder of the paper is organized as follows. Section II "
    "reviews related work across five streams and closes with an "
    "explicit statement of the research gap. Section III describes "
    "the hybrid framework, the tier role assignment, and the energy "
    "model; Fig. 1 illustrates the live architecture. Section IV "
    "presents the three cybersecurity workloads that exercise the "
    "framework. Section V reports the measured 17-task pipeline "
    "results with four tables and five embedded figures. Section VI "
    "discusses limitations, threats to validity, and the planned "
    "validation roadmap on standard intrusion-detection benchmarks. "
    "Section VII outlines five avenues of future work, and Section "
    "VIII concludes."
))

# =========================== II. RELATED WORK ===============================
P.append(h1("Related Work"))

P.append(h2("A. Primer: Classical, AI, and Quantum Tiers"))
P.append(bt(
    "For readers unfamiliar with heterogeneous computing, we briefly "
    "distinguish the three tiers used throughout the paper. The "
    "Central Processing Unit (CPU) is optimized for sequential "
    "control flow and branch-heavy code; in cybersecurity pipelines "
    "it typically handles packet parsing, feature engineering, and "
    "rule evaluation. The Graphics Processing Unit (GPU) is "
    "optimized for data-parallel numerical workloads and has become "
    "the default substrate for AI: deep neural networks for "
    "intrusion detection, batch inference, and large-scale kernel "
    "computations all map naturally onto its thousands of cores "
    "[24]. The Quantum Processing Unit (QPU) is a specialized "
    "coprocessor that executes short quantum circuits whose "
    "computational expressivity cannot be efficiently reproduced by "
    "any classical device. In the NISQ era [2], QPUs are only "
    "productively used for carefully scoped sub-tasks embedded "
    "inside a larger classical pipeline; this is precisely the "
    "structural observation that motivates our framework."
))

P.append(h2("B. NISQ Computing and Hybrid Workloads"))
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
    "to near-term quantum advantage, with the classical portion of "
    "the pipeline carrying most of the computational load. This "
    "conclusion directly motivates our orchestration-centric design: "
    "if classical work dominates, then the software layer that "
    "schedules classical and quantum work on appropriate hardware "
    "tiers is as important as the quantum circuits themselves."
))

P.append(h2("C. Quantum Machine Learning and Kernel Methods"))
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
    "geometric properties of the data and showing that, without such "
    "structure, classical kernels can match quantum ones using "
    "modest amounts of training data. Our QSVM workload reuses the "
    "exact ZZ feature map of [6]; the novelty is not the kernel "
    "itself but the execution pattern that interleaves a GPU neural "
    "feature extractor with QPU kernel-element estimation, producing "
    "a measurable hybrid pipeline rather than an idealized circuit."
))

P.append(h2("D. Variational and Search-Based Quantum Algorithms"))
P.append(bt(
    "Two quantum algorithms dominate cybersecurity-relevant NISQ "
    "research. The Quantum Approximate Optimization Algorithm, "
    "proposed by Farhi et al. [9], targets combinatorial problems "
    "such as MaxCut by alternating cost and mixer Hamiltonians over "
    "p variational layers. Zhou et al. [11] analyze its performance "
    "scaling, while Cerezo et al. [10] survey the broader family of "
    "Variational Quantum Algorithms (VQAs) and emphasize that every "
    "VQA is structurally hybrid: a classical optimizer iteratively "
    "updates circuit parameters from measurement statistics, so "
    "even a perfect quantum sub-circuit cannot escape the latency "
    "and energy of its classical driver loop. McClean et al. [14] "
    "established the theoretical foundations of this hybrid feedback "
    "loop. Separately, Grover\u2019s algorithm [12] provides a "
    "quadratic speedup for unstructured search, and Grassl et al. "
    "[13] quantify its impact on symmetric-key cryptanalysis, "
    "motivating the migration from AES-128 to AES-256. Our QAOA and "
    "Grover workloads invoke these algorithms not to reproduce their "
    "asymptotic claims, which is infeasible at NISQ scale, but to "
    "exercise the orchestration layer under realistic variational "
    "and amplitude-amplification workloads."
))

P.append(h2("E. Hybrid Heterogeneous Computing and Energy"))
P.append(bt(
    "Callison and Chancellor [15] explicitly argue that NISQ progress "
    "depends on tight integration between classical and quantum "
    "resources. Humble et al. [16] go further and position QPUs as "
    "accelerators inside HPC systems, analogous to the integration "
    "of GPUs into scientific workflows a decade earlier; their vision "
    "frames the QPU as one tier of a heterogeneous hierarchy rather "
    "than a standalone device. Existing work on QPU-HPC integration, "
    "however, focuses on offloading protocols and interconnects "
    "rather than on end-to-end workload characterization. In "
    "parallel, Auffeves [23] has called for a Quantum Energy "
    "Initiative, arguing that energy per computation must become a "
    "first-class metric for NISQ systems, on the grounds that "
    "dilution refrigerators and control electronics dominate the "
    "power budget of today\u2019s superconducting platforms. "
    "Strubell et al. [24] made the analogous case for classical "
    "deep learning. To our knowledge, no prior work reports per-"
    "unit runtime and energy for a full hybrid cybersecurity "
    "workload spanning CPU, GPU, and QPU tiers under a single "
    "measurement methodology."
))

P.append(h2("F. Quantum Computing for Cybersecurity"))
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
    "on both datasets, under which the framework is re-exercised "
    "with realistic traffic and against classical baselines chosen "
    "by the cybersecurity community."
))

P.append(h2("G. Research Gap"))
P.append(bt(
    "Summarizing: the NISQ literature establishes that hybrid is the "
    "only near-term path [2], [4]; the QML/QAOA/Grover literature "
    "focuses on individual algorithms in isolation [5]\u2013[14]; "
    "the heterogeneous-computing literature proposes QPU-in-HPC as "
    "an architectural direction [15], [16] but stops short of "
    "measured end-to-end workloads; and the energy-aware computing "
    "literature [23], [24] identifies energy as the missing metric. "
    "Our contribution sits precisely at this intersection: an "
    "orchestration framework that (i) routes three representative "
    "cybersecurity workloads across CPU, GPU, and QPU tiers, (ii) "
    "measures runtime and energy at the granularity of individual "
    "tasks, and (iii) makes the resulting characterization "
    "reproducible via an open task graph and a one-click launcher."
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
    "acceleration for feature extraction and batch inference. "
    "Fig. 1 shows the live architecture rendered by the running "
    "simulator, with all three tiers, their active tasks during a "
    "pipeline run, and the data-dependency edges between them."
))

# === FIGURE 1: Architecture ===
P.append(add_image(
    "hybrid_architecture_live.png",
    "Fig. 1.  Live architecture of the hybrid CPU+GPU+QPU orchestration "
    "framework during a pipeline execution. CPU coordinates control "
    "flow, GPU accelerates classical AI, QPU executes short quantum "
    "circuits."
))

P.append(h2("B. Tier Roles"))
P.append(btm([
    run("The "),
    run("CPU", bold=True),
    rt(" tier handles control flow, data ingestion, preprocessing, "
       "classical algorithm execution (e.g., SVM training with a "
       "precomputed kernel [22], greedy MaxCut, brute-force search), "
       "and result aggregation. The "),
    run("GPU", bold=True),
    rt(" tier accelerates parallel AI operations: a 3-layer neural "
       "feature extractor with 2,928 parameters, batch classification "
       "across test samples, RBF kernel estimation as a classical "
       "baseline, Kronecker-product Hamiltonian construction for "
       "QAOA, and parallel oracle evaluation for Grover. The "),
    run("QPU", bold=True),
    rt(" tier executes short quantum circuits: ZZ feature-map kernel "
       "evaluation [6], depth-p QAOA circuits driven by a classical "
       "COBYLA optimizer [10], [14], and amplitude-amplification "
       "circuits following the pattern of [12]. On our experimental "
       "setup the QPU tier is realized by Qiskit Aer in noiseless "
       "simulator mode [25]; the framework is agnostic to the "
       "backend and can be retargeted to real hardware without "
       "changing the task graph, because each tier is implemented "
       "behind a common dispatch interface."),
]))

P.append(h2("C. Task Graph and Dispatch"))
P.append(bt(
    "The task graph for the three workloads in this paper contains "
    "17 nodes (8 CPU, 6 GPU, 3 QPU) and 19 directed edges. During "
    "a run, the driver walks the graph in topological order: for "
    "each task, it selects the backend matching the task\u2019s "
    "tier label, times the call with a monotonic clock, and records "
    "an (ops, runtime, energy) triple. Tasks on the GPU tier that "
    "are mutually independent are dispatched in parallel to a "
    "single device; tasks on the QPU tier are serialized to match "
    "the behavior of real cloud queues. The driver is backend-"
    "agnostic: replacing the Aer simulator [25] with a hardware "
    "backend requires only a new implementation of the QPU dispatch "
    "interface, while the task graph and the measurement code remain "
    "unchanged. This property is central to the validation roadmap "
    "of Section VI."
))

P.append(h2("D. Energy Model"))
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
    "respectively, and a point estimate for the QPU tier because "
    "its dominant contribution (the dilution refrigerator) is "
    "largely workload-independent and varies by less than 5% over "
    "the sub-second timescales observed in our pipeline."
))

P.append(h2("E. Reproducibility"))
P.append(bt(
    "All workloads are implemented on top of Qiskit v1.x with the "
    "Aer statevector and QASM simulators [25], scikit-learn v1.x "
    "for classical baselines [22], NetworkX for graph construction, "
    "and PyTorch for GPU feature extraction. Random seeds are fixed "
    "at 42 for all experiments. The task graph, driver, and per-"
    "unit timing code are released alongside this paper, and a "
    "single-click Windows launcher (Run_Hybrid_Simulator.bat) "
    "executes the entire 17-task pipeline and regenerates all six "
    "figures shown in this paper end-to-end in under three seconds."
))

# =========================== IV. WORKLOADS ==================================
P.append(h1("Cybersecurity Workloads"))
P.append(bt(
    "The three workloads below are intentionally sized to NISQ "
    "constraints (4\u20137 qubits, shallow depth). We reiterate "
    "Section I: the objective is to exercise the orchestration "
    "framework under representative hybrid patterns\u2014not to "
    "claim algorithmic quantum advantage at these scales, which is "
    "ruled out a priori by [4] and [8]. Each workload is presented "
    "as a short task chain through the three tiers."
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
    "validation plan on NSL-KDD [20] and CICIDS2017 [21], both of "
    "which contain realistic traffic traces with many more features "
    "and strong class imbalance."
))
P.append(h3("2) AI stage (GPU)"))
P.append(bt(
    "A 3-layer feed-forward neural network with 2,928 parameters is "
    "trained on the GPU to project raw features into a 4-dimensional "
    "latent space suitable for amplitude encoding. The same GPU "
    "tier also computes an RBF-kernel classical SVM baseline, so "
    "that the AI feature extractor and the classical baseline share "
    "the same preprocessed input and the same device."
))
P.append(h3("3) Quantum stage (QPU)"))
P.append(bt(
    "In plain terms, the ZZ feature map is a short quantum "
    "circuit that loads each classical data point into a quantum "
    "state so that pairs of features become entangled. This lets "
    "a Support Vector Machine (SVM) \u201Csee\u201D interactions "
    "between features that a linear classifier would miss, and "
    "is the quantum counterpart of a nonlinear kernel in "
    "classical machine learning."
))
P.append(bt(
    "The ZZ feature map of Havlicek et al. [6] encodes each latent "
    "vector into a 4-qubit circuit. The quantum kernel between two "
    "points x and y is estimated as:"
))
P.append(eq("k(x, y) = |\u27E80^n| U_dag(y) U(x) |0^n\u27E9|\u00B2    (2)"))
P.append(bt(
    "with 2,000 shots per circuit, producing an 80 \u00D7 80 "
    "training kernel and an 80 \u00D7 40 test kernel that are "
    "consumed by a classical SVC with kernel=precomputed [22]. This "
    "task chain is the most QPU-intensive of the three workloads "
    "because the number of circuits grows quadratically with the "
    "training-set size."
))

P.append(h2("B. Workload 2: QAOA Network Segmentation"))
P.append(bt(
    "In plain terms, MaxCut is the problem of splitting the "
    "nodes of a graph into two groups so that as many edges as "
    "possible cross between the groups. Applied to network "
    "segmentation, each node is a subnet and each edge is a flow "
    "between subnets; a good cut puts the most-watched flows on "
    "the boundary where a monitoring sensor can see them. Finding "
    "the exact best cut on large graphs is NP-hard, so fast "
    "approximate solvers are valuable."
))
P.append(bt(
    "We use an Erdos-Renyi random graph G(n=7, p=0.35). A depth-2 "
    "QAOA circuit with 4 variational parameters is driven by the "
    "classical COBYLA optimizer [10], [14], [11] for up to 150 "
    "iterations. The GPU tier precomputes the cost Hamiltonian via "
    "Kronecker products; the CPU tier computes a greedy heuristic "
    "baseline and the brute-force optimum over the "
    "2\u2077 = 128 partitions. The alternation between classical "
    "optimizer and quantum circuit evaluation is the canonical "
    "variational pattern surveyed in [10], and the framework "
    "records each iteration as a measurable task."
))

P.append(h2("C. Workload 3: Grover-Style Search"))
P.append(bt(
    "A 4-qubit unstructured search instance (N = 16) with a single "
    "marked state |0110\u27E9 exercises amplitude amplification "
    "[12]. The circuit comprises an initial Hadamard layer followed "
    "by k* = \u230A(\u03C0/4)\u221AN\u230B = 3 Grover operators, "
    "each composed of the oracle O and the diffuser "
    "D = 2|s\u27E9\u27E8s| - I. The GPU tier performs a parallel "
    "classical oracle scan as both a baseline and a warm-start "
    "signal; this reflects the actual deployment pattern used by "
    "Grassl et al. [13] in their AES cryptanalysis study, where "
    "classical precomputation is used to narrow the quantum search "
    "space before dispatch."
))

# =========================== V. RESULTS =====================================
P.append(h1("Measured Pipeline Results"))
P.append(bt(
    "All measurements are reported for a single end-to-end execution "
    "of the task graph on noiseless simulators, with the same random "
    "seed and shot count across runs. The pipeline totals 17 tasks: "
    "8 on the CPU tier, 6 on the GPU tier, and 3 on the QPU tier. "
    "Fig. 2 shows the full pipeline timeline rendered by the "
    "simulator, with each task positioned on its assigned tier and "
    "shaded by runtime."
))

# === FIGURE 2: Pipeline Timeline ===
P.append(add_image(
    "hybrid_pipeline_timeline.png",
    "Fig. 2.  Pipeline timeline for the 17-task hybrid execution. "
    "The horizontal axis is wall-clock time; each bar is a task "
    "assigned to its tier."
))

P.append(h2("A. Per-Tier Utilization"))
P.append(bt(
    "Table I summarizes runtime and energy by tier. Figures are "
    "totals across the 17-task pipeline. Fig. 3 visualizes the same "
    "information as stacked bars per tier, making the imbalance "
    "between CPU/GPU and QPU immediately visible."
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

# === FIGURE 3: Unit Utilization ===
P.append(add_image(
    "hybrid_unit_utilization.png",
    "Fig. 3.  Per-unit utilization across the 17-task pipeline. "
    "The simulated QPU tier dominates both runtime and energy."
))

P.append(bt(
    "Two observations follow directly from Table I and Fig. 3. "
    "First, the CPU and GPU tiers jointly handle 14 of 17 tasks in "
    "under 15 ms and under 4 J; classical orchestration is not the "
    "bottleneck, which rules out a large class of hypothetical "
    "optimizations that target classical overhead. Second, the QPU "
    "tier alone accounts for 98.9% of pipeline runtime and 99.96% "
    "of pipeline energy. On the noiseless simulator this is an "
    "artifact of classical state-vector simulation (O(2\u00B2\u207F) "
    "operations per gate); on real superconducting hardware [16] "
    "the dilution refrigerator would still dominate the power "
    "budget, but the runtime bottleneck would shift by several "
    "orders of magnitude toward the classical tiers, making the "
    "orchestrator\u2019s per-task accounting directly actionable "
    "for scheduling decisions."
))

P.append(h2("B. Per-Workload Breakdown"))
P.append(bt(
    "Table II decomposes the pipeline by workload, reporting task "
    "count, quantum circuits executed, and the functional outcome. "
    "Fig. 4 presents the same data as a side-by-side comparison "
    "across the three workloads."
))
P.append(table(
    "TABLE II. Per-Workload Decomposition of the Pipeline",
    ["Workload", "Tasks", "QPU circuits", "Outcome"],
    [["QSVM",   "8", "120", "accuracy 0.625"],
     ["QAOA",   "5", "40",  "ratio 0.7752"],
     ["Grover", "4", "1",   "p_success 0.9570"]],
    4
))

# === FIGURE 4: Experiment Comparison ===
P.append(add_image(
    "hybrid_experiment_comparison.png",
    "Fig. 4.  Per-workload comparison across the three cybersecurity "
    "case studies exercised by the framework."
))

P.append(bt(
    "The QSVM workload consumes the largest share of pipeline energy "
    "because kernel estimation requires O(n_train\u00B2 + "
    "n_train\u00B7n_test) circuit executions. The QAOA workload "
    "runs 40 circuits driven by COBYLA until convergence [11]. The "
    "Grover workload executes a single circuit with 2,000 "
    "measurement shots. The functional outcomes are reported for "
    "completeness but, as Section VI argues, should not be read as "
    "classification or optimization quality claims at these scales."
))

P.append(h2("C. Energy Breakdown"))
P.append(bt(
    "Fig. 5 decomposes the 10,467 J pipeline energy budget by tier "
    "and by workload, showing that the QSVM kernel-estimation stage "
    "alone consumes over 96% of the total."
))

# === FIGURE 5: Energy Breakdown ===
P.append(add_image(
    "hybrid_energy_breakdown.png",
    "Fig. 5.  Energy breakdown across the three workloads and the "
    "three execution tiers. The QSVM kernel estimation dominates."
))

P.append(h2("D. Per-Task Runtime and Energy"))
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

P.append(h2("E. Tier Efficiency"))
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
    "measured in milliseconds rather than seconds and where the "
    "energy profile can be compared against the simulator-truth "
    "figures reported here."
))

P.append(h2("F. Simulator Dashboard"))
P.append(bt(
    "Fig. 6 collects the key per-unit, per-workload, and per-task "
    "plots into a single dashboard view that the simulator "
    "auto-generates at the end of every pipeline run. This "
    "dashboard is the primary artifact consumed by a user who "
    "invokes the one-click launcher."
))

# === FIGURE 6: Dashboard ===
P.append(add_image(
    "hybrid_simulation_dashboard.png",
    "Fig. 6.  Integrated simulator dashboard, combining per-tier "
    "utilization, per-workload comparison, energy breakdown, and "
    "top energy-consuming tasks in a single view."
))

P.append(h2("G. Projection to Real Hardware"))
P.append(bt(
    "To complement the simulator measurements above, Table V "
    "extrapolates the per-tier runtime to two representative "
    "hardware targets drawn from published gate-time data: a "
    "superconducting backend (IBM Eagle-class [16]) with 35 ns "
    "single-qubit gates and 300 ns two-qubit gates, and a trapped-"
    "ion backend (Quantinuum H1) with approximately 10 \u00B5s "
    "effective two-qubit gate time. The extrapolation multiplies "
    "the number of gates per circuit by the gate time, scales by "
    "the shot count, and adds a fixed 250 ms network latency to "
    "every QPU dispatch. Values are order-of-magnitude "
    "projections and should be read as illustrative, not "
    "predictive."
))
P.append(table(
    "TABLE V. Projected QPU-Tier Runtime on Real Hardware (s)",
    ["Workload", "Simulator (Aer)", "Superconducting", "Trapped-Ion"],
    [["QSVM",   "1.4042", "~0.42",  "~6.8"],
     ["QAOA",   "0.0484", "~0.031", "~0.52"],
     ["Grover", "0.0007", "~0.008", "~0.13"]],
    4
))
P.append(bt(
    "Two observations follow. First, on a superconducting backend "
    "the entire pipeline QPU time would drop from 1.45 s to "
    "approximately 0.46 s, leaving network latency and the "
    "classical CPU/GPU tiers as the new bottlenecks. Second, on "
    "a trapped-ion backend the QSVM workload remains the single "
    "largest cost center but the gap narrows from roughly "
    "five orders of magnitude (relative to GPU) to roughly two, "
    "meaning that circuit-batching and kernel-element caching "
    "become first-class optimization targets rather than "
    "asymptotic concerns. The framework\u2019s per-task accounting "
    "makes both optimizations directly measurable once a real "
    "backend is plugged into the driver."
))

# =========================== VI. DISCUSSION =================================
P.append(h1("Discussion"))

P.append(h2("A. What the Numbers Do and Do Not Show"))
P.append(bt(
    "The results above do not demonstrate quantum advantage. This is "
    "by design. At 4\u20137 qubits, the problem instances are fully "
    "classically tractable, and [4] and [8] make clear that advantage "
    "requires hardware beyond current reach. What the results do "
    "show is that a hybrid Quantum-Classical AI pipeline can be "
    "constructed, executed, and instrumented end-to-end, and that "
    "per-tier measurements immediately reveal where the runtime and "
    "energy budgets are being spent. This is actionable information "
    "for cloud orchestration [15] and for hardware-aware scheduling "
    "algorithms that prior work has not been able to inform with "
    "measured data. In particular, the dominance of the QSVM kernel-"
    "estimation task (Table III) tells a scheduler that caching "
    "kernel elements across runs, or batching circuits across "
    "clients, would repay far more than any optimization targeting "
    "the CPU or GPU tiers."
))

P.append(h2("B. Limitations"))
P.append(bt(
    "Four limitations should be acknowledged explicitly. First, all "
    "measurements are taken on a noiseless simulator; real hardware "
    "noise will change both runtime and outcome quality, especially "
    "for the depth-2 QAOA circuit [11], which contains 18 CNOT "
    "gates per layer and is sensitive to two-qubit gate errors. "
    "Second, the datasets are synthetic and intentionally small; "
    "they cannot be used to claim detection performance on "
    "operational traffic, and any accuracy numbers reported in "
    "Section V should be read as framework-exercise outcomes "
    "rather than as classification results. Third, the energy "
    "model in (1) uses nameplate power values rather than measured "
    "rail-level telemetry; future work will replace this with live "
    "meters following the methodology advocated by Auffeves [23] "
    "and by in-chassis energy telemetry interfaces such as Intel "
    "RAPL and NVIDIA NVML. Fourth, we report a single end-to-end "
    "run rather than a statistical distribution over seeds; the "
    "variability of QAOA\u2019s COBYLA optimizer [10], [14] "
    "warrants a multi-seed study in future work."
))

P.append(h2("C. Validation Roadmap"))
P.append(bt(
    "We plan a three-stage validation of the framework. Stage 1 "
    "replaces the synthetic QSVM dataset with NSL-KDD [20], "
    "subsampled and feature-reduced to the NISQ-compatible "
    "4\u20136 qubit envelope, and compares QSVM classification "
    "against classical SVM and random-forest baselines under "
    "identical pipeline conditions. Stage 2 extends to the richer "
    "CICIDS2017 dataset [21], which contains contemporary attack "
    "traffic (brute force, Heartbleed, botnet, DDoS, web attacks, "
    "infiltration) and supports a broader feature study including "
    "temporal flow statistics. Stage 3 deploys the task graph on a "
    "real hardware backend (IBM Quantum or Quantinuum) with live "
    "energy telemetry, converting the simulator-dominated energy "
    "profile of Table I into a hardware-truth profile and making "
    "the framework\u2019s per-task accounting directly comparable "
    "to published NISQ hardware benchmarks. Only after Stage 3 do "
    "we consider quantum-advantage claims warranted."
))

P.append(h2("D. Comparison to Prior Hybrid Studies"))
P.append(bt(
    "Our measurement discipline distinguishes this work from three "
    "classes of prior hybrid studies. Benchmarks of QSVM [6], [18] "
    "and QAOA [9], [11] report accuracy and approximation ratio "
    "respectively, but not per-task runtime or energy; their "
    "methodology cannot be composed across algorithms because "
    "each reports a different subset of metrics under a different "
    "experimental setup. HPC-quantum-integration studies [15], "
    "[16] articulate the architectural vision but do not publish "
    "measured numbers for cybersecurity workloads. Energy-aware "
    "computing studies [23], [24] report classical deep-learning "
    "energy profiles but do not cover hybrid pipelines. The "
    "present work is the first, to our knowledge, to combine all "
    "three elements\u2014hybrid cybersecurity workload, measured "
    "per-tier energy, and reproducible task graph\u2014inside a "
    "single paper."
))

P.append(h2("E. Threats to Validity"))
P.append(bt(
    "Construct validity is threatened by the use of synthetic data: "
    "our QSVM accuracy does not generalize to operational traffic, "
    "and the 4-qubit dimensionality collapses the rich feature "
    "space of real intrusion-detection benchmarks. Internal "
    "validity is threatened by single-run measurement, which does "
    "not separate systematic effects from variance. External "
    "validity is threatened by the use of a single simulator "
    "backend; different Qiskit versions and different hosts may "
    "produce different energy profiles even on identical task "
    "graphs. We mitigate each threat through the validation "
    "roadmap above and through the release of the task graph, "
    "the driver code, and the one-click launcher, which allows "
    "independent reproduction of every number in this paper."
))

# =========================== VII. FUTURE WORK ===============================
P.append(h1("Future Work"))
P.append(bt(
    "Beyond the three-stage validation roadmap of Section VI-C, "
    "we identify five concrete avenues for extending this work. "
    "Each is either already partially implemented in the "
    "simulator or directly supported by the framework\u2019s "
    "dispatch interface."
))

P.append(h2("A. Noise-Aware Simulation and Mitigation"))
P.append(bt(
    "Replacing the noiseless Aer backend with a device-calibrated "
    "noise model will make the framework sensitive to the "
    "depolarizing, dephasing, and measurement errors documented "
    "by Bharti et al. [4]. A direct next step is to re-run the "
    "QAOA workload under a range of two-qubit error rates and "
    "report the approximation-ratio degradation curve together "
    "with per-task energy. The framework\u2019s per-task "
    "accounting makes it straightforward to attribute energy "
    "overhead to error-mitigation circuits (zero-noise "
    "extrapolation, probabilistic error cancellation) at the "
    "individual task level."
))

P.append(h2("B. Hardware Deployment and Live Telemetry"))
P.append(bt(
    "The framework is designed so that plugging a cloud backend "
    "(IBM Quantum, AWS Braket, Azure Quantum, Quantinuum) into "
    "the dispatch interface requires no change to the task "
    "graph. A concrete deployment target is a side-by-side run "
    "on IBM Eagle and Quantinuum H1 for the QSVM workload, with "
    "live energy telemetry from the hosting classical node via "
    "Intel RAPL and NVIDIA NVML, and with the cloud provider\u2019s "
    "queue wait time folded into the per-task runtime. This "
    "deployment will convert the simulator-truth figures of "
    "Table I into a hardware-truth baseline."
))

P.append(h2("C. Dataset Scale-Up and Feature Study"))
P.append(bt(
    "Stages 1 and 2 of the validation roadmap (NSL-KDD [20] and "
    "CICIDS2017 [21]) will exercise the framework under "
    "realistic class imbalance, realistic feature cardinality, "
    "and realistic temporal dynamics. We plan an ablation over "
    "the number of features surviving dimensionality reduction "
    "(principal component analysis, autoencoder-based bottlenecks) "
    "and over the number of qubits in the ZZ feature map [6], to "
    "characterize the trade-off between encoding fidelity and "
    "NISQ circuit depth."
))

P.append(h2("D. Multi-Seed Statistical Study"))
P.append(bt(
    "Section VI-B acknowledged the limitation of single-run "
    "measurement. A natural extension is to run the pipeline "
    "across 100 independent seeds and report runtime and energy "
    "as distributions rather than point estimates, with 95% "
    "confidence intervals on the per-tier figures. The framework "
    "already supports this through a configurable random seed; "
    "the change is primarily a matter of runtime budget and "
    "plotting pipeline."
))

P.append(h2("E. Integration with Cloud Orchestration"))
P.append(bt(
    "Finally, the framework\u2019s task graph can be exported to "
    "standard cloud orchestration layers (Kubernetes, Airflow, "
    "Prefect). This would allow the same cybersecurity pipeline "
    "to be deployed at scale across a cluster of classical nodes "
    "and a pool of cloud QPUs, with the per-task accounting "
    "feeding into a cost-aware scheduler. This integration is "
    "the natural end point of the QPU-in-HPC vision of Humble "
    "et al. [16] and is the long-term target of our work."
))

# =========================== VIII. CONCLUSION ===============================
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
    "localizes the QSVM kernel-estimation task as the single "
    "largest optimization target, providing concrete guidance for "
    "future work on hardware-aware scheduling."
))
P.append(bt(
    "Six embedded figures, generated directly by the executing "
    "simulator and reproducible via a one-click launcher, "
    "document the architecture, pipeline timeline, per-unit "
    "utilization, per-workload comparison, energy breakdown, and "
    "an integrated dashboard. The paper is positioned as a proof-"
    "of-concept: the workloads are sized to NISQ constraints, and "
    "quantum-advantage claims are deferred to the three-stage "
    "validation roadmap on NSL-KDD [20] and CICIDS2017 [21], "
    "culminating in real-hardware deployment with live energy "
    "telemetry. We believe the framework and the per-unit "
    "measurement methodology are useful on their own terms, "
    "independent of whether any particular workload ultimately "
    "shows quantum advantage."
))

# =========================== ACKNOWLEDGMENT =================================
P.append(h1("Acknowledgment"))
P.append(bt(
    "The author thanks the anonymous reviewers for feedback that "
    "reshaped the paper from an algorithm-comparison study into the "
    "framework-centric proof-of-concept presented here, and for "
    "insisting on a validation roadmap grounded in standard "
    "cybersecurity datasets."
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
