"""
OCR PDF module — PDF-specific text extraction.

Strategy:
  1. Try PyMuPDF's text layer (fast, accurate for digital PDFs).
  2. If no text is found (scanned PDF), render each page to a high-DPI image,
     run preprocessing, then extract via Tesseract.
"""

import io
from typing import List

import fitz  # PyMuPDF
from PIL import Image

from app.ocr.preprocessing import preprocess_image

try:
    import pytesseract
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False


def _page_text_by_rows(page) -> str:
    """
    Return the page's text with one line per visual row.

    Lab software usually draws each table cell as a separate text object, so
    page.get_text() puts the name, value, unit and range on separate lines.
    Grouping words by vertical position rebuilds "Hemoglobin 11.2 g/dL 12-15.5"
    so the line-based parser can read it.
    """
    words = page.get_text("words")  # (x0, y0, x1, y1, text, block, line, word_no)
    if not words:
        return ""

    words.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    rows: List[list] = []
    row_mid = None
    for w in words:
        mid, height = (w[1] + w[3]) / 2, w[3] - w[1]
        # Same row if the vertical centres are within half a line height
        if rows and abs(mid - row_mid) <= max(height, 1.0) / 2:
            rows[-1].append(w)
        else:
            rows.append([w])
            row_mid = mid

    return "\n".join(" ".join(w[4] for w in sorted(row, key=lambda w: w[0])) for row in rows)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF file.
    Returns the full text as a single string.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    # ── Pass 1: native text layer ───────────────────────────────────────────
    full_text = "\n".join(_page_text_by_rows(page) for page in doc).strip()
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
