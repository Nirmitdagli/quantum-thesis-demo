"""Apply 3 ISAIA-specific tweaks to the user's HERO-S DOCX without
disturbing the rest of the formatting, then strip metadata and (optionally)
export PDF.

Tweaks:
  1. Soften the AIoT framing in 3 places to "interdisciplinary intelligent systems"
     (helps fit the broader ISAIA scope while keeping all IoT content).
  2. Add a human-centered closing sentence at the end of Section I Introduction
     (matches ISAIA's theme: "Human-Centered Intelligent Systems").
  3. Append "intelligent systems" to the Index Terms list.

We do this by direct text substitution inside word/document.xml. Because each
target string appears in a single <w:t> element we can use straight
str.replace() and the formatting / fonts / paragraph styles are preserved
exactly.

Then:
  - Strip docProps/core.xml and docProps/app.xml (anonymise the file).
  - Optionally call docx2pdf to produce the PDF and strip its metadata too.
"""
import os
import re
import sys
import zipfile

PAPER_DIR  = r"C:\Users\ndagl\OneDrive\Desktop\Qunatum Computing\quantum_thesis_demo\papers"
INPUT_DOCX = os.path.join(PAPER_DIR, "HERO-S_ISAIA_main.docx")
OUTPUT_PDF = os.path.join(PAPER_DIR, "HERO-S_ISAIA_main.pdf")

# -----------------------------------------------------------------------------
# 1. Read DOCX
# -----------------------------------------------------------------------------
with zipfile.ZipFile(INPUT_DOCX, 'r') as zin:
    tf = {n: zin.read(n) for n in zin.namelist()}

doc = tf['word/document.xml'].decode('utf-8')
original_len = len(doc)


# -----------------------------------------------------------------------------
# 2. Apply 3 ISAIA tweaks
# -----------------------------------------------------------------------------
def replace_once(haystack: str, needle: str, replacement: str) -> tuple[str, bool]:
    """Replace exactly one occurrence; return (new_text, succeeded)."""
    if needle in haystack:
        return haystack.replace(needle, replacement, 1), True
    return haystack, False


changes = []

# Word fragmented these paragraphs into many runs (often word-by-word).
# We therefore target the EXACT single-run text inside one <w:t> element,
# which preserves the surrounding formatting (font, size, bold, etc.).

# ---- Tweak 1a: Abstract opening softens "AIoT intrusion-detection workflows" ----
# Single run text: "—AIoT intrusion-detection workflows " (em-dash from
# the IEEE "Abstract—" lead-in)
needle = "—AIoT intrusion-detection workflows "
repl   = ("—Intelligent intrusion-detection workflows for AI-enabled "
          "Internet of Things (AIoT) systems ")
doc, ok = replace_once(doc, needle, repl)
changes.append(("Abstract: AIoT softening", ok))

# ---- Tweak 1b: Intro opening softens "AIoT security pipelines combine" ----
needle = "AIoT security pipelines combine"
repl   = ("Intelligent security pipelines spanning edge, cloud, and quantum "
          "services combine")
doc, ok = replace_once(doc, needle, repl)
changes.append(("Intro: AIoT pipelines softening", ok))

# ---- Tweak 1c: Contributions list "an AIoT edge-cloud-" ----
# Single run text: "The contributions are: (1) an AIoT edge-cloud-"
needle = "The contributions are: (1) an AIoT edge-cloud-"
repl   = "The contributions are: (1) an interdisciplinary edge-cloud-"
doc, ok = replace_once(doc, needle, repl)
changes.append(("Contributions: interdisciplinary framing", ok))

# ---- Tweak 2: Append human-centered closing sentence INSIDE the last
#               run of the contributions paragraph.
# The paragraph ends with run "<w:t>ity runs.</w:t>" (from "feasibil" + soft
# hyphen + "ity runs."). We append the new sentence inside that same run so
# the formatting stays consistent.
needle = "ity runs.</w:t>"
human_sentence = (
    " By making security-aware route decisions auditable and explainable, "
    "HERO-S supports the human security operators whose alert response "
    "times and accelerator budgets ultimately determine whether protected "
    "systems remain safe—directly aligning with human-centered "
    "intelligent-systems goals."
)
repl = "ity runs." + human_sentence + "</w:t>"
# Only the contributions paragraph contains "ity runs." — verify by counting
n_occurrences = doc.count(needle)
if n_occurrences == 1:
    doc = doc.replace(needle, repl, 1)
    changes.append(("Intro: human-centered closing sentence appended", True))
