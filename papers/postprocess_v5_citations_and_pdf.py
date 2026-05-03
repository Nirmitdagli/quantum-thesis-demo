"""
Post-process the user-edited Paper1_IEEE_HybridQCAI_v5.docx:

  1. Re-link every  [N]  citation in body paragraphs to the matching
     "refN" bookmark on the bibliography entry.  Prose and structure
     are left exactly as the user edited them - we only add/refresh
     <w:hyperlink> wrappers around citation tokens and ensure each
     reference paragraph still carries its refN bookmark.

  2. Clear all core/app metadata inside the .docx (author, title,
     last-modified-by, company, etc.) so the exported PDF inherits
     a clean identity.

  3. Convert to PDF via Word COM (docx2pdf).

  4. Strip residual PDF metadata (Producer, Creator, Title, Author,
     CreationDate, ModDate) with pypdf.

Output files (next to the source):
  - Paper1_IEEE_HybridQCAI_v5.docx        (overwritten, links added)
  - Paper1_IEEE_HybridQCAI_v5.bak.docx    (backup of user's edited copy)
  - Paper1_IEEE_HybridQCAI_v5.pdf         (final, no metadata)
"""
import os
import re
import shutil
import zipfile

PAPER_DIR   = r"C:\Users\ndagl\OneDrive\Desktop\Qunatum Computing\quantum_thesis_demo\papers"
INPUT_DOCX  = os.path.join(PAPER_DIR, "Paper1_IEEE_HybridQCAI_v5.docx")
BACKUP_DOCX = os.path.join(PAPER_DIR, "Paper1_IEEE_HybridQCAI_v5.bak.docx")
OUTPUT_PDF  = os.path.join(PAPER_DIR, "Paper1_IEEE_HybridQCAI_v5.pdf")

# -----------------------------------------------------------------------------
# 0. Backup
# -----------------------------------------------------------------------------
if not os.path.exists(BACKUP_DOCX):
    shutil.copy2(INPUT_DOCX, BACKUP_DOCX)
    print(f"[backup] {os.path.basename(BACKUP_DOCX)}")
else:
    print(f"[backup] already exists: {os.path.basename(BACKUP_DOCX)}")

# -----------------------------------------------------------------------------
# 1. Unpack and rewrite document.xml
# -----------------------------------------------------------------------------
with zipfile.ZipFile(INPUT_DOCX, 'r') as zin:
    tf = {n: zin.read(n) for n in zin.namelist()}

doc = tf['word/document.xml'].decode('utf-8')

# Paragraph-level processing
P_RE   = re.compile(r'<w:p\b[^>]*>.*?</w:p>', re.DOTALL)
HYP_RE = re.compile(r'<w:hyperlink\b[^>]*>.*?</w:hyperlink>', re.DOTALL)

# Run with a single <w:t> text child that may contain [N] tokens
RUN_RE = re.compile(
    r'(<w:r\b[^>]*>)'                          # 1: <w:r ...>
    r'(\s*(?:<w:rPr>.*?</w:rPr>)?\s*)'         # 2: optional rPr
    r'(<w:t[^>]*>)'                            # 3: <w:t ...>
    r'([^<]*)'                                 # 4: text content
    r'(</w:t>)'                                # 5: </w:t>
    r'(\s*</w:r>)',                            # 6: </w:r>
    re.DOTALL,
)
CITE_RE = re.compile(r'(\[\d+\])')

cite_link_count = 0
bookmark_added_count = 0
bookmark_kept_count = 0


def _rewrite_run(m):
    """Turn [N] tokens inside a normal run into clickable hyperlinks,
    preserving the surrounding run's formatting."""
    global cite_link_count
    r_open, rpr, t_open, text, t_close, r_close = m.groups()
    if '[' not in text:
        return m.group(0)
    parts = CITE_RE.split(text)
    if len(parts) == 1:
        return m.group(0)

    out = []
    for p in parts:
        if not p:
            continue
        mm = re.fullmatch(r'\[(\d+)\]', p)
        if mm:
            n = mm.group(1)
            # Plain-text styled hyperlink (IEEE convention: no blue/underline).
            out.append(
                f'<w:hyperlink w:anchor="ref{n}" w:history="1">'
                f'<w:r><w:rPr><w:color w:val="auto"/><w:u w:val="none"/></w:rPr>'
                f'<w:t xml:space="preserve">[{n}]</w:t></w:r>'
                f'</w:hyperlink>'
            )
            cite_link_count += 1
        else:
            # Rebuild the original run with its rPr and just this text slice.
            out.append(
                f'{r_open}{rpr}<w:t xml:space="preserve">{p}</w:t>{r_close}'
            )
    return ''.join(out)


def _process_body_paragraph(p):
    """Mask existing hyperlinks, rewrite plain runs with [N], restore."""
    hyps_local = []

    def stash(m):
        hyps_local.append(m.group(0))
        return f'\x01H{len(hyps_local) - 1}\x01'

    masked = HYP_RE.sub(stash, p)
    masked = RUN_RE.sub(_rewrite_run, masked)

    def unstash(m):
        return hyps_local[int(m.group(1))]

    return re.sub(r'\x01H(\d+)\x01', unstash, masked)


