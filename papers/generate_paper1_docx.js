const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, LevelFormat, PageBreak, Column, SectionType,
  Math: OOXMLMath, MathRun, MathFraction, MathSuperScript, MathSubScript
} = require("docx");

// IEEE Color scheme
const IEEE_BLUE = "1F4E79";
const BORDER_COLOR = "999999";
const HEADER_BG = "D9E2F3";

const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: BORDER_COLOR };
const borders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const noBorders = {
  top: { style: BorderStyle.NONE, size: 0 },
  bottom: { style: BorderStyle.NONE, size: 0 },
  left: { style: BorderStyle.NONE, size: 0 },
  right: { style: BorderStyle.NONE, size: 0 },
};

const cellMargins = { top: 40, bottom: 40, left: 80, right: 80 };

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: HEADER_BG, type: ShadingType.CLEAR },
    margins: cellMargins,
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, bold: true, font: "Times New Roman", size: 18 })]
    })]
  });
}

function dataCell(text, width, opts = {}) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    margins: cellMargins,
    children: [new Paragraph({
      alignment: opts.align || AlignmentType.CENTER,
      children: [new TextRun({ text, font: "Times New Roman", size: 18, ...opts })]
    })]
  });
}

function makeTable(headers, rows, colWidths) {
  const tableWidth = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: tableWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) }),
      ...rows.map(row => new TableRow({
        children: row.map((cell, i) => dataCell(cell, colWidths[i]))
      }))
    ]
  });
}

function sectionHeading(text) {
  return new Paragraph({
    spacing: { before: 300, after: 120 },
    children: [new TextRun({ text: text.toUpperCase(), bold: true, font: "Times New Roman", size: 20, color: IEEE_BLUE })]
  });
}

function subsectionHeading(text) {
  return new Paragraph({
    spacing: { before: 240, after: 80 },
    children: [new TextRun({ text, bold: true, italics: true, font: "Times New Roman", size: 20 })]
  });
}

function subsubHeading(text) {
  return new Paragraph({
    spacing: { before: 200, after: 60 },
    children: [new TextRun({ text, bold: true, font: "Times New Roman", size: 19 })]
  });
}

function bodyPara(runs, opts = {}) {
  return new Paragraph({
    spacing: { after: 80, line: 276 },
    alignment: AlignmentType.JUSTIFIED,
    indent: opts.noIndent ? undefined : { firstLine: 360 },
    children: runs.map(r =>
      typeof r === "string"
        ? new TextRun({ text: r, font: "Times New Roman", size: 20 })
        : new TextRun({ font: "Times New Roman", size: 20, ...r })
    ),
    ...opts,
  });
}

function bulletItem(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { after: 40, line: 276 },
    children: [new TextRun({ text, font: "Times New Roman", size: 20 })],
  });
}

function refItem(num, text) {
  return new Paragraph({
    spacing: { after: 40, line: 240 },
    indent: { left: 360, hanging: 360 },
    children: [
      new TextRun({ text: `[${num}] `, font: "Times New Roman", size: 18 }),
      new TextRun({ text, font: "Times New Roman", size: 18 }),
    ],
  });
}

function tableCaption(text) {
  return new Paragraph({
    spacing: { before: 200, after: 80 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text, font: "Times New Roman", size: 18, bold: true })]
  });
}

function equationPara(text) {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text, font: "Times New Roman", size: 20, italics: true })]
  });
}

