"""
Tests for POST /auth/register using a fake Supabase client (no network).
"""

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from gotrue.errors import AuthApiError

from app.api import auth

PATIENT_ROW = {
    "id": "11111111-1111-1111-1111-111111111111",
    "auth_user_id": "22222222-2222-2222-2222-222222222222",
    "date_of_birth": None,
    "sex": None,
    "created_at": "2026-10-09T00:00:00+00:00",
    "updated_at": "2026-10-09T00:00:00+00:00",
}


class FakeSupabase:
    """Records calls; behaviour is configured per test."""

    def __init__(self, sign_up_result=None, sign_up_error=None, insert_rows=None, insert_error=None):
        self.sign_up_result = sign_up_result
        self.sign_up_error = sign_up_error
        self.insert_rows = insert_rows
        self.insert_error = insert_error
        self.deleted_users = []
        self.inserted = []
        self.auth = SimpleNamespace(
            sign_up=self._sign_up,
            admin=SimpleNamespace(delete_user=self.deleted_users.append),
        )

    def _sign_up(self, credentials):
        if self.sign_up_error:
            raise self.sign_up_error
        return self.sign_up_result

    def table(self, name):
        fake = self

        class Query:
            def insert(self, payload):
                fake.inserted.append((name, payload))
                return self

            def execute(self):
                if fake.insert_error:
                    raise fake.insert_error
                return SimpleNamespace(data=fake.insert_rows)

        return Query()


def _user(identities):
    return SimpleNamespace(user=SimpleNamespace(id=PATIENT_ROW["auth_user_id"], identities=identities))


@pytest.fixture
def client_with(monkeypatch):
    def make(fake):
        monkeypatch.setattr(auth, "get_supabase", lambda: fake)
        app = FastAPI()
        app.include_router(auth.router)
        return TestClient(app)
    return make


BODY = {"email": "new@example.com", "password": "Password123!"}


def test_register_success(client_with):
    fake = FakeSupabase(sign_up_result=_user([{"id": "x"}]), insert_rows=[PATIENT_ROW])
    res = client_with(fake).post("/auth/register", json=BODY)
    assert res.status_code == 201
    assert res.json()["auth_user_id"] == PATIENT_ROW["auth_user_id"]
    assert fake.inserted == [("patients", {"auth_user_id": PATIENT_ROW["auth_user_id"]})]


def test_existing_email_with_confirmations_on_returns_409(client_with):
    # Supabase returns an obfuscated user with no identities instead of erroring
    fake = FakeSupabase(sign_up_result=_user([]))
    res = client_with(fake).post("/auth/register", json=BODY)
    assert res.status_code == 409
    assert fake.inserted == []


def test_existing_email_with_confirmations_off_returns_409(client_with):
    err = AuthApiError("User already registered", 422, "user_already_exists")
    res = client_with(FakeSupabase(sign_up_error=err)).post("/auth/register", json=BODY)
    assert res.status_code == 409


def test_other_auth_error_returns_400_with_message(client_with):
    err = AuthApiError("Password is too weak", 422, "weak_password")
    res = client_with(FakeSupabase(sign_up_error=err)).post("/auth/register", json=BODY)
    assert res.status_code == 400
    assert res.json()["detail"] == "Password is too weak"


@pytest.mark.parametrize("fake_kwargs", [
    {"insert_rows": []},
    {"insert_error": RuntimeError("db down")},
])
def test_profile_insert_failure_rolls_back_auth_user(client_with, fake_kwargs):
    fake = FakeSupabase(sign_up_result=_user([{"id": "x"}]), **fake_kwargs)
    res = client_with(fake).post("/auth/register", json=BODY)
    assert res.status_code == 500
    assert fake.deleted_users == [PATIENT_ROW["auth_user_id"]]


def test_short_password_rejected_before_calling_supabase(client_with):
    fake = FakeSupabase(sign_up_error=AssertionError("should not be called"))
    res = client_with(fake).post("/auth/register", json={"email": "a@example.com", "password": "short"})
    assert res.status_code == 422