def _ensure_ref_bookmark(p):
    """Each reference paragraph must carry a bookmark named refN where N
    is the leading [N] in its text, so body citations can link to it."""
    global bookmark_added_count, bookmark_kept_count
    m = re.search(r'<w:t[^>]*>\s*\[(\d+)\]', p)
    if not m:
        return p
    n = int(m.group(1))
    if f'w:name="ref{n}"' in p:
        bookmark_kept_count += 1
        return p
    bid = 1000 + n
    bm_start = f'<w:bookmarkStart w:id="{bid}" w:name="ref{n}"/>'
    bm_end = f'<w:bookmarkEnd w:id="{bid}"/>'
    # Insert start right after <w:pPr>...</w:pPr>, end right before </w:p>
    if '</w:pPr>' in p:
        p = p.replace('</w:pPr>', '</w:pPr>' + bm_start, 1)
    else:
        p = p.replace('<w:p>', '<w:p>' + bm_start, 1)
    p = p[::-1].replace('</w:p>'[::-1], (bm_end + '</w:p>')[::-1], 1)[::-1]
    bookmark_added_count += 1
    return p


def _process_paragraph(m):
    p = m.group(0)
    # A reference entry keeps its leading [N] as plain text (it IS the
    # target) but must expose a bookmark.
    if 'w:val="references"' in p:
        return _ensure_ref_bookmark(p)
    return _process_body_paragraph(p)


doc_final = P_RE.sub(_process_paragraph, doc)
tf['word/document.xml'] = doc_final.encode('utf-8')

# -----------------------------------------------------------------------------
# 2. Wipe document metadata (core + app + custom)
# -----------------------------------------------------------------------------
EMPTY_CORE = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<cp:coreProperties '
    'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:dcterms="http://purl.org/dc/terms/" '
    'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    '<dc:title></dc:title>'
    '<dc:creator></dc:creator>'
    '<cp:lastModifiedBy></cp:lastModifiedBy>'
    '<dc:description></dc:description>'
    '<dc:subject></dc:subject>'
    '<cp:keywords></cp:keywords>'
    '</cp:coreProperties>'
)
EMPTY_APP = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Properties '
    'xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
    'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
    '<Application></Application>'
    '<Company></Company>'
    '<Manager></Manager>'
    '</Properties>'
)

if 'docProps/core.xml' in tf:
    tf['docProps/core.xml'] = EMPTY_CORE.encode('utf-8')
if 'docProps/app.xml' in tf:
    tf['docProps/app.xml'] = EMPTY_APP.encode('utf-8')
# Drop any custom properties part entirely
for k in list(tf.keys()):
    if k.startswith('docProps/custom'):
        del tf[k]

# Repack
tmp_out = INPUT_DOCX + '.tmp'
with zipfile.ZipFile(tmp_out, 'w', zipfile.ZIP_DEFLATED) as zo:
    for n, d in tf.items():
        zo.writestr(n, d)
os.replace(tmp_out, INPUT_DOCX)
print(f"[docx]  citations linked:  {cite_link_count}")
print(f"[docx]  ref bookmarks kept: {bookmark_kept_count}")
print(f"[docx]  ref bookmarks added: {bookmark_added_count}")
print(f"[docx]  metadata cleared")

# -----------------------------------------------------------------------------
# 3. Convert to PDF via Word (docx2pdf)
# -----------------------------------------------------------------------------
print("[pdf]   converting via Word ...")
from docx2pdf import convert
convert(INPUT_DOCX, OUTPUT_PDF)
print(f"[pdf]   wrote {os.path.basename(OUTPUT_PDF)}")

# -----------------------------------------------------------------------------
# 4. Strip residual PDF metadata with pypdf
# -----------------------------------------------------------------------------
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject

reader = PdfReader(OUTPUT_PDF)
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)

# Completely empty the DocumentInfo dictionary and /Metadata stream if any
writer.add_metadata({
    NameObject('/Title'):    TextStringObject(''),
    NameObject('/Author'):   TextStringObject(''),
    NameObject('/Subject'):  TextStringObject(''),
    NameObject('/Keywords'): TextStringObject(''),
    NameObject('/Creator'):  TextStringObject(''),
    NameObject('/Producer'): TextStringObject(''),
    NameObject('/CreationDate'): TextStringObject(''),
    NameObject('/ModDate'):  TextStringObject(''),
})
# Remove XMP metadata stream from the catalog if present
if '/Metadata' in writer._root_object:
    del writer._root_object[NameObject('/Metadata')]

tmp_pdf = OUTPUT_PDF + '.tmp'
with open(tmp_pdf, 'wb') as f:
    writer.write(f)
os.replace(tmp_pdf, OUTPUT_PDF)

# Verify
reader = PdfReader(OUTPUT_PDF)
print(f"[pdf]   pages:    {len(reader.pages)}")
print(f"[pdf]   metadata: {dict(reader.metadata or {})}")
print(f"[pdf]   size:     {os.path.getsize(OUTPUT_PDF)/1024:.1f} KB")
print("DONE.")
