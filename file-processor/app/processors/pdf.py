"""PDF processing operations: merge, split, OCR, compress.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
"""

from __future__ import annotations

import io
import subprocess
import tempfile
from pathlib import Path

import pikepdf


class PDFError(Exception):
    def __init__(self, filename: str, reason: str) -> None:
        self.filename = filename
        self.reason = reason
        super().__init__(f"{filename}: {reason}")


def merge(pdf_bytes_list: list[tuple[str, bytes]]) -> bytes:
    """Merge multiple PDFs into one. Returns merged PDF bytes."""
    writer = pikepdf.Pdf.new()
    for filename, data in pdf_bytes_list:
        try:
            reader = pikepdf.Pdf.open(io.BytesIO(data))
        except Exception as e:
            raise PDFError(filename, f"Cannot read PDF: {e}")
        writer.pages.extend(reader.pages)
    buf = io.BytesIO()
    writer.save(buf)
    return buf.getvalue()


def split(pdf_bytes: bytes, filename: str, start: int, end: int) -> bytes:
    """Extract pages [start, end) (0-indexed) from a PDF."""
    try:
        reader = pikepdf.Pdf.open(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise PDFError(filename, f"Cannot read PDF: {e}")
    n = len(reader.pages)
    if start < 0 or end > n or start >= end:
        raise PDFError(filename, f"Invalid page range {start}-{end} for {n}-page document")
    writer = pikepdf.Pdf.new()
    for i in range(start, end):
        writer.pages.append(reader.pages[i])
    buf = io.BytesIO()
    writer.save(buf)
    return buf.getvalue()


def ocr(pdf_bytes: bytes, filename: str) -> bytes:
    """Run OCR on a scanned PDF, returning a searchable PDF."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as inp:
        inp.write(pdf_bytes)
        inp_path = inp.name
    out_path = inp_path.replace(".pdf", "_ocr.pdf")
    try:
        subprocess.run(
            ["ocrmypdf", "--skip-text", inp_path, out_path],
            check=True, capture_output=True, timeout=120,
        )
        return Path(out_path).read_bytes()
    except FileNotFoundError:
        raise PDFError(filename, "ocrmypdf not installed")
    except subprocess.CalledProcessError as e:
        raise PDFError(filename, f"OCR failed: {e.stderr.decode()[:200]}")
    finally:
        Path(inp_path).unlink(missing_ok=True)
        Path(out_path).unlink(missing_ok=True)


def compress(pdf_bytes: bytes, filename: str) -> bytes:
    """Compress a PDF to reduce file size."""
    try:
        reader = pikepdf.Pdf.open(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise PDFError(filename, f"Cannot read PDF: {e}")
    buf = io.BytesIO()
    reader.save(buf, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    return buf.getvalue()


def page_count(pdf_bytes: bytes) -> int:
    """Return the number of pages in a PDF."""
    return len(pikepdf.Pdf.open(io.BytesIO(pdf_bytes)).pages)
