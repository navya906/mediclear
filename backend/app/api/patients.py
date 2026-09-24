"""
Patients router.

GET  /patients/me   — return logged-in patient's profile
PATCH /patients/me  — update date_of_birth and/or sex
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.client import get_supabase
from app.schemas.patient import PatientResponse, PatientUpdate
from app.utils.auth import get_current_user

router = APIRouter(prefix="/patients", tags=["patients"])


def _get_patient_by_auth_user(auth_user_id: str) -> dict:
    """Fetch the patients row for the given auth_user_id. Raises 404 if not found."""
    supabase = get_supabase()
    result = (
        supabase.table("patients")
        .select("*")
        .eq("auth_user_id", auth_user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )
    return result.data


@router.get(
    "/me",
    response_model=PatientResponse,
    summary="Get the logged-in patient's profile",
)
def get_my_profile(user_id: str = Depends(get_current_user)):
    return PatientResponse(**_get_patient_by_auth_user(user_id))


@router.patch(
    "/me",
    response_model=PatientResponse,
    summary="Update the logged-in patient's profile",
)
def update_my_profile(
    body: PatientUpdate,
    user_id: str = Depends(get_current_user),
):
    # Only include fields that were actually provided
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields provided for update.",
        )

    # Convert date to ISO string for Supabase
    if "date_of_birth" in updates:
        updates["date_of_birth"] = updates["date_of_birth"].isoformat()

    supabase = get_supabase()
    patient = _get_patient_by_auth_user(user_id)

    result = (
        supabase.table("patients")
        .update(updates)
        .eq("id", patient["id"])
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile.",
        )

    return PatientResponse(**result.data[0])


@router.get("/me/trends")
def get_patient_trends(
    test_name: str,
    user_id: str = Depends(get_current_user)
):
    supabase = get_supabase()
    
    # Get patient ID
    patient_res = supabase.table("patients").select("id").eq("auth_user_id", user_id).single().execute()
    if not patient_res.data:
        raise HTTPException(status_code=404, detail="Patient profile not found.")
    patient_id = patient_res.data["id"]

    # Fetch lab results joined with reports for the test definition canonical name
    # We filter by test canonical_name and order by report created_at
    query = supabase.table("lab_results")\
        .select("value, reports!inner(created_at), test_definitions!inner(canonical_name)")\
        .eq("reports.patient_id", patient_id)\
        .eq("test_definitions.canonical_name", test_name)\
        .order("reports.created_at", asc=True)\
        .execute()

    results = query.data or []
    
    # Format the response for recharts (needs date and value)
    trends = []
    for r in results:
        report_data = r.get("reports", {})
        if report_data and r.get("value") is not None:
            trends.append({
                "date": report_data.get("created_at")[:10], # YYYY-MM-DD
                "value": r["value"]
            })
            
    return trends