else:
    changes.append((
        f"Intro: human-centered sentence (FAIL, found {n_occurrences} occurrences of anchor)",
        False))

# ---- Tweak 3: Append "intelligent systems" to Index Terms ----
needle = "energy-aware routing."
repl   = "energy-aware routing, intelligent systems."
doc, ok = replace_once(doc, needle, repl)
changes.append(("Index Terms: intelligent systems added", ok))


# -----------------------------------------------------------------------------
# 3. Wipe metadata
# -----------------------------------------------------------------------------
EMPTY_CORE = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<cp:coreProperties '
    'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:dcterms="http://purl.org/dc/terms/" '
    'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    '<dc:title></dc:title><dc:creator></dc:creator>'
    '<cp:lastModifiedBy></cp:lastModifiedBy>'
    '</cp:coreProperties>'
)
EMPTY_APP = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Properties '
    'xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
    '<Application></Application><Company></Company>'
    '</Properties>'
)
if 'docProps/core.xml' in tf:
    tf['docProps/core.xml'] = EMPTY_CORE.encode('utf-8')
if 'docProps/app.xml' in tf:
    tf['docProps/app.xml'] = EMPTY_APP.encode('utf-8')
for k in list(tf.keys()):
    if k.startswith('docProps/custom'):
        del tf[k]

# -----------------------------------------------------------------------------
# 4. Save modified DOCX
# -----------------------------------------------------------------------------
tf['word/document.xml'] = doc.encode('utf-8')
tmp = INPUT_DOCX + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, d in tf.items():
        zo.writestr(n, d)
os.replace(tmp, INPUT_DOCX)

# -----------------------------------------------------------------------------
# 5. Report
# -----------------------------------------------------------------------------
print("=" * 60)
print("ISAIA tweaks applied to HERO-S_ISAIA_main.docx")
print("=" * 60)
for label, ok in changes:
    mark = "OK" if ok else "FAIL (anchor not found)"
    print(f"  [{mark:>4}] {label}")
print()
print(f"  DOCX size:  {os.path.getsize(INPUT_DOCX)/1024:.1f} KB")
print(f"  document.xml grew by {len(doc) - original_len} chars")
print(f"  Metadata stripped (core.xml, app.xml, custom props)")

# Verify XML
try:
    from xml.etree import ElementTree as ET
    ET.fromstring(doc)
    print("  XML well-formed: OK")
except ET.ParseError as e:
    print(f"  XML PARSE ERROR: {e}")
    sys.exit(1)

# -----------------------------------------------------------------------------
# 6. Convert to PDF (if Word is closed) and strip PDF metadata
# -----------------------------------------------------------------------------
if "--pdf" in sys.argv:
    print()
    print("Converting to PDF via Word ...")
    if os.path.exists(OUTPUT_PDF):
        os.remove(OUTPUT_PDF)
    from docx2pdf import convert
    convert(INPUT_DOCX, OUTPUT_PDF)
    print(f"  PDF written: {OUTPUT_PDF}")

    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject, TextStringObject
    reader = PdfReader(OUTPUT_PDF)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata({
        NameObject('/Title'):        TextStringObject(''),
        NameObject('/Author'):       TextStringObject(''),
        NameObject('/Subject'):      TextStringObject(''),
        NameObject('/Keywords'):     TextStringObject(''),
        NameObject('/Creator'):      TextStringObject(''),
        NameObject('/Producer'):     TextStringObject(''),
        NameObject('/CreationDate'): TextStringObject(''),
        NameObject('/ModDate'):      TextStringObject(''),
    })
    if '/Metadata' in writer._root_object:
        del writer._root_object[NameObject('/Metadata')]
    tmp_pdf = OUTPUT_PDF + '.tmp'
    with open(tmp_pdf, 'wb') as f:
        writer.write(f)
    os.replace(tmp_pdf, OUTPUT_PDF)
    r2 = PdfReader(OUTPUT_PDF)
    print(f"  PDF pages:     {len(r2.pages)}")
    print(f"  PDF size:      {os.path.getsize(OUTPUT_PDF)/1024:.1f} KB")
    print(f"  PDF metadata:  {dict(r2.metadata or {})}")
    print()
    print("DONE.")
else:
    print()
    print("Run with --pdf to also produce the PDF.")
