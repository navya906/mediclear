"""
Auth router.

POST /auth/register
  - Sign up a new user via Supabase Auth Admin API (service key)
    which correctly hashes the password for signInWithPassword and
    auto-confirms the email so no verification email is needed.
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

    # 1. Create the auth.users record via the Admin API.
    #    admin.create_user() uses the service key but correctly hashes the
    #    password so that the frontend's signInWithPassword call succeeds.
    #    email_confirm=True skips the email verification step.
    try:
        auth_response = supabase.auth.admin.create_user({
            "email": body.email,
            "password": body.password,
            "email_confirm": True,
        })
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

    # 2. Insert the patients row (service key bypasses RLS)
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
