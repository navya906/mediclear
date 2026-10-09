"""
Auth router.

POST /auth/register
  - Sign up a new user via Supabase Auth sign_up, which sends the
    confirmation email (when confirmations are enabled in Supabase)
  - Insert a corresponding row in the patients table
  - If the patients insert fails, delete the auth user so the account
    can be registered again instead of being left without a profile
  - Return the new patient profile
"""

import logging

from fastapi import APIRouter, HTTPException, status
from gotrue.errors import AuthApiError
from pydantic import BaseModel, EmailStr, Field

from app.database.client import get_supabase
from app.schemas.patient import PatientResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

MIN_PASSWORD_LENGTH = 8

_EMAIL_TAKEN_DETAIL = "An account with this email already exists. Try signing in instead."


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH)


def _delete_auth_user(auth_user_id: str) -> None:
    """Best-effort rollback of a just-created auth user (needs the service key)."""
    try:
        get_supabase().auth.admin.delete_user(auth_user_id)
    except Exception:
        logger.exception("Could not roll back auth user %s; it has no patients row", auth_user_id)


@router.post(
    "/register",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient account",
)
def register(body: RegisterRequest):
    # 1. Create the auth.users record using the regular sign_up method.
    #    This ensures Supabase correctly dispatches the confirmation email.
    #    Use a dedicated client: if sign_up returns a session, supabase-py
    #    switches that client's DB calls to the new user's token.
    try:
        auth_response = get_supabase().auth.sign_up({
            "email": body.email,
            "password": body.password,
        })
    except AuthApiError as exc:
        # Raised when email confirmations are disabled and the email exists
        if exc.code == "user_already_exists" or "already registered" in exc.message.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_EMAIL_TAKEN_DETAIL)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message)
    except Exception:
        logger.exception("Supabase sign_up failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach the authentication service. Please try again.",
        )

    user = auth_response.user
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup failed. Please try again.",
        )

    # When email confirmations are enabled, Supabase does not error on an
    # existing email; it returns an obfuscated user with no identities.
    if user.identities is not None and len(user.identities) == 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=_EMAIL_TAKEN_DETAIL)

    auth_user_id = str(user.id)

    # 2. Insert the patients row (service key bypasses RLS)
    try:
        result = (
            get_supabase().table("patients")
            .insert({"auth_user_id": auth_user_id})
            .execute()
        )
    except Exception:
        logger.exception("Failed to create patients row for auth user %s", auth_user_id)
        result = None

    if result is None or not result.data:
        _delete_auth_user(auth_user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create patient profile. Please try registering again.",
        )

    return PatientResponse(**result.data[0])
