"""
Patient history router.

POST   /history            — add a history entry
GET    /history            — list all entries (optional ?category= filter)
PATCH  /history/{id}       — update an entry
DELETE /history/{id}       — delete an entry
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database.client import get_supabase
from app.schemas.history import (
    HistoryCreate,
    HistoryListResponse,
    HistoryResponse,
    HistoryUpdate,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/history", tags=["history"])


def _get_patient_id(auth_user_id: str) -> str:
    """Look up the patients.id for the given auth_user_id."""
    supabase = get_supabase()
    result = (
        supabase.table("patients")
        .select("id")
        .eq("auth_user_id", auth_user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found. Please complete registration.",
        )
    return result.data["id"]


def _assert_owns_entry(entry_id: str, patient_id: str) -> dict:
    """Fetch a history entry and verify it belongs to the current patient."""
    supabase = get_supabase()
    result = (
        supabase.table("patient_history")
        .select("*")
        .eq("id", entry_id)
        .eq("patient_id", patient_id)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History entry not found.",
        )
    return result.data


@router.post(
    "",
    response_model=HistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a medical history entry",
)
def add_history(
    body: HistoryCreate,
    user_id: str = Depends(get_current_user),
):
    patient_id = _get_patient_id(user_id)
    supabase = get_supabase()

    payload = body.model_dump(exclude_none=True)
    payload["patient_id"] = patient_id

    # Convert dates to ISO strings
    for field in ("start_date", "end_date"):
        if field in payload and payload[field] is not None:
            payload[field] = payload[field].isoformat()

    result = supabase.table("patient_history").insert(payload).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create history entry.",
        )

    return HistoryResponse(**result.data[0])


@router.get(
    "",
    response_model=HistoryListResponse,
    summary="List medical history entries",
)
def list_history(
    category: Optional[str] = Query(
        None,
        description="Filter by category: condition, medication, allergy, symptom, surgery, family_history, other",
    ),
    user_id: str = Depends(get_current_user),
):
    patient_id = _get_patient_id(user_id)
    supabase = get_supabase()

    query = (
        supabase.table("patient_history")
        .select("*")
        .eq("patient_id", patient_id)
        .order("created_at", desc=True)
    )

    if category:
        query = query.eq("category", category)

    result = query.execute()
    entries = [HistoryResponse(**row) for row in (result.data or [])]
    return HistoryListResponse(entries=entries, total=len(entries))


@router.patch(
    "/{entry_id}",
    response_model=HistoryResponse,
    summary="Update a medical history entry",
)
def update_history(
    entry_id: UUID,
    body: HistoryUpdate,
    user_id: str = Depends(get_current_user),
):
    patient_id = _get_patient_id(user_id)
    _assert_owns_entry(str(entry_id), patient_id)

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields provided for update.",
        )

    for field in ("start_date", "end_date"):
        if field in updates and updates[field] is not None:
            updates[field] = updates[field].isoformat()

    supabase = get_supabase()
    result = (
        supabase.table("patient_history")
        .update(updates)
        .eq("id", str(entry_id))
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update history entry.",
        )

    return HistoryResponse(**result.data[0])


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a medical history entry",
)
def delete_history(
    entry_id: UUID,
    user_id: str = Depends(get_current_user),
):
    patient_id = _get_patient_id(user_id)
    _assert_owns_entry(str(entry_id), patient_id)

    supabase = get_supabase()
    supabase.table("patient_history").delete().eq("id", str(entry_id)).execute()
