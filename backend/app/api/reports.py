"""
Reports router — thin controller that delegates to app.services.report_service.

POST /reports/upload       — accept file, validate, store, trigger background processing
GET  /reports              — list reports for logged-in patient
GET  /reports/{id}         — get single report metadata
GET  /reports/{id}/results — get parsed lab results for a report
"""

import uuid
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status

from app.database.client import get_supabase
from app.schemas.report import ReportResponse
from app.schemas.result import LabResultResponse
from app.services.report_service import process_report_background, validate_file
from app.utils.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_patient_id(auth_user_id: str) -> str:
    supabase = get_supabase()
    result = supabase.table("patients").select("id").eq("auth_user_id", auth_user_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found.")
    return result.data["id"]


@router.post("/upload", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    patient_id = _get_patient_id(user_id)
    supabase = get_supabase()

    file_bytes = await file.read()
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else "pdf"

    # Validate file type and size
    try:
        validate_file(file_bytes, file_ext)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    report_id = str(uuid.uuid4())
    storage_path = f"{patient_id}/{report_id}/{file.filename}"

    # Upload to Supabase Storage
    try:
        supabase.storage.from_("lab-reports").upload(
            storage_path, file_bytes, {"content-type": file.content_type}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {str(e)}")

    # Create reports row
    payload = {
        "id": report_id,
        "patient_id": patient_id,
        "file_name": file.filename,
        "file_type": file_ext,
        "storage_path": storage_path,
        "processing_status": "uploaded",
    }
    result = supabase.table("reports").insert(payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create report record.")

    # Trigger background processing
    background_tasks.add_task(
        process_report_background, report_id, file_bytes, file_ext, patient_id
    )

    return ReportResponse(**result.data[0])


@router.get("", response_model=List[ReportResponse])
def list_reports(user_id: str = Depends(get_current_user)):
    patient_id = _get_patient_id(user_id)
    supabase = get_supabase()
    result = (
        supabase.table("reports")
        .select("*")
        .eq("patient_id", patient_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [ReportResponse(**r) for r in (result.data or [])]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: UUID, user_id: str = Depends(get_current_user)):
    patient_id = _get_patient_id(user_id)
    supabase = get_supabase()
    result = (
        supabase.table("reports")
        .select("*")
        .eq("id", str(report_id))
        .eq("patient_id", patient_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Report not found.")
    return ReportResponse(**result.data)


@router.get("/{report_id}/results", response_model=List[LabResultResponse])
def get_report_results(report_id: UUID, user_id: str = Depends(get_current_user)):
    patient_id = _get_patient_id(user_id)
    supabase = get_supabase()

    report_res = (
        supabase.table("reports")
        .select("id")
        .eq("id", str(report_id))
        .eq("patient_id", patient_id)
        .single()
        .execute()
    )
    if not report_res.data:
        raise HTTPException(status_code=404, detail="Report not found.")

    result = (
        supabase.table("lab_results")
        .select("*, test_definition:test_definitions(*)")
        .eq("report_id", str(report_id))
        .execute()
    )
    return [LabResultResponse(**r) for r in (result.data or [])]
