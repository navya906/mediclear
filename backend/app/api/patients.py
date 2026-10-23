"""
Patients router.

GET  /patients/me   — return logged-in patient's profile
PATCH /patients/me  — update date_of_birth and/or sex
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.client import fetch_one, get_supabase
from app.schemas.patient import PatientResponse, PatientUpdate
from app.utils.auth import get_current_user

router = APIRouter(prefix="/patients", tags=["patients"])


def _get_patient_by_auth_user(auth_user_id: str) -> dict:
    """Fetch the patients row for the given auth_user_id. Raises 404 if not found."""
    supabase = get_supabase()
    patient = fetch_one(
        supabase.table("patients")
        .select("*")
        .eq("auth_user_id", auth_user_id)
    )
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )
    return patient


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


def _result_date(row: dict) -> str:
    """Date for a lab result: the date printed on the report, else the upload time."""
    report = row.get("reports") or {}
    return report.get("report_date") or report.get("created_at") or ""


@router.get("/me/trends/tests", summary="Tests this patient has results for")
def get_trend_tests(user_id: str = Depends(get_current_user)):
    """
    One entry per matched test the patient has at least one numeric result for,
    most readings first. Lets the dashboard offer only tests that will draw a
    chart, and pick a sensible default, even when there is very little data.
    """
    supabase = get_supabase()
    patient_id = _get_patient_by_auth_user(user_id)["id"]

    rows = (
        supabase.table("lab_results")
        .select(
            "value, reports!inner(patient_id, report_date, created_at), "
            "test_definitions!inner(canonical_name, display_name, category)"
        )
        .eq("reports.patient_id", patient_id)
        .execute()
        .data
        or []
    )

    tests: dict = {}
    for r in rows:
        if r.get("value") is None:
            continue
        td = r.get("test_definitions") or {}
        name = td.get("canonical_name")
        if not name:
            continue
        entry = tests.setdefault(name, {
            "value": name,
            "label": td.get("display_name") or name,
            "category": td.get("category"),
            "count": 0,
            "latest_date": "",
        })
        entry["count"] += 1
        entry["latest_date"] = max(entry["latest_date"], _result_date(r)[:10])

    return sorted(tests.values(), key=lambda t: (-t["count"], t["label"].lower()))


@router.get("/me/trends")
def get_patient_trends(
    test_name: str,
    user_id: str = Depends(get_current_user)
):
    supabase = get_supabase()
    patient_id = _get_patient_by_auth_user(user_id)["id"]

    # Fetch lab results joined with reports for the test definition canonical name
    query = supabase.table("lab_results")\
        .select(
            "value, unit, status, reference_min, reference_max, "
            "reports!inner(id, file_name, report_date, created_at), "
            "test_definitions!inner(canonical_name)"
        )\
        .eq("reports.patient_id", patient_id)\
        .eq("test_definitions.canonical_name", test_name)\
        .execute()

    results = query.data or []

    # Format the response for the chart. Prefer the date printed on the report;
    # fall back to the upload date. Unit, status and reference range let the
    # chart show whether a value is in range even with a single reading.
    trends = []
    for r in results:
        report_data = r.get("reports") or {}
        report_date = _result_date(r)
        if report_date and r.get("value") is not None:
            trends.append({
                "date": report_date[:10],  # YYYY-MM-DD
                "sort_key": report_date,   # full timestamp keeps same-day uploads in order
                "value": r["value"],
                "unit": r.get("unit"),
                "status": r.get("status"),
                "reference_min": r.get("reference_min"),
                "reference_max": r.get("reference_max"),
                "report_id": report_data.get("id"),
                "file_name": report_data.get("file_name"),
            })

    # PostgREST can't order parent rows by an embedded column here, so sort in Python
    trends.sort(key=lambda t: t["sort_key"])
    for t in trends:
        del t["sort_key"]
    return trends
