"""
OCR PDF module — PDF-specific text extraction.

Strategy:
  1. Try PyMuPDF's text layer (fast, accurate for digital PDFs).
  2. If no text is found (scanned PDF), render each page to a high-DPI image,
     run preprocessing, then extract via Tesseract.
"""

import io

import fitz  # PyMuPDF
from PIL import Image

from app.ocr.preprocessing import preprocess_image

try:
    import pytesseract
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF file.
    Returns the full text as a single string.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    # ── Pass 1: native text layer ───────────────────────────────────────────
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    full_text = full_text.strip()
    if full_text:
        return full_text

    # ── Pass 2: scanned PDF — render to image and OCR each page ────────────
    if not _TESSERACT_AVAILABLE:
        raise RuntimeError(
            "This PDF appears to be a scanned document but pytesseract is not installed."
        )

    ocr_text = ""
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        processed = preprocess_image(img)
        ocr_text += pytesseract.image_to_string(processed) + "\n"

    return ocr_text
