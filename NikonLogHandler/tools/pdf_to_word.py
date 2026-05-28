"""
pdf_to_word.py
==============
Converts NLH PDF documentation files to Word (.docx) format.

Preserves:
  - Text content with approximate heading detection
  - Images (embedded in the PDF)
  - Tables (best-effort via pdfplumber)
  - Page structure

Requirements:
    pip install pdfplumber python-docx Pillow

Usage (CLI):
    python pdf_to_word.py input.pdf
    python pdf_to_word.py input.pdf --output output.docx
    python pdf_to_word.py --all-docs NPE            # convert all docs in NPE/docs/
    python pdf_to_word.py --all-docs                # convert all docs in all subsidiaries

Usage (API):
    from tools.pdf_to_word import PdfToWordConverter
    conv = PdfToWordConverter()
    conv.convert(Path("NLH_Parser_List.pdf"))
"""

from __future__ import annotations

import argparse
import io
import logging
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Converter
# ---------------------------------------------------------------------------

class PdfToWordConverter:
    """
    Converts a PDF file to a .docx Word document.

    Uses pdfplumber for text/table extraction and python-docx to build the Word file.
    Images are extracted via PyMuPDF (fitz) if available, falling back to Pillow.
    """

    HEADING_FONT_THRESHOLD = 14     # pts – text larger than this is treated as a heading
    MIN_HEADING_LENGTH = 3
    MAX_HEADING_LENGTH = 120

    def __init__(self):
        self._check_deps()

    @staticmethod
    def _check_deps() -> None:
        missing = []
        for pkg in ("pdfplumber", "docx", "PIL"):
            try:
                __import__(pkg)
            except ImportError:
                label = {"docx": "python-docx", "PIL": "Pillow"}.get(pkg, pkg)
                missing.append(label)
        if missing:
            raise RuntimeError(
                f"Missing packages: {', '.join(missing)}. "
                f"Install with: pip install {' '.join(missing)}"
            )

    def convert(self, pdf_path: Path, output_path: Optional[Path] = None) -> Path:
        """
        Convert a PDF to Word.

        Parameters
        ----------
        pdf_path : Path
            Source PDF file.
        output_path : Path, optional
            Destination .docx file. Defaults to same name as PDF with .docx extension.

        Returns
        -------
        Path
            Path to the created .docx file.
        """
        import pdfplumber
        from docx import Document
        from docx.shared import Pt, Inches, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if output_path is None:
            output_path = pdf_path.with_suffix(".docx")

        doc = Document()
        self._set_document_style(doc)

        with pdfplumber.open(str(pdf_path)) as pdf:
            logging.info(f"Converting {pdf_path.name} ({len(pdf.pages)} pages)")

            for page_num, page in enumerate(pdf.pages, start=1):
                logging.debug(f"  Processing page {page_num}")

                # ── Tables first ────────────────────────────────────────────
                tables = page.extract_tables()
                table_bboxes = [tbl.bbox for tbl in page.find_tables()] if tables else []

                for tbl_data in tables:
                    self._add_table(doc, tbl_data)
                    doc.add_paragraph()

                # ── Text ─────────────────────────────────────────────────────
                words = page.extract_words(
                    extra_attrs=["size", "fontname"],
                    x_tolerance=3,
                    y_tolerance=3,
                )
                self._add_text_content(doc, words)

                # ── Images ───────────────────────────────────────────────────
                images = self._extract_images(pdf_path, page_num - 1)
                for img_bytes in images:
                    try:
                        doc.add_picture(io.BytesIO(img_bytes), width=Inches(5))
                    except Exception as exc:
                        logging.debug(f"Could not insert image: {exc}")

                # ── Page break ────────────────────────────────────────────────
                if page_num < len(pdf.pages):
                    doc.add_page_break()

        doc.save(str(output_path))
        logging.info(f"Saved: {output_path}")
        return output_path

    def _set_document_style(self, doc) -> None:
        from docx.shared import Pt
        style = doc.styles["Normal"]
        font = style.font
        font.name = "Calibri"
        font.size = Pt(11)

    def _add_text_content(self, doc, words: list[dict]) -> None:
        from docx.shared import Pt

        if not words:
            return

        # Group words into lines by vertical position
        lines: dict[float, list[dict]] = {}
        for word in words:
            y = round(word.get("top", 0), 0)
            lines.setdefault(y, []).append(word)

        for y in sorted(lines):
            line_words = sorted(lines[y], key=lambda w: w.get("x0", 0))
            text = " ".join(w["text"] for w in line_words)
            if not text.strip():
                continue

            # Detect heading by font size
            avg_size = sum(w.get("size", 11) for w in line_words) / len(line_words)
            is_heading = (
                avg_size >= self.HEADING_FONT_THRESHOLD
                and self.MIN_HEADING_LENGTH <= len(text) <= self.MAX_HEADING_LENGTH
                and not text.endswith(".")
            )

            if is_heading:
                level = 1 if avg_size >= 18 else 2
                doc.add_heading(text, level=level)
            else:
                doc.add_paragraph(text)

    def _add_table(self, doc, table_data: list[list]) -> None:
        from docx.shared import Pt
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement

        if not table_data:
            return

        rows = [r for r in table_data if any(c for c in r if c)]
        if not rows:
            return

        num_cols = max(len(r) for r in rows)
        tbl = doc.add_table(rows=len(rows), cols=num_cols)
        tbl.style = "Table Grid"

        for r_idx, row in enumerate(rows):
            for c_idx, cell_text in enumerate(row):
                if c_idx < num_cols:
                    tbl.cell(r_idx, c_idx).text = str(cell_text or "")

    @staticmethod
    def _extract_images(pdf_path: Path, page_index: int) -> list[bytes]:
        """Extract images from a PDF page. Returns list of PNG/JPEG byte strings."""
        images = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(pdf_path))
            page = doc[page_index]
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                images.append(base_image["image"])
            doc.close()
        except ImportError:
            pass  # PyMuPDF not available; skip images
        except Exception as exc:
            logging.debug(f"Image extraction failed for page {page_index}: {exc}")
        return images

    def convert_directory(self, docs_dir: Path) -> list[Path]:
        """Convert all PDF files in a directory. Returns list of created .docx paths."""
        results = []
        for pdf in sorted(docs_dir.glob("*.pdf")):
            try:
                out = self.convert(pdf)
                results.append(out)
            except Exception as exc:
                logging.error(f"Failed to convert {pdf.name}: {exc}")
        return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="NLH PDF-to-Word converter"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("pdf", nargs="?", type=Path, help="PDF file to convert")
    group.add_argument("--all-docs", nargs="?", const="ALL", metavar="SUBSIDIARY",
                       help="Convert all docs for a subsidiary (NPE/NPI/NPC) or all if omitted")

    parser.add_argument("--output", type=Path,
                        help="Output .docx path (single file mode only)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    converter = PdfToWordConverter()

    repo_root = Path(__file__).resolve().parent.parent

    if args.pdf:
        out = converter.convert(args.pdf, args.output)
        print(f"Created: {out}")

    elif args.all_docs:
        subsidiaries = ["NPE", "NPI", "NPC"] if args.all_docs == "ALL" else [args.all_docs.upper()]
        for sub in subsidiaries:
            docs_dir = repo_root / "subsidiaries" / sub / "docs"
            if not docs_dir.exists():
                print(f"  {sub}: docs/ not found – skipping")
                continue
            converted = converter.convert_directory(docs_dir)
            print(f"  {sub}: converted {len(converted)} PDFs")


if __name__ == "__main__":
    _cli()
