# HERO-S Reference Audit and Optimization

Date: 2026-04-26

## What Was Checked

- Compared the original paper reference list in `Paper1_IEEE_HybridQCAI_v5.pdf` against the current HERO-S manuscript.
- Removed or avoided quantum-algorithm references that no longer support the revised AIoT scheduling scope.
- Added missing AIoT/IIoT security, cloud-edge IDS, edge intelligence, federated IoT IDS, quantum-ML IDS, and energy-aware scheduling references needed by the revised Related Work.
- Verified all current bibliography entries through DOI metadata APIs or official project URLs.

## Original Reference Themes

The original paper used about 25 references, mostly in these groups:

- Quantum computing foundations and NISQ: Nielsen and Chuang; Preskill; Arute et al.; Bharti et al.
- Quantum ML and variational/hybrid algorithms: Biamonte et al.; Havlicek et al.; Schuld and Killoran; Huang et al.; Farhi et al.; Cerezo et al.; Zhou et al.; McClean et al.; Callison and Chancellor.
- Grover/AES and quantum cybersecurity: Grover; Grassl et al.; Suryotrisongko and Musashi; Payares and Martinez-Santos; Kilber et al.
- IDS datasets/classifiers: Tavallaee et al.; Sharafaldin et al.; Cortes and Vapnik.
- Energy/Qiskit: Auffeves; Strubell et al.; Qiskit contributors.

## Retained From Original Paper

These references still directly support the revised HERO-S paper and were retained or cleaned:

- `preskill2018nisq` -- NISQ context; DOI added.
- `havlicek2019supervised` -- quantum feature maps/kernels.
- `schuld2019qml` -- quantum feature Hilbert spaces.
- `cerezo2021vqa` -- variational quantum algorithms.
- `tavallaee2009kdd` -- NSL-KDD/KDD benchmark context; pages cleaned.
- `sharafaldin2018toward` -- CICIDS2017 dataset generation.
- `strubell2019energy` -- ML energy-accounting motivation; DOI/pages added.
- `qiskit` -- Qiskit implementation citation; DOI/URL verified.

## Dropped As No Longer Central

The revised article no longer studies QAOA, Grover search, AES resource estimates, or broad quantum supremacy, so these original references were intentionally not carried into the final bibliography: Nielsen and Chuang; Arute et al.; Bharti et al.; Biamonte et al.; Huang et al.; Farhi et al.; Zhou et al.; Grover; Grassl et al.; McClean et al.; Callison and Chancellor; Humble et al.; Suryotrisongko and Musashi; Payares and Martinez-Santos; Kilber et al.; Cortes and Vapnik; Auffeves.

## Added or Strengthened References

- Real IDS datasets: `alsaedi2020toniot`, `garcia2020iot23`, `sharafaldin2018detailed`.
- Edge/MEC orchestration: `shi2016edge`, `mach2017mec`, `satyanarayanan2017edge`, `mao2017mec`.
- Strong IoT IDS baselines/surveys: `ferrag2020deep`, `mirsky2018kitsune`, `meidan2018nbaiot`, `li2019sdiotids`.
- Federated/distributed and cloud-edge IoT security context: `nguyen2019diot`, `mothukuri2021survey`, `yang2023cloudedgeids`.
- AIoT/IIoT security and edge-intelligence context: `siam2025aiot`, `alotaibi2023iiotsecurity`, `zhou2019edgeintelligence`.
- Energy-aware scheduling context: `chen2023energy`.
- Quantum-ML IDS context: `kalinin2023qmlids`.
- Simulator implementation: `aer`.

## Verification Result

Current `AIIOT_HEROS_SUBMISSION_PACKAGE/references.bib` contains 28 entries. All 28 are cited by `main.tex`; there are no uncited or missing bibliography keys.

- 27 entries have DOIs verified through Crossref or DataCite metadata APIs.
- 1 entry, `aer`, uses the official Qiskit Aer GitHub repository URL and returned HTTP 200.
- LaTeX/BibTeX rebuild completed with no warnings, no undefined citations, and no bibliography errors.

