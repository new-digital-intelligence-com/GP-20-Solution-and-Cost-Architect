"""
Read a .docx into plain text, using only the standard library.

A .docx is a zip of XML — no third-party package is required. This exists
because `python-docx` is frequently unavailable (no pip access on locked-down
corporate networks), and improvising an extractor mid-demo wastes time and
loses table structure.

Paragraphs and tables are emitted in document order, so section numbering and
annex tables stay in the sequence a reader would see them.

Usage:
    python read_docx.py <file.docx>
    python read_docx.py <file.docx> --json
"""


from __future__ import annotations

# --- Windows console safety -------------------------------------------------
# Windows defaults stdout to cp1252, which cannot encode the currency symbols,
# em-dashes and comparison operators this model emits. Force UTF-8 so the
# caller never has to remember `python -X utf8`.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        if _s and getattr(_s, "encoding", "").lower().replace("-", "") != "utf8":
            _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
# ---------------------------------------------------------------------------


import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Guard against decompression bombs from externally supplied tenders.
MAX_UNCOMPRESSED = 80 * 1024 * 1024


def _para_text(p: ET.Element) -> str:
    """Concatenate the runs of a paragraph, honouring tabs and line breaks."""
    out: list[str] = []
    for node in p.iter():
        if node.tag == f"{W}t":
            out.append(node.text or "")
        elif node.tag == f"{W}tab":
            out.append("\t")
        elif node.tag in (f"{W}br", f"{W}cr"):
            out.append("\n")
    return "".join(out).strip()


def _table_rows(tbl: ET.Element) -> list[list[str]]:
    rows: list[list[str]] = []
    for tr in tbl.findall(f"{W}tr"):
        cells: list[str] = []
        for tc in tr.findall(f"{W}tc"):
            parts = [_para_text(p) for p in tc.findall(f"{W}p")]
            cells.append(" ".join(x for x in parts if x).strip())
        if any(cells):
            rows.append(cells)
    return rows


def extract(path: str | Path) -> list[dict]:
    """Return document blocks in order: {"type": "paragraph"|"table", ...}."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    with zipfile.ZipFile(path) as z:
        total = sum(i.file_size for i in z.infolist())
        if total > MAX_UNCOMPRESSED:
            raise ValueError(f"Refusing to read: uncompressed size {total} bytes")
        if "word/document.xml" not in z.namelist():
            raise ValueError("Not a Word document (word/document.xml missing)")
        xml = z.read("word/document.xml")

    body = ET.fromstring(xml).find(f"{W}body")
    if body is None:
        return []

    blocks: list[dict] = []
    for child in body:
        if child.tag == f"{W}p":
            text = _para_text(child)
            if text:
                blocks.append({"type": "paragraph", "text": text})
        elif child.tag == f"{W}tbl":
            rows = _table_rows(child)
            if rows:
                blocks.append({"type": "table", "rows": rows})
    return blocks


def to_text(blocks: list[dict]) -> str:
    out: list[str] = []
    for b in blocks:
        if b["type"] == "paragraph":
            out.append(b["text"])
        else:
            widths: list[int] = []
            for row in b["rows"]:
                for i, cell in enumerate(row):
                    if i >= len(widths):
                        widths.append(0)
                    widths[i] = max(widths[i], len(cell))
            out.append("")
            for r, row in enumerate(b["rows"]):
                line = " | ".join(c.ljust(widths[i]) for i, c in enumerate(row))
                out.append(line.rstrip())
                if r == 0:
                    out.append("-+-".join("-" * w for w in widths[:len(row)]))
            out.append("")
    return "\n".join(out)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    blocks = extract(sys.argv[1])
    if "--json" in sys.argv:
        print(json.dumps(blocks, indent=2, ensure_ascii=False))
    else:
        print(to_text(blocks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
