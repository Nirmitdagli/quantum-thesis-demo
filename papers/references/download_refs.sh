#!/bin/bash
# Downloads open-access arXiv PDFs for Paper 1 literature review.
# Paywalled sources (Nature, IEEE Xplore, Springer, SPIE) cannot be downloaded —
# the freely-available arXiv preprints are fetched instead.

set -e
cd "$(dirname "$0")"

# Map: filename  ->  arXiv ID
declare -A REFS=(
  ["02_Preskill_2018_NISQ.pdf"]="1801.00862"
  ["03_Arute_2019_QuantumSupremacy.pdf"]="1910.11333"
  ["04_Bharti_2022_NISQ_Algorithms.pdf"]="2101.08448"
  ["05_Biamonte_2017_QML_Survey.pdf"]="1611.09347"
  ["06_Havlicek_2019_ZZ_FeatureMap.pdf"]="1804.11326"
  ["07_Schuld_2019_FeatureHilbert.pdf"]="1803.07128"
  ["08_Huang_2021_PowerOfData.pdf"]="2011.01938"
  ["09_Farhi_2014_QAOA.pdf"]="1411.4028"
  ["10_Cerezo_2021_VQA_Review.pdf"]="2012.09265"
  ["11_Zhou_2020_QAOA_Performance.pdf"]="1812.01041"
  ["12_Grover_1996_Search.pdf"]="quant-ph/9605043"
  ["13_Grassl_2016_GroverAES.pdf"]="1512.04965"
  ["14_McClean_2016_HybridVQE.pdf"]="1509.04279"
  ["15_Callison_2022_HybridNISQ.pdf"]="2208.14807"
  ["19_Kilber_2021_QuantumCybersecurity.pdf"]="2110.14701"
  ["24_Strubell_2019_EnergyDL.pdf"]="1906.02243"
)

echo "Downloading arXiv references..."
for fname in "${!REFS[@]}"; do
  arxiv_id="${REFS[$fname]}"
  url="https://arxiv.org/pdf/${arxiv_id}.pdf"
  if [[ -f "$fname" ]]; then
    echo "  [skip] $fname"
    continue
  fi
  echo "  [get ] $fname  <- arXiv:$arxiv_id"
  curl -sSL -o "$fname" "$url" || echo "    FAILED: $fname"
done

echo ""
echo "Done. Paywalled refs (list in PAYWALLED.txt) must be retrieved manually."
ls -lh *.pdf 2>/dev/null | awk '{print $5, $9}'
