"""
Normalizer — matches raw test names to canonical test definitions
and computes result status.

Matching strategy (in order):
  1. Exact canonical_name / display_name match (case-insensitive)
  2. Token overlap — any word in the canonical name appears in the raw name
  3. Fallback reference ranges when the report didn't include them
"""

from typing import Dict, List, Optional

from app.parser.reference_ranges import get_fallback_range

# How far outside the range a value must be (as a fraction of the range width)
# to be flagged CRITICAL instead of HIGH / LOW.
CRITICAL_MULTIPLIER = 1.5  # > 150% of range width outside boundary → CRITICAL


def _token_match(raw_name: str, canonical: str, display: str) -> bool:
    """Return True if any significant token from the canonical/display name is in raw_name."""
    raw_tokens = set(raw_name.lower().split())
    for ref in (canonical, display):
        ref_tokens = [t for t in ref.lower().split("_") if len(t) > 2]
        if any(tok in raw_tokens for tok in ref_tokens):
            return True
    return False


def _compute_status(value: float, ref_min: Optional[float], ref_max: Optional[float]) -> str:
    """
    Compute status string from value and reference bounds.
    Returns: CRITICAL | HIGH | LOW | NORMAL | UNKNOWN
    """
    if value is None or ref_min is None or ref_max is None:
        return "UNKNOWN"

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


def normalize_and_score(parsed_result: Dict, test_definitions: List[Dict]) -> Dict:
    """
    Match a parsed result to a canonical test definition and compute its status.

    Updates the dict in place with:
      - test_definition_id
      - status (LOW / NORMAL / HIGH / CRITICAL / UNKNOWN)
      - needs_review flag for low-confidence extractions
      - fills missing reference range from fallback table if possible
    """
    raw_name = parsed_result.get("test_name_raw", "").lower()
    ref_min: Optional[float] = parsed_result.get("reference_min")
    ref_max: Optional[float] = parsed_result.get("reference_max")
    confidence: float = parsed_result.get("extraction_confidence", 1.0)

    # ── Step 1: find matching test definition ──────────────────────────────
    matched_def: Optional[Dict] = None

    # Exact match first
    for td in test_definitions:
        canonical = td.get("canonical_name", "").lower()
        display = td.get("display_name", "").lower()
        if canonical == raw_name or display == raw_name:
            matched_def = td
            break

    # Token overlap fallback
    if matched_def is None:
        for td in test_definitions:
            canonical = td.get("canonical_name", "")
            display = td.get("display_name", "")
            if _token_match(raw_name, canonical, display):
                matched_def = td
                break

    # ── Step 2: fill missing reference range from fallback table ──────────
    if (ref_min is None or ref_max is None) and matched_def:
        canonical_name = matched_def.get("canonical_name", "")
        fallback = get_fallback_range(canonical_name)
        if fallback:
            ref_min, ref_max, fallback_unit = fallback
            # Only overwrite unit if the parsed one is empty
            if not parsed_result.get("unit"):
                parsed_result["unit"] = fallback_unit
            parsed_result["reference_min"] = ref_min
            parsed_result["reference_max"] = ref_max
            parsed_result["reference_text"] = f"{ref_min} - {ref_max}"

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
