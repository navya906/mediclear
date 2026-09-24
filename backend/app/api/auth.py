"""
Auth router.

POST /auth/register
  - Sign up a new user via Supabase Auth
  - Insert a corresponding row in the patients table
  - Return the new patient profile
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.database.client import get_supabase
from app.schemas.patient import PatientResponse

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


@router.post(
    "/register",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient account",
)
def register(body: RegisterRequest):
    supabase = get_supabase()

    # 1. Create the auth.users record via Supabase Auth
    try:
        auth_response = supabase.auth.sign_up(
            {"email": body.email, "password": body.password}
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {exc}",
        )

    if auth_response.user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup failed. The email may already be registered.",
        )

    auth_user_id = str(auth_response.user.id)

    # 2. Insert the patients row
    try:
        result = (
            supabase.table("patients")
            .insert({"auth_user_id": auth_user_id})
            .execute()
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create patient profile: {exc}",
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create patient profile.",
        )

    return PatientResponse(**result.data[0])
