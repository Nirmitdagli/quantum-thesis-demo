# Response to Reviewers for HERO-S

Dear Chairs and Reviewers,

Thank you for the detailed feedback. We made a focused revision that preserves the scope of a master's-level conference paper while addressing the main technical risks: scheduler value, QPU proxy limitations, energy/SLA framing, classical baselines, and AIoT venue fit. The manuscript is now titled **HERO-S: QPU-Aware Energy-Latency Orchestration for AIoT Intrusion Detection** and presents HERO-S as a QPU-aware edge-cloud scheduler with explicit utility, queue-time, and energy constraints.

## Reviewer 1

### Comment 1. Add real datasets, multi-run statistics, and stronger validation.

**Response.** We replaced the earlier weak validation with four real IDS datasets and 30-seed experiments.

**Evidence.** Section IV and Section IV-A reports TON_IoT, NSL-KDD, CICIDS2017, and IoT-23. Section V reports 30-seed means, HERO-S F1 standard deviations in the scheduler table, Wilcoxon tests, and a new F1 boxplot figure.

### Comment 2. Improve the energy model and identify measured versus modeled energy.

**Response.** We clarified the telemetry source for each route. Edge/cloud energy uses RAPL/NVML when available and otherwise a labeled fallback model; QPU infrastructure energy is modeled only and used for sensitivity analysis.

**Evidence.** Section IV-C and the new route-cost/telemetry table report latency, energy, and source for edge CPU, cloud CPU/GPU, and QPU-capable routes. Section VI explicitly states that QPU energy is not per-job facility telemetry.

### Comment 3. Provide statistical evidence beyond a single run.

**Response.** We added paired Wilcoxon signed-rank tests and a boxplot distribution figure.

**Evidence.** The scheduler results table reports p-values for HERO-S versus the uncertainty cascade. Fig. 4 shows 30-seed F1 distributions for edge-only, cascade, and HERO-S.

## Reviewer 2

### Comment 1. The validation was weak and lacked real datasets.

**Response.** We now evaluate on TON_IoT, NSL-KDD, CICIDS2017, and IoT-23, with 30 random seeds and stratified sampling.

**Evidence.** Section IV-A gives dataset sizes and class ratios. Section IV describes sampling and leakage-field removal for IoT-23.

### Comment 2. Classical baselines were insufficient.

**Response.** We added a complete baseline table with Logistic Regression, RBF-SVM, Random Forest, Histogram Gradient Boosting, MLP, and the reduced-kernel proxy.

**Evidence.** The IDS baseline table reports accuracy, F1, recall, FPR, FNR, ROC-AUC, and PR-AUC for every model on every dataset, with proxy F1 standard deviations.

### Comment 3. The paper should not claim quantum advantage.

**Response.** We removed quantum-advantage framing. The QPU route is treated as an optional QPU-compatible path whose use must be justified by utility, confidence, queue time, and energy.

**Evidence.** Section IV-B states that the reduced-kernel route is a classical proxy and not a hardware QSVM result. Section V-D states that the Qiskit subset is feasibility-only.

### Comment 4. The scheduler contribution appeared weak.

**Response.** We added the closest classical baseline: an edge-cloud uncertainty cascade. HERO-S now outperforms this cascade under the 2.5 ms/sample average gateway budget.

**Evidence.** The scheduler results table shows HERO-S versus edge-only, uncertainty cascade, cloud-only, and static QPU. HERO-S improves over the cascade on the three nontrivial datasets and achieves marginal additional F1 on IoT-23 where all policies are near-saturated, with Wilcoxon p-values: TON_IoT 1.86e-9, NSL-KDD 3.54e-8, CICIDS2017 4.66e-8, and IoT-23 1.60e-2. We also explain the NSL-KDD case where the fixed uncertainty cascade can underperform edge-only because its escalated subset is not consistently improved by cloud inference.

## Reviewer 3

### Comment 1. Title/content mismatch and cybersecurity contribution.

**Response.** We retitled and reframed the paper as QPU-aware AIoT intrusion-detection orchestration. We added explicit security metadata: severity, asset criticality, uncertainty, confidence, deadline, queue time, and energy.

