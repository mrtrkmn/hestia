"""Property 4: Invalid file input produces structured error.

Feature: hestia, Property 4: Invalid file input produces structured error

For any invalid file input (corrupt PDF, format mismatch, undecoded media),
the File_Processor should return an error containing filename and failure reason.

Validates: Requirements 1.5, 2.4, 3.5
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import io
import pytest
from PIL import Image

from app.processors.pdf import merge, split, compress, PDFError
from app.processors.image import convert_image, ImageError


def test_corrupt_pdf_merge_error():
    with pytest.raises(PDFError) as exc_info:
        merge([("bad.pdf", b"not a pdf")])
    assert "bad.pdf" in str(exc_info.value)
    assert exc_info.value.filename == "bad.pdf"
    assert exc_info.value.reason


def test_corrupt_pdf_split_error():
    with pytest.raises(PDFError) as exc_info:
        split(b"corrupt data", "broken.pdf", 0, 1)
    assert exc_info.value.filename == "broken.pdf"


def test_corrupt_pdf_compress_error():
    with pytest.raises(PDFError) as exc_info:
        compress(b"not valid", "bad.pdf")
    assert exc_info.value.filename == "bad.pdf"


def test_format_mismatch_error():
    """Declare PNG but provide JPEG data."""
    img = Image.new("RGB", (10, 10), "blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_data = buf.getvalue()

    with pytest.raises(ImageError) as exc_info:
        convert_image(jpeg_data, "fake.png", "PNG", "JPEG")
    assert exc_info.value.filename == "fake.png"
    assert "mismatch" in exc_info.value.reason.lower()
