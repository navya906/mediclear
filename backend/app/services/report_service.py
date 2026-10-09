"""
Report Service — background processing pipeline for uploaded lab reports.

Moved out of app.api.reports to keep the router thin and testable.
"""

import logging
from typing import List

from postgrest.exceptions import APIError

from app.database.client import fetch_one, get_supabase
from app.ocr.core import extract_text_from_file
from app.parser.core import normalize_and_score, parse_lab_text
from app.services.explanation_service import get_or_create_explanation

logger = logging.getLogger(__name__)

# Maximum file size accepted (10 MB)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def validate_file(file_bytes: bytes, file_ext: str) -> None:
    """
    Raise ValueError if the file does not pass validation checks.
    """
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File is too large ({len(file_bytes) // (1024*1024)} MB). "
            f"Maximum allowed size is {MAX_FILE_SIZE_BYTES // (1024*1024)} MB."
        )
    if file_ext not in ("pdf", "jpg", "jpeg", "png"):
        raise ValueError(
            f"Unsupported file type '{file_ext}'. "
            "Accepted types: PDF, JPG, JPEG, PNG."
        )


def _insert_lab_results(supabase, payloads: List[dict]) -> List[dict]:
    """
    Insert lab_results rows, including the needs_review flag.

    If the needs_review column hasn't been added yet
    (data/migrations/001_lab_results_needs_review.sql), retry without it so
    processing still succeeds; the report-level status still records it.
    """
    if not payloads:
        return []
    try:
        return supabase.table("lab_results").insert(payloads).execute().data or []
    except APIError as exc:
        # PGRST204: column not found in the schema cache
        if exc.code != "PGRST204" or "needs_review" not in (exc.message or ""):
            raise
        logger.warning("lab_results.needs_review column missing; run the migration to persist it")
        stripped = [{k: v for k, v in p.items() if k != "needs_review"} for p in payloads]
        return supabase.table("lab_results").insert(stripped).execute().data or []


def process_report_background(
    report_id: str,
    file_bytes: bytes,
    file_ext: str,
    patient_id: str,
) -> None:
    """
    Full OCR → parse → normalize → save → auto-explain pipeline.
    Updates report processing_status throughout.
    Called as a FastAPI BackgroundTask.
    """
    supabase = get_supabase()

    try:
        # ── 1. Mark as processing ──────────────────────────────────────────
        supabase.table("reports").update(
            {"processing_status": "processing"}
        ).eq("id", report_id).execute()

        # ── 2. OCR ────────────────────────────────────────────────────────
        raw_text = extract_text_from_file(file_bytes, file_ext)
        if not raw_text.strip():
            raise ValueError("No text could be extracted from the file.")

        # ── 3. Parse ──────────────────────────────────────────────────────
        parsed_results = parse_lab_text(raw_text)

        # ── 4. Fetch test definitions and patient context ─────────────────
        defs_result = supabase.table("test_definitions").select("*").execute()
        test_definitions = defs_result.data or []
        defs_by_id = {td["id"]: td for td in test_definitions}

        patient = fetch_one(
            supabase.table("patients").select("id, sex, date_of_birth").eq("id", patient_id)
        ) or {}

        # ── 5. Normalize + insert lab_results ─────────────────────────────
        insert_payloads = [
            {**normalize_and_score(pr, test_definitions, patient.get("sex")), "report_id": report_id}
            for pr in parsed_results
        ]
        saved_results = _insert_lab_results(supabase, insert_payloads)

        # ── 6. Mark completed, or needs_review if any value is uncertain ───
        any_needs_review = any(p["needs_review"] for p in insert_payloads)
        supabase.table("reports").update(
            {"processing_status": "needs_review" if any_needs_review else "completed"}
        ).eq("id", report_id).execute()

        # ── 7. Auto-generate AI explanations for each result ──────────────
        history_res = supabase.table("patient_history").select("*").eq("patient_id", patient_id).execute()
        patient_history = history_res.data or []

        for result_row in saved_results:
            try:
                if not result_row.get("id"):
                    continue
                test_def = defs_by_id.get(result_row.get("test_definition_id")) or {}
                get_or_create_explanation(supabase, result_row, test_def, patient_history, patient)
            except Exception as explain_err:
                logger.warning("Auto-explanation failed for result %s: %s", result_row.get("id"), explain_err)

    except Exception as e:
        logger.error("Report processing failed for %s: %s", report_id, e)
        supabase.table("reports").update({
            "processing_status": "failed",
            "error_message": str(e),
        }).eq("id", report_id).execute()
