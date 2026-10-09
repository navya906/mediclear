"""
Normalizer — matches raw test names to canonical test definitions
and computes result status.

Matching strategy (in order):
  1. Exact match on canonical name, display name, or a known alias
  2. Phrase match — every word of a name/alias appears in the raw name;
     the most specific (longest) phrase wins
  3. Fallback reference ranges when the report didn't include them
"""

import re
from typing import Dict, List, Optional

from app.parser.parser import METHOD_WORDS
from app.parser.reference_ranges import get_fallback_range

# How far outside the range a value must be (as a fraction of the range width)
# to be flagged CRITICAL instead of HIGH / LOW.
CRITICAL_MULTIPLIER = 1.5  # > 150% of range width outside boundary → CRITICAL


# Common lab-report spellings / abbreviations, keyed by canonical_name.
# These supplement the canonical and display names from test_definitions.
ALIASES: Dict[str, List[str]] = {
    "hemoglobin":        ["hb", "hgb", "haemoglobin"],
    "wbc":               ["tlc", "white blood cells", "total leucocyte count", "total leukocyte count"],
    "rbc":               ["red blood cells", "rbc count"],
    "platelets":         ["plt", "platelet", "platelet count"],
    "hematocrit":        ["hct", "pcv", "haematocrit", "packed cell volume"],
    "total_cholesterol": ["cholesterol", "serum cholesterol"],
    "ldl_cholesterol":   ["ldl", "ldl c"],
    "hdl_cholesterol":   ["hdl", "hdl c"],
    "triglycerides":     ["tg", "triglyceride"],
    "free_t3":           ["ft3"],
    "free_t4":           ["ft4"],
}

# Words that describe the sample or method rather than which test it is.
_FILLER_TOKENS = METHOD_WORDS | {
    "serum", "plasma", "blood", "whole", "level", "levels", "test", "s", "of", "the",
}

# A definition must account for MORE than this fraction of the raw name's
# meaningful tokens. Stops "Hemoglobin A1c" from matching plain "Hemoglobin".
_MIN_COVERAGE = 0.5


def _tokens(text: str) -> List[str]:
    """Lowercase and split on anything that isn't a letter or digit."""
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def _phrases_for(td: Dict) -> List[List[str]]:
    """All token phrases that can identify a test definition."""
    canonical = td.get("canonical_name", "") or ""
    display = td.get("display_name", "") or ""
    texts = [canonical.replace("_", " "), display]
    # "Free T3 (Triiodothyronine)" → also "Free T3" and "Triiodothyronine"
    texts.append(re.sub(r"\(.*?\)", " ", display))
    texts.extend(re.findall(r"\((.*?)\)", display))
    texts.extend(ALIASES.get(canonical.lower(), []))
    return [p for p in (_tokens(t) for t in texts) if p]


def _match_definition(raw_name: str, test_definitions: List[Dict]) -> Optional[Dict]:
    """
    Pick the test definition that best explains raw_name.

    A phrase matches when all of its tokens appear in the raw name. Among
    matching definitions the one with the longest matched phrase wins, so
    "HDL Cholesterol" prefers hdl_cholesterol over the bare "cholesterol"
    alias of total_cholesterol.
    """
    raw_tokens = set(_tokens(raw_name))
    meaningful = raw_tokens - _FILLER_TOKENS
    if not meaningful:
        return None

    best_def: Optional[Dict] = None
    best_score = (0.0, 0)
    for td in test_definitions:
        phrases = _phrases_for(td)

        # Exact phrase match is unambiguous
        if any(set(p) == raw_tokens or set(p) == meaningful for p in phrases):
            return td

        matched = [p for p in phrases if set(p) <= raw_tokens]
        if not matched:
            continue
        covered = set().union(*matched) & meaningful
        coverage = len(covered) / len(meaningful)
        if coverage <= _MIN_COVERAGE:
            continue
        score = (coverage, max(len(p) for p in matched))
        if score > best_score:
            best_def, best_score = td, score

    return best_def


