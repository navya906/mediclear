"""
OCR Core — public entry point for text extraction.

Delegates to app.ocr.pdf and app.ocr.image depending on file type.
"""

from app.ocr.pdf import extract_text_from_pdf
from app.ocr.image import extract_text_from_image


def extract_text_from_file(file_bytes: bytes, file_type: str) -> str:
    """
    Extract text from a file (pdf, jpg, jpeg, png).
    Raises ValueError for unsupported file types.
    """
    ft = file_type.lower()
    if ft == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ft in ("jpg", "jpeg", "png"):
        return extract_text_from_image(file_bytes)
    else:
        raise ValueError(f"Unsupported file type for OCR: {file_type}")
