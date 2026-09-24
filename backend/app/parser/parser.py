"""
Parser — extracts structured lab results from raw OCR text.

Supports multiple real-world lab report layouts:
  1. Inline pattern: "Hemoglobin 14.2 g/dL 13.0-17.0"
  2. Tabular (colon-separated): "Hemoglobin: 14.2 g/dL (13.0-17.0)"
  3. Result-only (value without reference): "Hemoglobin 14.2 g/dL"
"""

import re
from typing import Dict, List, Optional

# ── Pattern 1: Name  Value  Unit  Min-Max (space-separated, no colon) ───────
PATTERN_INLINE = re.compile(
    r"([A-Za-z][A-Za-z\s/()]{1,40}?)\s+"   # test name (2-40 chars)
    r"(\d+\.?\d*)\s+"                        # numeric value
    r"([A-Za-z%/µu]{1,10})\s+"              # unit
    r"(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)",   # reference range
    re.IGNORECASE,
)

# ── Pattern 2: Name: Value Unit (Ref) ────────────────────────────────────────
PATTERN_COLON = re.compile(
    r"([A-Za-z][A-Za-z\s/()]{1,40}?)\s*:\s*"  # name + colon
    r"(\d+\.?\d*)\s*"                           # value
    r"([A-Za-z%/µu]{1,10})?\s*"                # optional unit
    r"[\(\[]?\s*(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)\s*[\)\]]?",  # ref range
    re.IGNORECASE,
)

# ── Pattern 3: Name  Value  Unit (no reference range) ────────────────────────
PATTERN_NO_REF = re.compile(
    r"([A-Za-z][A-Za-z\s/()]{1,40}?)\s+"  # name
    r"(\d+\.?\d*)\s+"                      # value
    r"([A-Za-z%/µu]{1,10})",               # unit
    re.IGNORECASE,
)

# Noise words that often appear in OCR output and are not test names
_NOISE_WORDS = {
    "date", "name", "age", "sex", "gender", "result", "report", "test",
    "lab", "patient", "doctor", "ref", "reference", "normal", "unit",
    "value", "range", "remarks", "page", "sample", "collected",
}


def _is_noise(name: str) -> bool:
    """Return True if the extracted name looks like a header or noise word."""
    clean = name.strip().lower()
    return len(clean) < 3 or clean in _NOISE_WORDS or clean.startswith("_")


def parse_lab_text(raw_text: str) -> List[Dict]:
    """
    Parse raw OCR text and return a list of structured lab result dicts.
    Each dict has: test_name_raw, value, unit, reference_min (opt),
                   reference_max (opt), reference_text (opt), extraction_confidence.
    """
    results: List[Dict] = []
    seen_names: set = set()

    for line in raw_text.splitlines():
        line = line.strip()
        if not line or len(line) < 5:
            continue

        result: Optional[Dict] = None

        # Try Pattern 1 (inline with reference)
        m = PATTERN_INLINE.search(line)
        if m:
            name = m.group(1).strip()
            if not _is_noise(name):
                result = {
                    "test_name_raw":        name,
                    "value":                float(m.group(2)),
                    "unit":                 m.group(3).strip(),
                    "reference_min":        float(m.group(4)),
                    "reference_max":        float(m.group(5)),
                    "reference_text":       f"{m.group(4)} - {m.group(5)}",
                    "extraction_confidence": 0.90,
                }

        # Try Pattern 2 (colon format with reference)
        if result is None:
            m = PATTERN_COLON.search(line)
            if m:
                name = m.group(1).strip()
                if not _is_noise(name):
                    result = {
                        "test_name_raw":        name,
                        "value":                float(m.group(2)),
                        "unit":                 (m.group(3) or "").strip(),
                        "reference_min":        float(m.group(4)),
                        "reference_max":        float(m.group(5)),
                        "reference_text":       f"{m.group(4)} - {m.group(5)}",
                        "extraction_confidence": 0.88,
                    }

        # Try Pattern 3 (no reference range — lower confidence)
        if result is None:
            m = PATTERN_NO_REF.search(line)
            if m:
                name = m.group(1).strip()
                if not _is_noise(name):
                    result = {
                        "test_name_raw":        name,
                        "value":                float(m.group(2)),
                        "unit":                 m.group(3).strip(),
                        "reference_min":        None,
                        "reference_max":        None,
                        "reference_text":       None,
                        "extraction_confidence": 0.60,
                    }

        if result and result["test_name_raw"].lower() not in seen_names:
            seen_names.add(result["test_name_raw"].lower())
            results.append(result)

    return results