**Evidence.** The title is now QPU-aware rather than broadly hybrid quantum-classical. Section II-B and the scheduler section define the security metadata and routing role.

### Comment 2. Venue mismatch with AIoT.

**Response.** We added an AIoT edge-cloud deployment model and data-plane discussion. The QPU is explicitly remote and optional, while IoT devices and edge gateways remain lightweight.

**Evidence.** Section II-A describes devices, edge gateways, MQTT/CoAP/HTTP or broker-based telemetry export, cloud inference, and optional remote QPU service. Fig. 1 shows the edge-cloud-QPU architecture.

### Comment 3. QPU energy dominance and QPU proxy limitations.

**Response.** We now present static QPU routing as a stress-test baseline and state that the reduced-kernel proxy is a scheduler-scale proxy rather than a hardware result. HERO-S is evaluated by whether it admits or suppresses QPU-capable routing according to utility, queue time, and confidence.

**Evidence.** Section V-C reports that static QPU routing has EDP 5.85e5 at 250 ms queue time. Section V-D labels the Qiskit subset as feasibility validation only.

### Comment 4. QPU call rate is zero at 250 ms queue time.

**Response.** We explicitly explain that this is correct scheduler behavior, not disappearance of the QPU component. HERO-S has the ability to select QPU-capable execution when queue and confidence permit, but suppresses it when the current proxy is weaker than classical alternatives or queue time violates the edge budget.

**Evidence.** Section V-D and the queue-sensitivity figure report queue sensitivity: at zero queue, HERO-S invokes the QPU-capable path for 0.001 of TON_IoT samples and 0.010 of NSL-KDD samples; at 50 ms these rates drop; at 250 ms they become zero. Section VI now frames this as QPU-ready orchestration: the same utility gates admit QPU-capable routes when queue and confidence are favorable and suppress them when the route is low utility.

### Comment 5. The 2.5 ms/sample SLA lacked support.

**Response.** We changed the wording from a universal SLA to a representative average gateway compute budget for latency-sensitive edge operation. We also added edge/MEC citations and separately report sampled-deadline violation rates.

**Evidence.** Section IV-C cites edge and MEC work and states that the 2.5 ms/sample number is a stress-test budget, not a universal hard real-time standard. The scheduler results table reports sampled-deadline violation rates.

### Comment 6. Related work was too thin.

**Response.** We expanded Related Work into four focused paragraphs: IDS datasets/metrics, deep-learning and IoT IDS, edge-cloud orchestration, and quantum-aware security workflows.

**Evidence.** Section VII adds citations to AIoT and IIoT security surveys, edge intelligence, cloud-edge IoT IDS, federated IoT IDS, Kitsune, N-BaIoT, software-defined IoT IDS, and quantum-ML IDS work.

### Additional clarification. Qiskit subset accuracy values looked identical.

**Response.** We checked the Qiskit subset logs and confirmed that the repeated 0.833 accuracy is not a data-switching bug. Each run uses only eight balanced test samples, so accuracy is quantized in increments of 0.125. Both datasets happened to produce the same 6/7/7-correct pattern over the three seeds, while the F1 scores differ because the false-positive/false-negative mix differs. We added this explanation to the Qiskit subset discussion.

**Evidence.** Section V-D now explains the quantization and why noiseless/low-noise labels can remain identical on such small subsets.

## Summary of Current Artifacts

- `main.pdf`: revised IEEE manuscript, 7 pages.
- `main.tex`: revised LaTeX source.
- `AIIOT_HEROS_SUBMISSION_READY.docx`: Word manuscript copy.
- `RESPONSE_TO_REVIEWERS_AIIOT_UPDATED.docx`: this response letter.
- `figures/hero_s_f1_boxplot.png`: new 30-seed distribution figure.
- `additional_aiiot_analysis/v2_model_summary.csv`: full baseline metrics.
- `additional_aiiot_analysis/v2_scheduler_summary.csv`: route, SLA, energy, and EDP metrics.
- `additional_aiiot_analysis/v2_wilcoxon_tests.csv`: paired statistical tests.
