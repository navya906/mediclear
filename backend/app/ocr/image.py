"""
OCR Image module — image-specific text extraction using Tesseract.
Delegates preprocessing to app.ocr.preprocessing before calling pytesseract.
"""

import io

import pytesseract
from PIL import Image

from app.ocr.preprocessing import preprocess_image


def extract_text_from_image(file_bytes: bytes) -> str:
    """
    Extract text from a raw image file (jpg, jpeg, png).
    Runs the preprocessing pipeline first to maximise OCR accuracy.
    """
    img = Image.open(io.BytesIO(file_bytes))
    processed = preprocess_image(img)
    return pytesseract.image_to_string(processed)
