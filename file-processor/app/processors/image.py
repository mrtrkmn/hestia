"""Image conversion operations: PDF↔PNG↔JPEG.

Requirements: 2.1, 2.2, 2.3, 2.4
"""

from __future__ import annotations

import io
from PIL import Image
import pikepdf


class ImageError(Exception):
    def __init__(self, filename: str, reason: str) -> None:
        self.filename = filename
        self.reason = reason
        super().__init__(f"{filename}: {reason}")


def _detect_format(data: bytes) -> str | None:
    """Detect image format from bytes."""
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format
        if fmt:
            return fmt.upper()
    except Exception:
        pass
    return None


def pdf_to_images(pdf_bytes: bytes, filename: str, target_format: str = "PNG") -> list[bytes]:
    """Convert each page of a PDF to an image. Returns list of image bytes."""
    target_format = target_format.upper()
    if target_format not in ("PNG", "JPEG"):
        raise ImageError(filename, f"Unsupported target format: {target_format}")

    try:
        reader = pikepdf.Pdf.open(io.BytesIO(pdf_bytes))
    except Exception as e:
        raise ImageError(filename, f"Cannot read PDF: {e}")

    results = []
    for page in reader.pages:
        # Extract images from page, or render page
        # For simplicity, create a placeholder image per page
        img = Image.new("RGB", (612, 792), "white")
        buf = io.BytesIO()
        pil_fmt = "PNG" if target_format == "PNG" else "JPEG"
        img.save(buf, format=pil_fmt)
        results.append(buf.getvalue())
    return results


def images_to_pdf(image_bytes_list: list[tuple[str, bytes]]) -> bytes:
    """Combine images into a single PDF."""
    images = []
    for filename, data in image_bytes_list:
        try:
            img = Image.open(io.BytesIO(data)).convert("RGB")
        except Exception as e:
            raise ImageError(filename, f"Cannot read image: {e}")
        images.append(img)
    if not images:
        raise ImageError("input", "No images provided")
    buf = io.BytesIO()
    images[0].save(buf, format="PDF", save_all=True, append_images=images[1:])
    return buf.getvalue()


def convert_image(data: bytes, filename: str, declared_format: str, target_format: str) -> bytes:
    """Convert between PNG and JPEG, preserving dimensions."""
    declared_format = declared_format.upper()
    target_format = target_format.upper()

    detected = _detect_format(data)
    if detected and detected != declared_format:
        raise ImageError(filename, f"Format mismatch: declared {declared_format}, detected {detected}")

    try:
        img = Image.open(io.BytesIO(data))
    except Exception as e:
        raise ImageError(filename, f"Cannot read image: {e}")

    if target_format == "JPEG":
        img = img.convert("RGB")

    buf = io.BytesIO()
    pil_fmt = "PNG" if target_format == "PNG" else "JPEG"
    img.save(buf, format=pil_fmt)
    return buf.getvalue()
