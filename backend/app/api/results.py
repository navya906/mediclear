"""
Results router.

POST /results/{id}/explain — Generate and save an AI explanation for a result
GET  /results/{id}/explanation — Get the existing explanation
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.client import fetch_one, get_supabase
from app.schemas.explanation import ExplanationResponse
from app.services.explanation_service import (
    get_or_create_explanation,
    load_patient_results,
    previous_results_for,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/results", tags=["results"])


def _get_patient(auth_user_id: str) -> dict:
    """Return the patients row (id, sex, date_of_birth) for the auth user, or 404."""
    supabase = get_supabase()
    patient = fetch_one(
        supabase.table("patients").select("id, sex, date_of_birth").eq("auth_user_id", auth_user_id)
    )
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found.")
    return patient


@router.post("/{result_id}/explain", response_model=ExplanationResponse)
def explain_result(result_id: UUID, user_id: str = Depends(get_current_user)):
    patient = _get_patient(user_id)
    patient_id = patient["id"]
    supabase = get_supabase()

    # 1. Fetch the lab result, joined with report (to verify ownership) and test_def
    result_data = fetch_one(supabase.table("lab_results").select("*, reports(*), test_definitions(*)").eq("id", str(result_id)))
    if not result_data:
        raise HTTPException(status_code=404, detail="Result not found.")

    report_data = result_data.get("reports")
    test_def = result_data.get("test_definitions") or {}

    if not report_data or report_data.get("patient_id") != patient_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this result.")

    # 2. Fetch patient history for context
    history_res = supabase.table("patient_history").select("*").eq("patient_id", patient_id).execute()
    patient_history = history_res.data or []

    # 3. Earlier results for the same test, from reports dated before this one
    current_date = report_data.get("report_date") or report_data.get("created_at")
    previous = previous_results_for(load_patient_results(supabase, patient_id), result_data, current_date)

    # 4. Reuse the stored explanation, or generate one. Also replaces placeholders
    #    left by an LLM failure or missing API key, and explanations written
    #    before the patient's age, sex, history or earlier results changed.
    saved = get_or_create_explanation(supabase, result_data, test_def, patient_history, patient, previous)
    if not saved:
        raise HTTPException(status_code=500, detail="Failed to save explanation.")

    return ExplanationResponse(**saved)


@router.get("/{result_id}/explanation", response_model=ExplanationResponse)
def get_explanation(result_id: UUID, user_id: str = Depends(get_current_user)):
    # Very similar logic to above to verify ownership
    patient_id = _get_patient(user_id)["id"]
    supabase = get_supabase()

    # Verify ownership via report
    result_data = fetch_one(supabase.table("lab_results").select("reports(patient_id)").eq("id", str(result_id)))
    if not result_data:
        raise HTTPException(status_code=404, detail="Result not found.")
    if (result_data.get("reports") or {}).get("patient_id") != patient_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this result.")

    existing = fetch_one(supabase.table("explanations").select("*").eq("lab_result_id", str(result_id)))
    if not existing:
        raise HTTPException(status_code=404, detail="Explanation not found.")

    return ExplanationResponse(**existing)