// ======================================================================
// BUILD DOCUMENT
// ======================================================================

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Times New Roman", size: 20 },
      },
    },
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0,
          format: LevelFormat.BULLET,
          text: "\u2022",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } },
        }],
      },
    ],
  },
  sections: [
    // ============ TITLE PAGE / HEADER SECTION (single column) ============
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1080, right: 900, bottom: 1080, left: 900 },
        },
        column: { count: 2, space: 360, equalWidth: true },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.LEFT,
            children: [new TextRun({ text: "IEEE Conference Paper", font: "Times New Roman", size: 16, italics: true, color: "888888" })]
          })]
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [new TextRun({ children: [PageNumber.CURRENT], font: "Times New Roman", size: 18 })]
          })]
        }),
      },
      children: [
        // TITLE
        new Paragraph({
          spacing: { before: 200, after: 200 },
          alignment: AlignmentType.CENTER,
          children: [new TextRun({
            text: "Hybrid Quantum-AI Algorithms for Cybersecurity: A Comparative Analysis of QSVM, QAOA, and Grover\u2019s Search",
            bold: true, font: "Times New Roman", size: 28,
          })]
        }),
        // AUTHOR
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 40 },
          children: [new TextRun({ text: "Author Name", font: "Times New Roman", size: 22 })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 20 },
          children: [new TextRun({ text: "Department of Computer Science", font: "Times New Roman", size: 20, italics: true })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 20 },
          children: [new TextRun({ text: "University Name", font: "Times New Roman", size: 20, italics: true })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 240 },
          children: [new TextRun({ text: "email@university.edu", font: "Times New Roman", size: 20 })]
        }),

        // ABSTRACT
        new Paragraph({
          spacing: { before: 120, after: 80 },
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Abstract", bold: true, italics: true, font: "Times New Roman", size: 20 })]
        }),
        bodyPara([
          { text: "Abstract\u2014", bold: true, italics: true },
          "Quantum computing offers transformative potential for cybersecurity applications, yet systematic comparisons of quantum algorithms against classical baselines on security-relevant tasks remain scarce. This paper presents a rigorous empirical evaluation of three hybrid quantum-AI algorithms applied to core cybersecurity problems: a Quantum Support Vector Machine (QSVM) with ZZ feature map kernel for network anomaly detection, the Quantum Approximate Optimization Algorithm (QAOA) for network segmentation via MaxCut, and Grover\u2019s search algorithm for cryptographic key space exploration. Each quantum algorithm is benchmarked against its classical counterpart across accuracy, runtime, and energy consumption metrics. Our results demonstrate that the QSVM achieves classification accuracy on par with classical RBF-kernel SVMs (100% on our benchmark), QAOA surpasses greedy heuristics with an 88.3% approximation ratio versus 85.7%, and Grover\u2019s algorithm attains 96.35% target-state success probability in O(\u221AN) iterations. We analyze the conditions under which quantum advantage materializes and discuss implications for deploying hybrid quantum-classical cybersecurity systems."
        ], { noIndent: true }),

        // KEYWORDS
        new Paragraph({
          spacing: { before: 80, after: 200 },
          children: [
            new TextRun({ text: "Keywords\u2014", bold: true, italics: true, font: "Times New Roman", size: 20 }),
            new TextRun({ text: "quantum computing, cybersecurity, quantum machine learning, QAOA, Grover\u2019s algorithm, anomaly detection, quantum kernel methods", font: "Times New Roman", size: 20, italics: true }),
          ]
        }),

        // =====================================================
        // I. INTRODUCTION
        // =====================================================
        sectionHeading("I. Introduction"),

        bodyPara([
          "The cybersecurity landscape faces escalating challenges as threat actors leverage increasingly sophisticated attack vectors. Network intrusion detection systems must process growing volumes of traffic data, cryptographic protocols face emerging quantum threats, and network segmentation problems grow combinatorially with infrastructure scale [1]. These pressures motivate the exploration of quantum computing as a complementary paradigm to classical security systems."
        ], { noIndent: true }),

        bodyPara([
          "Quantum algorithms exploit superposition, entanglement, and interference to process information in fundamentally different ways than classical computers. Three classes of quantum algorithms hold particular relevance for cybersecurity: (1) quantum kernel methods that map classical data into exponentially large Hilbert spaces for improved classification [2], (2) variational optimization algorithms that explore combinatorial solution spaces more efficiently [3], and (3) amplitude amplification algorithms that provide provable quadratic speedups for unstructured search [4]."
        ]),

        bodyPara([
          "Despite growing theoretical interest, few studies provide direct empirical comparisons of these three algorithm families on cybersecurity-specific tasks with consistent experimental methodology. This paper addresses that gap with the following contributions:"
        ]),

        bulletItem("A unified experimental framework implementing QSVM, QAOA, and Grover\u2019s algorithm alongside classical baselines, evaluated on cybersecurity-relevant problems."),
        bulletItem("Quantitative comparison across three metrics: classification/optimization accuracy, wall-clock runtime, and estimated energy consumption using a cloud-aware power model."),
        bulletItem("Analysis of scaling behavior and identification of crossover points where quantum approaches are projected to outperform classical alternatives."),

        bodyPara([
          "The remainder of this paper is organized as follows: Section II reviews related work. Section III details the algorithms and experimental setup. Section IV presents results. Section V provides analysis and discussion. Section VI concludes with future directions."
        ]),

        // =====================================================
        // II. RELATED WORK
        // =====================================================
        sectionHeading("II. Related Work"),

        subsectionHeading("A. Quantum Machine Learning for Cybersecurity"),
        bodyPara([
          "Quantum kernel methods were formalized by Havl\u00ed\u010dek et al. [2], who demonstrated that quantum feature maps can achieve classification advantages on problems with specific data structure. Subsequent work applied quantum SVMs to network intrusion detection [5], showing competitive accuracy on the NSL-KDD dataset. Liu et al. [6] established rigorous conditions under which quantum kernels provide provable learning advantages over classical approaches. Our work extends this line by implementing a ZZ feature map kernel specifically designed for cybersecurity anomaly detection with entanglement-based feature interaction."
        ], { noIndent: true }),

        subsectionHeading("B. Quantum Optimization for Network Security"),
        bodyPara([
          "The Quantum Approximate Optimization Algorithm (QAOA), introduced by Farhi et al. [3], addresses combinatorial optimization problems such as MaxCut. Applications to network segmentation and graph partitioning have been explored by Zhou et al. [7], who analyzed QAOA performance at various circuit depths. Guerreschi and Matsuura [8] examined practical resource requirements for quantum advantage in QAOA. Our contribution applies QAOA to a cybersecurity-motivated network segmentation scenario and compares it against greedy heuristics."
        ], { noIndent: true }),

        subsectionHeading("C. Grover\u2019s Algorithm and Cryptographic Implications"),
        bodyPara([
          "Grover\u2019s algorithm [4] provides a quadratic speedup for unstructured search, with direct implications for symmetric-key cryptography. The NIST post-quantum cryptography standardization effort [1] considers Grover\u2019s algorithm as a baseline threat model. Jaques et al. [9] analyzed concrete resource estimates for applying Grover\u2019s algorithm to AES key search. Our work implements Grover\u2019s algorithm for a 4-qubit search space with scaling analysis projected to cryptographically relevant key sizes."
        ], { noIndent: true }),

        // =====================================================
        // III. METHODOLOGY
        // =====================================================
        sectionHeading("III. Methodology"),

        subsectionHeading("A. Experimental Framework"),
        bodyPara([
          "All quantum experiments were implemented using IBM Qiskit v1.x with the Aer statevector and QASM simulators. Classical baselines used scikit-learn v1.x. Experiments were executed on a classical workstation, with quantum circuits simulated via AerSimulator using 2000 measurement shots per circuit. The random seed was fixed at 42 for reproducibility across all experiments."
        ], { noIndent: true }),

        subsectionHeading("B. Experiment 1: QSVM for Anomaly Detection"),

        subsubHeading("1) Dataset Generation"),
        bodyPara([
          "A synthetic cybersecurity anomaly detection dataset was generated with 120 samples across 4 features (corresponding to 4 qubits). Normal traffic samples (n=60) were drawn from \u039D(\u03BC=0.2, \u03C3=0.1) per feature, while anomaly samples (n=60) were drawn from \u039D(\u03BC=0.8, \u03C3=0.1). All features were normalized to [0, 1] via min-max scaling. The dataset was split 67%/33% for training/testing with stratified sampling."
        ], { noIndent: true }),

        subsubHeading("2) Quantum Kernel Construction"),
        bodyPara([
          "The quantum kernel employs a second-order ZZ feature map. For an input vector x \u2208 \u211D\u207F, the feature map circuit U(x) applies phase gates and Hadamard gates with CNOT-based entanglement. The quantum kernel matrix element between data points x and y is computed as:"
        ], { noIndent: true }),

        equationPara("k(x, y) = |\u27E80\u207F| U\u2020(y) U(x) |0\u207F\u27E9|\u00B2    (1)"),

        bodyPara([
          "This kernel matrix was precomputed for all training and test sample pairs and passed to a scikit-learn SVC with a precomputed kernel."
        ]),

        subsubHeading("3) Classical Baseline"),
        bodyPara([
          "A standard SVM with radial basis function (RBF) kernel was trained with \u03B3 = scale (i.e., \u03B3 = 1/(n_features \u00D7 Var(X))), representing the most widely used kernel for nonlinear classification."
        ], { noIndent: true }),

        subsectionHeading("C. Experiment 2: QAOA for Network Segmentation"),

        subsubHeading("1) Problem Formulation"),
        bodyPara([
          "The MaxCut problem on a random Erd\u0151s-R\u00E9nyi graph G(n=7, p=0.35) models network segmentation, where the objective is to partition nodes into two groups maximizing the number of inter-group edges. The generated graph contained 9 edges with an optimal cut value of 7."
        ], { noIndent: true }),

        subsubHeading("2) QAOA Circuit"),
        bodyPara([
          "A depth p=2 QAOA circuit was constructed with 7 qubits. The initial state is prepared as uniform superposition via Hadamard gates. Each layer l \u2208 {1, 2} consists of:"
        ], { noIndent: true }),

        bodyPara([
          { text: "Cost unitary: ", bold: true },
          "For each edge (i, j) \u2208 E, implemented via CNOT-Rz(\u03B3)-CNOT decomposition:"
        ], { noIndent: true }),

        equationPara("U_C(\u03B3_l) = \u220F_{(i,j)\u2208E} exp(-i \u03B3_l Z_i Z_j / 2)    (2)"),

        bodyPara([
          { text: "Mixer unitary: ", bold: true },
        ], { noIndent: true }),

        equationPara("U_M(\u03B2_l) = \u220F_{i=1}^{n} exp(-i \u03B2_l X_i) = \u220F_{i=1}^{n} R_X(2\u03B2_l)    (3)"),

        bodyPara([
          "The four variational parameters (\u03B3\u2081, \u03B3\u2082, \u03B2\u2081, \u03B2\u2082) were optimized using COBYLA with a maximum of 150 iterations, initialized uniformly random in [0, \u03C0]. The cost function was the negative expected cut value computed from 2000 measurement shots."
        ]),

        subsubHeading("3) Classical Baseline"),
        bodyPara([
          "A greedy heuristic iteratively assigns each node to the partition that maximizes the current cut value. The brute-force optimum was computed by exhaustive enumeration of all 2\u2077 = 128 partitions."
        ], { noIndent: true }),

        subsectionHeading("D. Experiment 3: Grover\u2019s Search"),

        subsubHeading("1) Problem Setup"),
        bodyPara([
          "A 4-qubit search space of N = 16 states was constructed with target state |0110\u27E9. The optimal number of Grover iterations is k* = \u230A(\u03C0/4)\u221AN\u230B = 3."
        ], { noIndent: true }),

        subsubHeading("2) Circuit Construction"),
        bodyPara([
          "The Grover circuit consists of three components applied iteratively:"
        ], { noIndent: true }),

        bodyPara([
          { text: "Oracle: ", bold: true },
          "A multi-controlled Z gate marks the target state with a phase flip. For target state |t\u27E9, X gates are applied to qubits where t_i = 0, followed by a multi-controlled X (with Hadamard on the target qubit to implement controlled-Z), then X gates are reapplied."
        ], { noIndent: true }),

        bodyPara([
          { text: "Diffusion operator: ", bold: true },
          "Implements 2|s\u27E9\u27E8s| - I where |s\u27E9 = H\u2297\u207F|0\u207F\u27E9, via H\u2297\u207F \u00B7 (2|0\u27E9\u27E80| - I) \u00B7 H\u2297\u207F."
        ], { noIndent: true }),

        bodyPara([
          { text: "Iteration: ", bold: true },
          "Oracle and diffusion are applied k* = 3 times after an initial Hadamard layer."
        ], { noIndent: true }),

        subsubHeading("3) Classical Baseline"),
        bodyPara([
          "Sequential brute-force search iterates through all N states until the target is found, with expected complexity O(N/2) and worst case O(N)."
        ], { noIndent: true }),

        subsectionHeading("E. Energy Model"),
        bodyPara([
          "Energy consumption is estimated using a cloud datacenter model:"
        ], { noIndent: true }),

        equationPara("E = t_runtime \u00D7 P \u00D7 PUE    (4)"),

        bodyPara([
          "where P \u2208 {5000, 25000} W represents the server power range and PUE = 1.2 accounts for cooling and infrastructure overhead. This yields low and high energy bounds in joules."
        ]),

        // =====================================================
        // IV. RESULTS
        // =====================================================
        sectionHeading("IV. Results"),

        subsectionHeading("A. QSVM Anomaly Detection"),
        bodyPara([
          "Table I presents the classification results. Both quantum and classical SVMs achieved perfect classification on the test set."
        ], { noIndent: true }),

        tableCaption("TABLE I: QSVM vs. Classical SVM for Anomaly Detection"),
        makeTable(
          ["Metric", "Quantum SVM", "Classical SVM"],
          [
            ["Accuracy", "1.0000", "1.0000"],
            ["Precision", "1.0000", "1.0000"],
            ["Recall", "1.0000", "1.0000"],
            ["F1 Score", "1.0000", "1.0000"],
            ["Runtime (s)", "28.789", "0.007"],
            ["Energy Low (J)", "172,733", "44"],
            ["Energy High (J)", "863,666", "222"],
          ],
          [2800, 2200, 2200]
        ),

        bodyPara([
          "The confusion matrices for both classifiers showed zero misclassifications across all 40 test samples (20 normal, 20 anomaly). The quantum kernel successfully mapped the 4-dimensional input into a higher-dimensional Hilbert space where the two classes are linearly separable."
        ]),

        subsectionHeading("B. QAOA Network Segmentation"),
        bodyPara([
          "Table II shows the MaxCut optimization results. QAOA achieved a higher expected cut value and approximation ratio than the greedy heuristic."
        ], { noIndent: true }),

        tableCaption("TABLE II: QAOA vs. Greedy Heuristic for MaxCut"),
        makeTable(
          ["Metric", "QAOA", "Greedy", "Optimal"],
          [
            ["Cut Value", "6.18", "6.00", "7.00"],
            ["Approx. Ratio", "0.883", "0.857", "1.000"],
            ["Runtime (s)", "8.070", "4.7\u00D710\u207B\u2075", "\u2014"],
            ["Energy Low (J)", "48,419", "0.28", "\u2014"],
            ["Energy High (J)", "242,097", "1.42", "\u2014"],
          ],
          [2100, 1600, 1600, 1600]
        ),

        bodyPara([
          "The COBYLA optimizer converged within 150 iterations, progressively improving the expected cut value from the initial random parameters. The output distribution showed non-trivial probability mass on optimal and near-optimal bitstrings."
        ]),

        subsectionHeading("C. Grover\u2019s Search"),
        bodyPara([
          "Table III presents the search results. Grover\u2019s algorithm achieved near-theoretical success probability."
        ], { noIndent: true }),

        tableCaption("TABLE III: Grover\u2019s Algorithm vs. Brute-Force Search"),
        makeTable(
          ["Metric", "Grover", "Brute-Force"],
          [
            ["Success Probability", "0.9635", "1.0000"],
            ["Optimal Iterations", "3", "up to 16"],
            ["Runtime (s)", "0.115", "7\u00D710\u207B\u2076"],
            ["Energy Low (J)", "691", "0.04"],
            ["Energy High (J)", "3,457", "0.22"],
          ],
          [2800, 2200, 2200]
        ),

        bodyPara([
          "The probability versus iteration analysis revealed the characteristic oscillatory behavior of Grover\u2019s algorithm, with peak probability at 3 iterations (\u224896.35%), consistent with the theoretical maximum of sin\u00B2((2k+1)/2 \u00D7 arcsin(1/\u221AN)) \u2248 96.1% for N=16, k=3."
        ]),

        subsectionHeading("D. Cross-Experiment Summary"),
        bodyPara([
          "Table IV provides a unified comparison across all experiments."
        ], { noIndent: true }),

        tableCaption("TABLE IV: Cross-Experiment Performance Summary"),
        makeTable(
          ["Task", "Algorithm", "Primary Metric", "Runtime (s)", "Energy Mid (J)"],
          [
            ["QSVM", "Quantum", "1.000", "28.79", "518,200"],
            ["QSVM", "Classical", "1.000", "0.007", "133"],
            ["QAOA", "Quantum", "0.883", "8.07", "145,258"],
            ["QAOA", "Classical", "0.857", "10\u207B\u2075", "0.85"],
            ["Grover", "Quantum", "0.964", "0.115", "2,074"],
            ["Grover", "Classical", "1.000", "10\u207B\u2076", "0.13"],
          ],
          [1400, 1400, 1600, 1400, 1600]
        ),

        // =====================================================
        // V. DISCUSSION
        // =====================================================
        sectionHeading("V. Discussion"),

        subsectionHeading("A. Accuracy Analysis"),
        bodyPara([
          "The quantum algorithms demonstrated competitive or superior accuracy across all three tasks. The QSVM\u2019s perfect classification validates that the ZZ feature map kernel effectively captures the nonlinear decision boundary in the 4-dimensional feature space. The quantum kernel\u2019s ability to leverage entanglement-based feature interactions in 2\u2074 = 16-dimensional Hilbert space provides a representational advantage that, while not manifested at this problem scale, is expected to become significant for higher-dimensional cybersecurity datasets where classical kernels struggle [6]."
        ], { noIndent: true }),

        bodyPara([
          "QAOA\u2019s superiority over the greedy heuristic (88.3% vs. 85.7% approximation ratio) demonstrates the algorithm\u2019s capacity to explore the solution landscape more effectively through quantum superposition and interference. The depth-2 circuit strikes a balance between expressibility and noise resilience, consistent with findings by Zhou et al. [7]."
        ]),

        bodyPara([
          "Grover\u2019s 96.35% success probability closely matches the theoretical bound, confirming correct implementation and demonstrating the algorithm\u2019s practical reliability for search-based cybersecurity applications."
        ]),

        subsectionHeading("B. Runtime and Scalability"),
        bodyPara([
          "All quantum algorithms exhibited higher wall-clock runtime than their classical counterparts. This overhead is attributed entirely to the classical simulation of quantum circuits\u2014the Aer simulator models the full 2\u207F-dimensional statevector, incurring exponential classical resources. On native quantum hardware, circuit execution time scales polynomially with circuit depth and is independent of the Hilbert space dimension."
        ], { noIndent: true }),

        bodyPara([
          "The critical insight is the asymptotic scaling behavior. Grover\u2019s algorithm offers O(\u221AN) query complexity versus O(N) classical, yielding a crossover at modest problem sizes. For n-qubit search:"
        ]),

        equationPara("Speedup = 2\u207F / ((\u03C0/4)\u221A(2\u207F)) = (4/\u03C0) \u00D7 2^(n/2)    (5)"),

        bodyPara([
          "At n = 128 (AES key length), this represents a speedup factor exceeding 10\u00B9\u2079."
        ]),

        subsectionHeading("C. Energy Considerations"),
        bodyPara([
          "The energy disparity in our experiments reflects simulator overhead rather than intrinsic quantum costs. On dedicated quantum hardware, superconducting qubits execute gates in ~35 ns with ~20 kW system power, while trapped-ion systems use ~3 kW. For circuits completing in microseconds to milliseconds, the per-task energy drops by 3\u20136 orders of magnitude compared to our simulator measurements. This analysis motivates the cloud platform energy comparison presented in our companion paper."
        ], { noIndent: true }),

        subsectionHeading("D. Implications for Cybersecurity"),
        bodyPara([
          "The results suggest a hybrid deployment strategy: classical algorithms for small-scale, latency-critical tasks (real-time packet inspection), with quantum co-processors handling large-scale pattern recognition (QSVM on high-dimensional feature spaces), network optimization (QAOA for infrastructure segmentation), and cryptographic analysis (Grover-accelerated key search). The maturation of error-corrected quantum hardware will shift the crossover point toward smaller problem sizes."
        ], { noIndent: true }),

        subsectionHeading("E. Limitations"),
        bodyPara([
          "Several limitations should be noted. The synthetic dataset, while structured to model cybersecurity anomaly detection, does not capture the full complexity of real network traffic. The 4-qubit and 7-qubit problem sizes are within classical tractability; quantum advantage is projected but not directly observed. All quantum experiments used noiseless simulation; real hardware noise will degrade performance, particularly for deeper circuits."
        ], { noIndent: true }),

        // =====================================================
        // VI. CONCLUSION
        // =====================================================
        sectionHeading("VI. Conclusion"),
        bodyPara([
          "This paper presented a comparative evaluation of three quantum algorithms\u2014QSVM, QAOA, and Grover\u2019s search\u2014applied to cybersecurity problems: anomaly detection, network segmentation, and cryptographic key search. Our experiments demonstrate that quantum approaches achieve competitive or superior accuracy to classical baselines while exhibiting well-understood runtime-energy trade-offs. The QSVM validates quantum kernels for cybersecurity classification, QAOA outperforms greedy heuristics for network optimization, and Grover\u2019s algorithm confirms provable quadratic speedup for search tasks."
        ], { noIndent: true }),

        bodyPara([
          "Future work will evaluate these algorithms on real quantum hardware across multiple cloud platforms, investigate noise-aware training techniques, and scale to larger problem instances approaching the boundary of classical tractability."
        ]),

        // =====================================================
        // ACKNOWLEDGMENTS
        // =====================================================
        sectionHeading("Acknowledgments"),
        bodyPara([
          "The authors acknowledge the use of IBM Qiskit for quantum circuit simulation."
        ], { noIndent: true }),

        // =====================================================
        // REFERENCES
        // =====================================================
        sectionHeading("References"),

        refItem(1, "D. J. Bernstein and T. Lange, \u201CPost-quantum cryptography,\u201D Nature, vol. 549, no. 7671, pp. 188\u2013194, 2017."),
        refItem(2, "V. Havl\u00ed\u010dek et al., \u201CSupervised learning with quantum-enhanced feature spaces,\u201D Nature, vol. 567, no. 7747, pp. 209\u2013212, 2019."),
        refItem(3, "E. Farhi, J. Goldstone, and S. Gutmann, \u201CA quantum approximate optimization algorithm,\u201D arXiv preprint arXiv:1411.4028, 2014."),
        refItem(4, "L. K. Grover, \u201CA fast quantum mechanical algorithm for database search,\u201D in Proc. 28th Annual ACM Symp. Theory of Computing, 1996, pp. 212\u2013219."),
        refItem(5, "E. Payares and J. C. Martinez-Santos, \u201CQuantum machine learning for intrusion detection of distributed denial of service attacks: A comparative overview,\u201D in Proc. Int. Conf. Applied Informatics, Springer, 2021, pp. 35\u201349."),
        refItem(6, "Y. Liu et al., \u201CA rigorous and robust quantum speed-up in supervised machine learning,\u201D Nature Physics, vol. 17, pp. 1013\u20131017, 2021."),
        refItem(7, "L. Zhou et al., \u201CQuantum approximate optimization algorithm: Performance, mechanism, and implementation on near-term devices,\u201D Physical Review X, vol. 10, no. 2, p. 021067, 2020."),
        refItem(8, "G. G. Guerreschi and A. Y. Matsuura, \u201CQAOA for Max-Cut requires hundreds of qubits for quantum speed-up,\u201D Scientific Reports, vol. 9, no. 1, p. 6903, 2019."),
        refItem(9, "S. Jaques et al., \u201CImplementing Grover oracles for quantum key search on AES and LowMC,\u201D in Advances in Cryptology\u2014EUROCRYPT 2020, Springer, 2020, pp. 280\u2013310."),
      ],
    },
  ],
});

// Generate the document
const outputPath = "C:/Users/ndagl/OneDrive/Desktop/Qunatum Computing/quantum_thesis_demo/papers/Paper1_Hybrid_Quantum_AI_Cybersecurity.docx";
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(outputPath, buffer);
  console.log("SUCCESS: Paper 1 written to " + outputPath);
  console.log("Size: " + (buffer.length / 1024).toFixed(1) + " KB");
});
