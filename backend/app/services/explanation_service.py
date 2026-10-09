"""
Explanation Service — fetch-or-generate logic for lab result explanations.

Shared by the POST /results/{id}/explain endpoint and the background
report pipeline so both reuse good explanations and replace placeholders.
"""

import uuid
from typing import Optional

from app.ai.generator import generate_explanation, should_regenerate
from app.database.client import fetch_one


def get_or_create_explanation(
    supabase,
    result_row: dict,
    test_def: dict,
    patient_history: list,
    patient: Optional[dict] = None,
) -> Optional[dict]:
    """
    Return the stored explanation for a lab result, generating one if none
    exists or the stored one is a placeholder (LLM error / no-key fallback).
    Returns the saved explanations row, or None if saving failed.
    """
    existing = fetch_one(
        supabase.table("explanations").select("*").eq("lab_result_id", str(result_row["id"]))
    )
    if existing and not should_regenerate(existing):
        return existing

    explanation = generate_explanation(result_row, test_def, patient_history, patient)
    # mode="json" turns the UUID into a string so the request body can be encoded
    payload = explanation.model_dump(mode="json")

    if existing:
        saved = supabase.table("explanations").update(payload).eq("id", existing["id"]).execute()
    else:
        payload["id"] = str(uuid.uuid4())
        saved = supabase.table("explanations").insert(payload).execute()

    return saved.data[0] if saved.data else None
