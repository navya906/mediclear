"""Pydantic schemas for the reports table."""

from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel

PROCESSING_STATUS = Literal["uploaded", "processing", "completed", "failed", "needs_review"]


class ReportResponse(BaseModel):
    id: UUID
    patient_id: UUID
    file_name: str
    file_type: str
    storage_path: str
    report_date: Optional[date] = None
    processing_status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
