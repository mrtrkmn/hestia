"""Property tests for image conversion.

Property 5: PDF-to-image conversion produces one image per page
Property 6: Images-to-PDF conversion preserves image count as page count
Property 7: Image format conversion preserves dimensions

Validates: Requirements 2.1, 2.2, 2.3
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import io
import pikepdf
from PIL import Image
from hypothesis import given, settings
from hypothesis import strategies as st

from app.processors.image import pdf_to_images, images_to_pdf, convert_image
from app.processors.pdf import page_count


def _make_pdf(n_pages: int) -> bytes:
    pdf = pikepdf.Pdf.new()
    for _ in range(n_pages):
        pdf.add_blank_page(page_size=(612, 792))
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


def _make_image(width: int, height: int, fmt: str = "PNG") -> bytes:
    img = Image.new("RGB", (width, height), "red")
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Property 5: PDF-to-image produces one image per page
# Feature: hestia, Property 5: PDF-to-image conversion produces one image per page
# ---------------------------------------------------------------------------

@given(
    n_pages=st.integers(min_value=1, max_value=5),
    fmt=st.sampled_from(["PNG", "JPEG"]),
)
@settings(max_examples=50)
def test_pdf_to_images_count(n_pages: int, fmt: str):
    pdf_bytes = _make_pdf(n_pages)
    images = pdf_to_images(pdf_bytes, "test.pdf", fmt)
    assert len(images) == n_pages


# ---------------------------------------------------------------------------
# Property 6: Images-to-PDF preserves image count as page count
# Feature: hestia, Property 6: Images-to-PDF conversion preserves image count as page count
# ---------------------------------------------------------------------------

@given(n_images=st.integers(min_value=1, max_value=5))
@settings(max_examples=50, deadline=None)
def test_images_to_pdf_page_count(n_images: int):
    imgs = [("img{}.png".format(i), _make_image(100, 100)) for i in range(n_images)]
    pdf_bytes = images_to_pdf(imgs)
    assert page_count(pdf_bytes) == n_images


# ---------------------------------------------------------------------------
# Property 7: Image format conversion preserves dimensions
# Feature: hestia, Property 7: Image format conversion preserves dimensions
# ---------------------------------------------------------------------------

@given(
    width=st.integers(min_value=10, max_value=200),
    height=st.integers(min_value=10, max_value=200),
)
@settings(max_examples=50)
def test_png_to_jpeg_preserves_dimensions(width: int, height: int):
    png_data = _make_image(width, height, "PNG")
    jpeg_data = convert_image(png_data, "test.png", "PNG", "JPEG")
    img = Image.open(io.BytesIO(jpeg_data))
    assert img.size == (width, height)


@given(
    width=st.integers(min_value=10, max_value=200),
    height=st.integers(min_value=10, max_value=200),
)
@settings(max_examples=50)
def test_jpeg_to_png_preserves_dimensions(width: int, height: int):
    jpeg_data = _make_image(width, height, "JPEG")
    png_data = convert_image(jpeg_data, "test.jpg", "JPEG", "PNG")
    img = Image.open(io.BytesIO(png_data))
    assert img.size == (width, height)
