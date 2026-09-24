"""
History Service — database operations for patient_history rows.

Extracted from app.api.history to keep the router thin.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status

from app.database.client import get_supabase
from app.schemas.history import HistoryCreate, HistoryResponse, HistoryUpdate


def get_patient_id(auth_user_id: str) -> str:
    """Resolve the patients.id for the given Supabase auth user ID."""
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


def assert_owns_entry(entry_id: str, patient_id: str) -> dict:
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


def create_entry(body: HistoryCreate, patient_id: str) -> HistoryResponse:
    supabase = get_supabase()
    payload = body.model_dump(exclude_none=True)
    payload["patient_id"] = patient_id
    for field in ("start_date", "end_date"):
        if field in payload and payload[field] is not None:
            payload[field] = payload[field].isoformat()
    result = supabase.table("patient_history").insert(payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create history entry.")
    return HistoryResponse(**result.data[0])


def list_entries(patient_id: str, category: Optional[str] = None) -> List[HistoryResponse]:
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
    return [HistoryResponse(**row) for row in (result.data or [])]


def update_entry(entry_id: UUID, body: HistoryUpdate, patient_id: str) -> HistoryResponse:
    assert_owns_entry(str(entry_id), patient_id)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No fields provided for update.")
    for field in ("start_date", "end_date"):
        if field in updates and updates[field] is not None:
            updates[field] = updates[field].isoformat()
    supabase = get_supabase()
    result = supabase.table("patient_history").update(updates).eq("id", str(entry_id)).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to update history entry.")
    return HistoryResponse(**result.data[0])


def delete_entry(entry_id: UUID, patient_id: str) -> None:
    assert_owns_entry(str(entry_id), patient_id)
    supabase = get_supabase()
    supabase.table("patient_history").delete().eq("id", str(entry_id)).execute()