# Spellings of the same unit, after _unit_key() normalisation
_UNIT_EQUIVALENTS = [
    {"k/ul", "10^3/ul", "x10^3/ul", "10³/ul", "x10³/ul", "thou/ul", "10^3/cumm", "thou/cumm"},
    {"m/ul", "10^6/ul", "x10^6/ul", "10⁶/ul", "x10⁶/ul", "mill/ul", "mill/cumm", "million/cumm"},
    {"miu/l", "uiu/ml"},
]


def _unit_key(unit: str) -> str:
    return re.sub(r"\s+", "", unit.lower().replace("µ", "u").replace("μ", "u").replace("×", "x"))


def _units_compatible(parsed_unit: Optional[str], fallback_unit: str) -> bool:
    """True if the parsed unit is missing or means the same as the fallback unit."""
    if not parsed_unit:
        return True
    a, b = _unit_key(parsed_unit), _unit_key(fallback_unit)
    return a == b or any(a in group and b in group for group in _UNIT_EQUIVALENTS)


def _compute_status(value: float, ref_min: Optional[float], ref_max: Optional[float]) -> str:
    """
    Compute status string from value and reference bounds.
    Returns: CRITICAL | HIGH | LOW | NORMAL | UNKNOWN
    """
    if value is None or (ref_min is None and ref_max is None):
        return "UNKNOWN"

    # One-sided ranges ("< 200", "> 40") have no width, so no CRITICAL level
    if ref_min is None:
        return "HIGH" if value > ref_max else "NORMAL"
    if ref_max is None:
        return "LOW" if value < ref_min else "NORMAL"

    range_width = ref_max - ref_min
    critical_margin = range_width * CRITICAL_MULTIPLIER

    if value < ref_min:
        if value < ref_min - critical_margin:
            return "CRITICAL"
        return "LOW"
    elif value > ref_max:
        if value > ref_max + critical_margin:
            return "CRITICAL"
        return "HIGH"
    return "NORMAL"


def normalize_and_score(
    parsed_result: Dict,
    test_definitions: List[Dict],
    sex: Optional[str] = None,
) -> Dict:
    """
    Match a parsed result to a canonical test definition and compute its status.

    Updates the dict in place with:
      - test_definition_id
      - status (LOW / NORMAL / HIGH / CRITICAL / UNKNOWN)
      - needs_review flag for low-confidence extractions
      - fills missing reference range from fallback table if possible,
        using the patient's sex for sex-dependent tests
    """
    raw_name = parsed_result.get("test_name_raw", "").lower()
    ref_min: Optional[float] = parsed_result.get("reference_min")
    ref_max: Optional[float] = parsed_result.get("reference_max")
    confidence: float = parsed_result.get("extraction_confidence", 1.0)

    # ── Step 1: find matching test definition ──────────────────────────────
    matched_def = _match_definition(raw_name, test_definitions)

    # ── Step 2: fill missing reference range from fallback table ──────────
    # Only when the report gave no range at all, and only if the units agree:
    # a fallback in K/uL is meaningless for a count reported in /cumm.
    if ref_min is None and ref_max is None and matched_def:
        canonical_name = matched_def.get("canonical_name", "")
        fallback = get_fallback_range(canonical_name, sex)
        if fallback and _units_compatible(parsed_result.get("unit"), fallback[2]):
            ref_min, ref_max, fallback_unit = fallback
            # Only overwrite unit if the parsed one is empty
            if not parsed_result.get("unit"):
                parsed_result["unit"] = fallback_unit
            parsed_result["reference_min"] = ref_min
            parsed_result["reference_max"] = ref_max
            parsed_result["reference_text"] = f"{ref_min:g} - {ref_max:g}"

    # ── Step 3: compute status ─────────────────────────────────────────────
    value = parsed_result.get("value")
    status = _compute_status(value, ref_min, ref_max)

    # ── Step 4: needs_review flag ──────────────────────────────────────────
    needs_review = confidence < 0.75 or status == "UNKNOWN"

    return {
        **parsed_result,
        "reference_min": ref_min,
        "reference_max": ref_max,
        "test_definition_id": matched_def["id"] if matched_def else None,
        "status": status,
        "needs_review": needs_review,
    }
