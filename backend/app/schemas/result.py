"""Pydantic schemas for the lab_results table."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TestDefinition(BaseModel):
    id: UUID
    canonical_name: str
    display_name: str
    category: str
    default_unit: Optional[str] = None
    description: Optional[str] = None


class LabResultResponse(BaseModel):
    id: UUID
    report_id: UUID
    test_definition_id: Optional[UUID] = None
    test_name_raw: str
    value: Optional[float] = None
    unit: Optional[str] = None
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    reference_text: Optional[str] = None
    status: str
    extraction_confidence: Optional[float] = None
    created_at: datetime

    # The joined test definition (if available)
    test_definition: Optional[TestDefinition] = None
