"""
OCR Preprocessing — image enhancement pipeline before Tesseract.

Applies contrast enhancement, denoising, and grayscale conversion to improve
OCR accuracy on low-quality scans and photos.
"""

import io

from PIL import Image, ImageEnhance, ImageFilter


def preprocess_image(img: Image.Image) -> Image.Image:
    """
    Run the full preprocessing pipeline on a PIL Image before OCR:
      1. Convert to RGB (handle RGBA / palette images)
      2. Upscale small images to at least 300 DPI equivalent
      3. Convert to grayscale
      4. Enhance contrast
      5. Sharpen edges
      6. Apply a light denoise pass
    Returns a processed PIL Image ready for pytesseract.
    """
    # 1. Normalise colour mode
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # 2. Upscale if the image is very small (< 1000px on either axis)
    w, h = img.size
    if w < 1000 or h < 1000:
        scale = max(1000 / w, 1000 / h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # 3. Grayscale
    img = img.convert("L")

    # 4. Contrast enhancement
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    # 5. Sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.0)

    # 6. Light Gaussian denoise
    img = img.filter(ImageFilter.MedianFilter(size=3))

    return img


def preprocess_bytes(image_bytes: bytes) -> bytes:
    """
    Convenience wrapper: accept raw image bytes, run preprocessing, return PNG bytes.
    """
    img = Image.open(io.BytesIO(image_bytes))
    processed = preprocess_image(img)
    buf = io.BytesIO()
    processed.save(buf, format="PNG")
    return buf.getvalue()
