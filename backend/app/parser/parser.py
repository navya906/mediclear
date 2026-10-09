"""
Parser — extracts structured lab results from raw OCR text.

Each line is matched against a single layout:

    <name> [:] [< or >]<value> [flag] [unit] [(]<reference>[)]

which covers the common real-world variants, for example:
  "Hemoglobin 14.2 g/dL 13.0-17.0"
  "TSH: 2.5 mIU/L (0.4-4.0)"
  "Platelet Count 1,50,000 /cumm 1,50,000 - 4,50,000"   (Indian digit grouping)
  "WBC 7.2 10^3/uL 4.0-11.0"                             (digits in the unit)
  "Hemoglobin 10.1 L g/dL 13.0 to 17.0"                  (H/L flag, "to" range)
  "LDL Cholesterol 130 mg/dL < 100"                      (one-sided reference)
  "Glucose <70 mg/dL"                                    (comparator on the value)

A line needs a unit or a reference range to count as a result, which keeps
things like "Age 45" or "Page 1 of 2" out.
"""

import re
from typing import Dict, List, Optional, Tuple

# Plain numbers, decimals, and comma-grouped numbers (1,50,000 or 150,000)
_NUM = r"(?:\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)"

# Units: "10^3/uL", "x10³/µL", or a token starting with a letter, µ, % or /
_UNIT = (
    r"(?:[x×]\s?)?10\s?(?:\^|\*\*)?\s?[0-9³⁶⁹]+\s*/\s*[A-Za-zµμ]+"
    r"|[A-Za-zµμ%/][\w%/µμ.²³^\-]*"
)

_LESS = r"(?:<=?|≤|(?i:up\s*to|less\s+than))"
_MORE = r"(?:>=?|≥|(?i:more\s+than|greater\s+than))"

_REFERENCE = (
    rf"(?P<ref_lo>{_NUM})\s*(?:-|–|to)\s*(?P<ref_hi>{_NUM})"
    rf"|(?P<ref_lt>{_LESS})\s*(?P<ref_lt_num>{_NUM})"
    rf"|(?P<ref_gt>{_MORE})\s*(?P<ref_gt_num>{_NUM})"
)

LINE_PATTERN = re.compile(
    # Test name: starts with a letter, may contain digits ("Vitamin B12",
    # "Free T3"), parentheses, commas ("Cholesterol, Total") etc.
    r"(?P<name>[A-Za-z][\w ()/,.'+\-]*?[A-Za-z0-9)\]])"
    r"\s*(?::\s*|\s+)"
    # Value, optionally prefixed by a comparator ("<70")
    rf"(?P<cmp>[<>]=?|≤|≥)?\s*(?P<value>{_NUM})(?![\w^/])"
    # Optional abnormal flag printed next to the value
    r"(?:\s+(?:\((?:H|L|High|Low)\)|H|L|High|Low|\*)(?=\s|$))?"
    rf"(?:\s+(?P<unit>{_UNIT}))?"
    rf"(?:\s*[\(\[]?\s*(?:{_REFERENCE})\s*[\)\]]?)?",
)

# Lines with dates or clock times are header/footer metadata, not results
# (same separator twice, so a range like "13.0-17.0" isn't mistaken for a date)
_DATE_OR_TIME = re.compile(r"\b\d{1,2}([/.\-])\d{1,2}\1\d{2,4}\b|\b\d{1,2}:\d{2}\b")

# Words that mark a line as patient/report metadata rather than a test name
_NOISE_WORDS = {
    "date", "name", "age", "sex", "gender", "result", "report", "reported",
    "patient", "doctor", "dr", "ref", "referred", "reference", "unit", "units",
    "value", "range", "remarks", "page", "sample", "collected", "received",
    "registered", "phone", "mobile", "id", "uhid", "barcode", "years", "yrs",
}


def _to_float(num: str) -> float:
    return float(num.replace(",", ""))


def _is_noise(name: str) -> bool:
    """Return True if the extracted name looks like a header or metadata."""
    clean = name.strip().lower()
    if len(clean) < 2 or clean.startswith("_"):
        return True
    tokens = set(re.split(r"[^a-z0-9]+", clean))
    return bool(tokens & _NOISE_WORDS)


def _reference(m: re.Match) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """Return (min, max, text) for the matched reference range, if any."""
    if m.group("ref_lo"):
        lo, hi = _to_float(m.group("ref_lo")), _to_float(m.group("ref_hi"))
        return lo, hi, f"{lo:g} - {hi:g}"
    if m.group("ref_lt"):
        hi = _to_float(m.group("ref_lt_num"))
        return None, hi, f"< {hi:g}"
    if m.group("ref_gt"):
        lo = _to_float(m.group("ref_gt_num"))
        return lo, None, f"> {lo:g}"
    return None, None, None


def _parse_line(line: str) -> Optional[Dict]:
    if _DATE_OR_TIME.search(line):
        return None

    m = LINE_PATTERN.search(line)
    if not m:
        return None

    name = re.sub(r"\s+", " ", m.group("name")).strip(" ,.-")
    if _is_noise(name):
        return None

    unit = m.group("unit")
    ref_min, ref_max, ref_text = _reference(m)
    if not unit and ref_text is None:
        return None

    if ref_min is not None and ref_max is not None:
        confidence = 0.90
    elif ref_text is not None:
        confidence = 0.85
    else:
        confidence = 0.60
    if m.group("cmp"):
        # "<70" is a bound, not an exact value
        confidence -= 0.10

    return {
        "test_name_raw":         name,
        "value":                 _to_float(m.group("value")),
        "unit":                  unit or "",
        "reference_min":         ref_min,
        "reference_max":         ref_max,
        "reference_text":        ref_text,
        "extraction_confidence": round(confidence, 2),
    }


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
        if len(line) < 4:
            continue

        result = _parse_line(line)
        if result and result["test_name_raw"].lower() not in seen_names:
            seen_names.add(result["test_name_raw"].lower())
            results.append(result)

    return results
