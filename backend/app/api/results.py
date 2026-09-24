"""
Results router.

POST /results/{id}/explain — Generate and save an AI explanation for a result
GET  /results/{id}/explanation — Get the existing explanation
"""

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.ai.generator import generate_explanation
from app.database.client import get_supabase
from app.schemas.explanation import ExplanationResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/results", tags=["results"])


def _get_patient_id(auth_user_id: str) -> str:
    supabase = get_supabase()
    result = supabase.table("patients").select("id").eq("auth_user_id", auth_user_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found.")
    return result.data["id"]


@router.post("/{result_id}/explain", response_model=ExplanationResponse)
def explain_result(result_id: UUID, user_id: str = Depends(get_current_user)):
    patient_id = _get_patient_id(user_id)
    supabase = get_supabase()

    # 1. Fetch the lab result, joined with report (to verify ownership) and test_def
    result_res = supabase.table("lab_results").select("*, reports(*), test_definitions(*)").eq("id", str(result_id)).single().execute()
    if not result_res.data:
        raise HTTPException(status_code=404, detail="Result not found.")
    
    result_data = result_res.data
    report_data = result_data.get("reports")
    test_def = result_data.get("test_definitions") or {}

    if not report_data or report_data.get("patient_id") != patient_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this result.")

    # 2. Check if explanation already exists
    existing = supabase.table("explanations").select("*").eq("lab_result_id", str(result_id)).execute()
    if existing.data:
        return ExplanationResponse(**existing.data[0])

    # 3. Fetch patient history for context
    history_res = supabase.table("patient_history").select("*").eq("patient_id", patient_id).execute()
    patient_history = history_res.data or []

    # 4. Generate Explanation
    explanation_obj = generate_explanation(result_data, test_def, patient_history)

    # 5. Save to DB
    insert_payload = explanation_obj.model_dump()
    insert_payload["id"] = str(uuid.uuid4())
    
    save_res = supabase.table("explanations").insert(insert_payload).execute()
    if not save_res.data:
        raise HTTPException(status_code=500, detail="Failed to save explanation.")

    return ExplanationResponse(**save_res.data[0])


@router.get("/{result_id}/explanation", response_model=ExplanationResponse)
def get_explanation(result_id: UUID, user_id: str = Depends(get_current_user)):
    # Very similar logic to above to verify ownership
    patient_id = _get_patient_id(user_id)
    supabase = get_supabase()

    # Verify ownership via report
    result_res = supabase.table("lab_results").select("reports(patient_id)").eq("id", str(result_id)).single().execute()
    if not result_res.data or result_res.data.get("reports", {}).get("patient_id") != patient_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this result.")

    existing = supabase.table("explanations").select("*").eq("lab_result_id", str(result_id)).single().execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Explanation not found.")

    return ExplanationResponse(**existing.data)
