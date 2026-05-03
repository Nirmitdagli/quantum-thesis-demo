"""
Update the paper title in Paper1_IEEE_HybridQCAI_v5.docx to the exact
string the user requested, then re-export the PDF with no metadata.

Target title:
  HERO: A Heterogeneous Energy-Aware Runtime Orchestrator for
  Quantum-Classical Cybersecurity Workloads
"""
import os
import re
import zipfile

PAPER_DIR  = r"C:\Users\ndagl\OneDrive\Desktop\Qunatum Computing\quantum_thesis_demo\papers"
INPUT_DOCX = os.path.join(PAPER_DIR, "Paper1_IEEE_HybridQCAI_v5.docx")
OUTPUT_PDF = os.path.join(PAPER_DIR, "Paper1_IEEE_HybridQCAI_v5.pdf")

NEW_TITLE = ("HERO: A Heterogeneous Energy-Aware Runtime Orchestrator for "
             "Quantum-Classical Cybersecurity Workloads")

# -----------------------------------------------------------------------------
# 1. Rewrite title inside document.xml
# -----------------------------------------------------------------------------
with zipfile.ZipFile(INPUT_DOCX, 'r') as zin:
    tf = {n: zin.read(n) for n in zin.namelist()}

doc = tf['word/document.xml'].decode('utf-8')

TITLE_PARA_RE = re.compile(
    r'(<w:p\b[^>]*>(?:(?!</w:p>).)*?w:val="papertitle"(?:(?!</w:p>).)*?</w:p>)',
    re.DOTALL,
)

def _replace_title(m):
    p = m.group(0)
    # Replace every <w:t ...>...</w:t> inside this paragraph's runs with
    # the new title (placed in a single run). Preserve the pPr + first
    # run's rPr; wipe trailing runs.
    # Extract pPr
    ppr_m = re.search(r'(<w:pPr>.*?</w:pPr>)', p, re.DOTALL)
    ppr = ppr_m.group(1) if ppr_m else ''
    # Extract first run's rPr (if any)
    first_run = re.search(r'<w:r\b[^>]*>(.*?)</w:r>', p, re.DOTALL)
    rpr = ''
    if first_run:
        rpr_m = re.search(r'(<w:rPr>.*?</w:rPr>)', first_run.group(1), re.DOTALL)
        rpr = rpr_m.group(1) if rpr_m else ''
    # Extract the <w:p ...> opening tag attributes
    open_m = re.match(r'(<w:p\b[^>]*>)', p)
    p_open = open_m.group(1) if open_m else '<w:p>'
    safe_title = (NEW_TITLE
                  .replace('&', '&amp;')
                  .replace('<', '&lt;')
                  .replace('>', '&gt;'))
    new_para = (
        f'{p_open}{ppr}'
        f'<w:r>{rpr}<w:t xml:space="preserve">{safe_title}</w:t></w:r>'
        f'</w:p>'
    )
    return new_para

doc_new, n_sub = TITLE_PARA_RE.subn(_replace_title, doc, count=1)
assert n_sub == 1, f"expected 1 title replacement, got {n_sub}"
tf['word/document.xml'] = doc_new.encode('utf-8')

# Wipe metadata again (Word re-adds some on save)
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
    '<dc:description></dc:description><dc:subject></dc:subject>'
    '<cp:keywords></cp:keywords></cp:coreProperties>'
)
EMPTY_APP = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Properties '
    'xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
    '<Application></Application><Company></Company><Manager></Manager>'
    '</Properties>'
)
if 'docProps/core.xml' in tf:
    tf['docProps/core.xml'] = EMPTY_CORE.encode('utf-8')
if 'docProps/app.xml' in tf:
    tf['docProps/app.xml'] = EMPTY_APP.encode('utf-8')

tmp = INPUT_DOCX + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, d in tf.items():
        zo.writestr(n, d)
os.replace(tmp, INPUT_DOCX)
print(f"[docx] title set to: {NEW_TITLE}")

# -----------------------------------------------------------------------------
# 2. Export PDF via Word
# -----------------------------------------------------------------------------
if os.path.exists(OUTPUT_PDF):
    os.remove(OUTPUT_PDF)

print("[pdf]  converting via Word ...")
from docx2pdf import convert
convert(INPUT_DOCX, OUTPUT_PDF)
print(f"[pdf]  wrote {os.path.basename(OUTPUT_PDF)}")

# -----------------------------------------------------------------------------
# 3. Strip PDF metadata
# -----------------------------------------------------------------------------
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

r = PdfReader(OUTPUT_PDF)
print(f"[pdf]  pages:    {len(r.pages)}")
print(f"[pdf]  size:     {os.path.getsize(OUTPUT_PDF)/1024:.1f} KB")
print(f"[pdf]  metadata: {dict(r.metadata or {})}")
print("DONE.")
