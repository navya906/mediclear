"""
Report Service — background processing pipeline for uploaded lab reports.

Moved out of app.api.reports to keep the router thin and testable.
"""

import uuid
import logging

from app.database.client import get_supabase
from app.ocr.core import extract_text_from_file
from app.parser.core import normalize_and_score, parse_lab_text
from app.ai.generator import generate_explanation

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

        # ── 4. Fetch test definitions ──────────────────────────────────────
        defs_result = supabase.table("test_definitions").select("*").execute()
        test_definitions = defs_result.data or []

        # ── 5. Normalize + insert lab_results ─────────────────────────────
        insert_payloads = []
        needs_review_flags = []  # track separately — column not in DB schema
        for pr in parsed_results:
            normalized = normalize_and_score(pr, test_definitions)
            normalized["report_id"] = report_id
            # Pop needs_review: the lab_results table doesn't have this column.
            # Run `ALTER TABLE lab_results ADD COLUMN needs_review BOOLEAN DEFAULT FALSE;`
            # in Supabase SQL Editor if you want to persist this flag.
            needs_review_flags.append(normalized.pop("needs_review", False))
            insert_payloads.append(normalized)

        saved_results = []
        if insert_payloads:
            res = supabase.table("lab_results").insert(insert_payloads).execute()
            saved_results = res.data or []

        # ── 6. Mark completed ──────────────────────────────────────────────
        supabase.table("reports").update(
            {"processing_status": "completed"}
        ).eq("id", report_id).execute()

        # ── 7. Auto-generate AI explanations for each result ──────────────
        history_res = supabase.table("patient_history").select("*").eq("patient_id", patient_id).execute()
        patient_history = history_res.data or []

        for result_row in saved_results:
            try:
                result_id = result_row.get("id")
                if not result_id:
                    continue

                # Skip if already explained
                existing = supabase.table("explanations").select("id").eq("lab_result_id", result_id).execute()
                if existing.data:
                    continue

                test_def = {}
                if result_row.get("test_definition_id"):
                    td_res = supabase.table("test_definitions").select("*").eq("id", result_row["test_definition_id"]).single().execute()
                    test_def = td_res.data or {}

                explanation_obj = generate_explanation(result_row, test_def, patient_history)
                payload = explanation_obj.model_dump()
                payload["id"] = str(uuid.uuid4())
                supabase.table("explanations").insert(payload).execute()

            except Exception as explain_err:
                logger.warning("Auto-explanation failed for result %s: %s", result_row.get("id"), explain_err)

    except Exception as e:
        logger.error("Report processing failed for %s: %s", report_id, e)
        supabase.table("reports").update({
            "processing_status": "failed",
            "error_message": str(e),
        }).eq("id", report_id).execute()
