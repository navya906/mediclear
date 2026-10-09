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
    # Test name: starts with a letter (or a numeric prefix like "25-OH"),
    # may contain digits ("Vitamin B12", "Free T3"), parentheses, commas
    # ("Cholesterol, Total") etc.
    r"(?P<name>(?:\d+(?:,\d+)?-)?[A-Za-z][\w ()/,.'+\-]*?[A-Za-z0-9)\]])"
    r"\s*(?::\s*|\s+)"
    # Value, optionally prefixed by a comparator ("<70")
    rf"(?P<cmp>[<>]=?|≤|≥)?\s*(?P<value>{_NUM})(?![\w^/])"
    # Optional abnormal flag printed next to the value
    r"(?:\s+(?:\((?:H|L|High|Low)\)|H|L|High|Low|\*)(?=\s|$))?"
    rf"(?:\s+(?P<unit>{_UNIT}))?"
    rf"(?:\s*[\(\[]?\s*(?:{_REFERENCE})\s*[\)\]]?)?"
    # Some reports print the unit after the range ("12.0 - 15.5 g/dL");
    # a trailing H/L flag is not a unit
    rf"(?:\s*(?!(?:H|L|High|Low)(?:\s|$))(?P<unit_after>{_UNIT}))?",
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
    # interpretation legends: "Deficiency < 20 ng/mL, Insufficiency 20 - 30 ..."
    "deficiency", "insufficiency", "sufficiency", "toxicity", "desirable",
    "borderline", "optimal", "interpretation", "note", "comment", "comments",
}

# Explanatory paragraphs contain numbers too ("levels from 29 to 38 ng/mL").
# A real test name is short and doesn't end in a connecting word, and plain
# English words are never units.
_MAX_NAME_WORDS = 6
_MAX_TRAILING_WORDS = 3
_CONNECTING_WORDS = {
    "a", "an", "the", "and", "or", "of", "to", "from", "in", "on", "at", "by",
    "for", "with", "as", "than", "is", "are", "was", "were", "be", "been",
    "above", "below", "over", "under", "between", "about", "around",
    "approximately", "upto", "within", "if", "when", "which", "that",
}
_SENTENCE_BREAK = re.compile(r"[.;!?]\s+[A-Za-z]")


# PDFs and OCR often use look-alike characters: non-breaking/thin spaces,
# and soft hyphens, en/em dashes or minus signs in ranges like "12.0 – 15.5".
_SPACE_CHARS = re.compile(r"[\u00a0\u2000-\u200a\u202f\u205f\u3000\t]")
_DASH_CHARS = re.compile(r"[\u00ad\u2010-\u2015\u2212\ufe63\uff0d]")


def normalise_text(text: str) -> str:
    """Replace look-alike spaces and dashes with plain ASCII ones."""
    return _DASH_CHARS.sub("-", _SPACE_CHARS.sub(" ", text))


def _to_float(num: str) -> float:
    return float(num.replace(",", ""))


def _is_noise(name: str) -> bool:
    """Return True if the extracted name looks like a header or metadata."""
    clean = name.strip().lower()
    if len(clean) < 2 or clean.startswith("_"):
        return True
    tokens = set(re.split(r"[^a-z0-9]+", clean))
    return bool(tokens & _NOISE_WORDS)


# Test method names printed beside or under a test name ("Hemoglobin
# Colorimetric", "TSH ECLIA"). They say how a test was run, not which test.
METHOD_WORDS = {
    "colorimetric", "colorimetry", "photometric", "photometry", "spectrophotometric",
    "spectrophotometry", "calculated", "derived", "direct", "indirect", "enzymatic",
    "kinetic", "eclia", "clia", "cmia", "elisa", "ria", "hplc", "ise", "impedance",
    "cytometry", "flow", "turbidimetric", "turbidimetry", "immunoturbidimetric",
    "immunoturbidimetry", "chemiluminescence", "automated", "analyser", "analyzer",
    "microscopy", "manual",
}

# Short words that follow a result line but are not part of its name
_NOT_CONTINUATION = METHOD_WORDS | {
    "comment", "comments", "note", "notes", "interpretation", "impression",
    "advice", "method", "specimen", "normal", "abnormal", "borderline",
    "desirable", "optimal", "end",
}
_CONTINUATION = re.compile(r"[A-Za-z(][A-Za-z ()/,.'\-]*")


def _is_name_continuation(line: str) -> bool:
    """
    True if a line looks like the wrapped second half of a test name:
    a few words of plain text with no numbers or colon. ALL-CAPS lines are
    section headings ("LIPID PROFILE") unless bracketed, like "(PCV)".
    """
    if len(line) > 30 or len(line.split()) > 3 or not _CONTINUATION.fullmatch(line):
        return False
    if line.isupper() and not (line.startswith("(") and line.endswith(")")):
        return False
    tokens = set(re.split(r"[^a-z]+", line.lower()))
    return not (tokens & (_NOISE_WORDS | _NOT_CONTINUATION))


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


def _looks_like_prose(name: str, rest_of_line: str, has_range: bool) -> bool:
    """True if a matched "result" is really part of a sentence."""
    words = name.split()
    if len(words) > _MAX_NAME_WORDS:
        return True
    # "S. Creatinine" is fine; "...(34 ng/mL). Neuromuscular peak ..." is not
    if len(words) > 3 and _SENTENCE_BREAK.search(name):
        return True
    if words[-1].lower().strip(".,;") in _CONNECTING_WORDS:
        return True
    # Without a reference range, a row may end with a method or flag but not
    # with more sentence. (With a range, a trailing comment is allowed.)
    if has_range:
        return False
    trailing = [w for w in rest_of_line.split() if w.isalpha()]
    return len(trailing) > _MAX_TRAILING_WORDS


def _parse_line(line: str) -> Optional[Dict]:
    if _DATE_OR_TIME.search(line):
        return None

    m = LINE_PATTERN.search(line)
    if not m:
        return None

    name = re.sub(r"\s+", " ", m.group("name")).strip(" ,.-")
    ref_min, ref_max, ref_text = _reference(m)
    if _is_noise(name) or _looks_like_prose(name, line[m.end():], ref_text is not None):
        return None

    # Only trust a unit after the range when the range itself was found
    unit = m.group("unit") or (m.group("unit_after") if ref_text else None)
    if unit and unit.lower().rstrip(".") in _CONNECTING_WORDS:
        unit = None  # "from 29 to 38": "to" is not a unit
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
    previous: Optional[Dict] = None  # result parsed from the previous line

    for line in normalise_text(raw_text).splitlines():
        line = line.strip()
        if not line:
            continue

        # A long test name wrapped onto the next line: "Total Leucocyte" / "Count"
        if previous is not None and _is_name_continuation(line):
            seen_names.discard(previous["test_name_raw"].lower())
            previous["test_name_raw"] += " " + line
            seen_names.add(previous["test_name_raw"].lower())
            previous = None
            continue

        result = _parse_line(line) if len(line) >= 4 else None
        if result and result["test_name_raw"].lower() not in seen_names:
            seen_names.add(result["test_name_raw"].lower())
            results.append(result)
            previous = result
        else:
            previous = None

    return results
