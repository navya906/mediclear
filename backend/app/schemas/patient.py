"""Pydantic schemas for the patients table."""

from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class PatientUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    sex: Optional[Literal["male", "female", "other", "prefer_not_to_say"]] = None


class PatientResponse(BaseModel):
    id: UUID
    auth_user_id: UUID
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    created_at: datetime
    updated_at: datetime
