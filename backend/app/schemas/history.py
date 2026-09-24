"""Pydantic schemas for the patient_history table."""

from datetime import date, datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel

HISTORY_CATEGORIES = Literal[
    "condition",
    "medication",
    "allergy",
    "symptom",
    "surgery",
    "family_history",
    "other",
]


class HistoryCreate(BaseModel):
    category: HISTORY_CATEGORIES
    title: Optional[str] = None
    description: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class HistoryUpdate(BaseModel):
    category: Optional[HISTORY_CATEGORIES] = None
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class HistoryResponse(BaseModel):
    id: UUID
    patient_id: UUID
    category: str
    title: Optional[str] = None
    description: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime


class HistoryListResponse(BaseModel):
    entries: List[HistoryResponse]
    total: int
