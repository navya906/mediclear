"""Pydantic schemas for the explanations table."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class ExplanationCreate(BaseModel):
    lab_result_id: UUID
    language: str = "en"
    simple_explanation: str
    why_it_matters: Optional[str] = None
    possible_reasons: List[str] = []
    doctor_questions: List[str] = []
    model: Optional[str] = None
    prompt_version: Optional[str] = None


class ExplanationResponse(ExplanationCreate):
    id: UUID
    created_at: datetime
