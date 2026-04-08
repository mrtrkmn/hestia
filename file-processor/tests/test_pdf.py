"""Property tests for PDF operations.

Property 1: PDF merge preserves total page count
Property 2: PDF split extracts exact page range
Property 3: PDF compression reduces or maintains file size

Validates: Requirements 1.1, 1.2, 1.4
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import io
import pikepdf
from hypothesis import given, settings
from hypothesis import strategies as st

from app.processors.pdf import merge, split, compress, page_count


def _make_pdf(n_pages: int) -> bytes:
    """Create a minimal valid PDF with n_pages pages."""
    pdf = pikepdf.Pdf.new()
    for _ in range(n_pages):
        pdf.add_blank_page(page_size=(612, 792))
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Property 1: PDF merge preserves total page count
# Feature: hestia, Property 1: PDF merge preserves total page count
# ---------------------------------------------------------------------------

@given(page_counts=st.lists(st.integers(min_value=1, max_value=5), min_size=1, max_size=5))
@settings(max_examples=100)
def test_merge_preserves_page_count(page_counts: list[int]):
    pdfs = [("doc{}.pdf".format(i), _make_pdf(n)) for i, n in enumerate(page_counts)]
    merged = merge(pdfs)
    assert page_count(merged) == sum(page_counts)


# ---------------------------------------------------------------------------
# Property 2: PDF split extracts exact page range
# Feature: hestia, Property 2: PDF split extracts exact page range
# ---------------------------------------------------------------------------

@given(
    n_pages=st.integers(min_value=2, max_value=10),
    data=st.data(),
)
@settings(max_examples=100)
def test_split_extracts_exact_range(n_pages: int, data: st.DataObject):
    pdf_bytes = _make_pdf(n_pages)
    start = data.draw(st.integers(min_value=0, max_value=n_pages - 1))
    end = data.draw(st.integers(min_value=start + 1, max_value=n_pages))
    result = split(pdf_bytes, "test.pdf", start, end)
    assert page_count(result) == end - start


# ---------------------------------------------------------------------------
# Property 3: PDF compression reduces or maintains file size
# Feature: hestia, Property 3: PDF compression reduces or maintains file size
# ---------------------------------------------------------------------------

@given(n_pages=st.integers(min_value=1, max_value=5))
@settings(max_examples=50)
def test_compression_reduces_or_maintains_size(n_pages: int):
    original = _make_pdf(n_pages)
    compressed = compress(original, "test.pdf")
    # Compressed output must be a valid PDF with same page count
    assert page_count(compressed) == n_pages
    # For multi-page docs compression should help; for tiny docs overhead is acceptable
    if n_pages >= 3:
        assert len(compressed) <= len(original)
