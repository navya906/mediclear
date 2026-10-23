"""
Explanation Service — fetch-or-generate logic for lab result explanations.

Shared by the POST /results/{id}/explain endpoint and the background
report pipeline so both reuse good explanations and replace placeholders
or explanations written for out-of-date patient data.
"""

import logging
import uuid
from typing import List, Optional

from app.ai.generator import expected_prompt_version, generate_explanation, should_regenerate
from app.ai.prompts import MAX_PREVIOUS_RESULTS
from app.database.client import fetch_one

logger = logging.getLogger(__name__)


def _row_date(row: dict) -> str:
    report = row.get("reports") or {}
    return report.get("report_date") or report.get("created_at") or ""


def load_patient_results(supabase, patient_id: Optional[str]) -> List[dict]:
    """
    All matched lab results for a patient, with their report dates.
    Loaded once per request so earlier values can be looked up per test
    without a query for every result. Returns [] on any error, since earlier
    values only add context and must never block an explanation.
    """
    if not patient_id:
        return []
    try:
        return (
            supabase.table("lab_results")
            .select("id, test_definition_id, value, unit, status, reports!inner(patient_id, report_date, created_at)")
            .eq("reports.patient_id", patient_id)
            .execute()
            .data
            or []
        )
    except Exception as exc:
        logger.warning("Could not load earlier results for patient %s: %s", patient_id, exc)
        return []


def previous_results_for(
    patient_results: List[dict],
    result_row: dict,
    current_date: Optional[str],
) -> List[dict]:
    """
    Earlier results for the same test as result_row, oldest first, at most
    MAX_PREVIOUS_RESULTS. "Earlier" means from a report dated before
    current_date (the report this result came from); results from the same
    report, or from later reports, are left out.
    """
    test_id = result_row.get("test_definition_id")
    if not test_id:
        return []
    earlier = []
    for r in patient_results:
        if r.get("test_definition_id") != test_id or r.get("id") == result_row.get("id"):
            continue
        if r.get("value") is None:
            continue
        when = _row_date(r)
        if not when or (current_date and when >= current_date):
            continue
        earlier.append((when, {
            "date": when[:10],
            "value": r["value"],
            "unit": r.get("unit"),
            "status": r.get("status"),
        }))
    earlier.sort(key=lambda pair: pair[0])
    return [item for _, item in earlier][-MAX_PREVIOUS_RESULTS:]


def get_or_create_explanation(
    supabase,
    result_row: dict,
    test_def: dict,
    patient_history: list,
    patient: Optional[dict] = None,
    previous_results: Optional[List[dict]] = None,
) -> Optional[dict]:
    """
    Return the stored explanation for a lab result, generating one if none
    exists, the stored one is a placeholder (LLM error / no-key fallback), or
    it was written before the patient's age, sex, history or earlier results
    changed. Returns the saved explanations row, or None if saving failed.
    """
    existing = fetch_one(
        supabase.table("explanations").select("*").eq("lab_result_id", str(result_row["id"]))
    )
    expected = expected_prompt_version(patient_history, patient, previous_results)
    if existing and not should_regenerate(existing, expected):
        return existing

    explanation = generate_explanation(result_row, test_def, patient_history, patient, previous_results)
    # mode="json" turns the UUID into a string so the request body can be encoded
    payload = explanation.model_dump(mode="json")

    if existing:
        saved = supabase.table("explanations").update(payload).eq("id", existing["id"]).execute()
    else:
        payload["id"] = str(uuid.uuid4())
        saved = supabase.table("explanations").insert(payload).execute()

    return saved.data[0] if saved.data else None
