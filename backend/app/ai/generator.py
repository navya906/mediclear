"""
AI Generator — orchestrates explanation generation.

Calls app.ai.prompts to build the prompt and app.ai.explainer to call the LLM.
Handles the fallback case (no API key) and returns an ExplanationCreate schema.
"""

import logging
from typing import List, Optional

from app.ai.explainer import AI_MODEL, call_llm, get_client, get_prompt_version
from app.ai.prompts import build_explanation_prompt, context_fingerprint
from app.schemas.explanation import ExplanationCreate

logger = logging.getLogger(__name__)

# `model` values for explanations that were not produced by the LLM
MODEL_FALLBACK = "fallback"
MODEL_ERROR = "error"


def expected_prompt_version(
    patient_history: Optional[list],
    patient: Optional[dict] = None,
    previous_results: Optional[List[dict]] = None,
) -> str:
    """
    Prompt version plus a fingerprint of the patient context, e.g. "v4+3f9a0c1b2d4e".
    An explanation saved with a different value was written for older patient data.
    """
    return f"{get_prompt_version()}+{context_fingerprint(patient, patient_history, previous_results)}"


def should_regenerate(existing: Optional[dict], expected_version: Optional[str] = None) -> bool:
    """
    True if a stored explanation is worth replacing:
      - an LLM failure placeholder,
      - the no-API-key fallback, now that a key is configured, or
      - (when expected_version is given) an explanation written for a different
        prompt or older patient context: age, sex, history or earlier results.
    """
    if not existing:
        return False
    model = existing.get("model")
    if model == MODEL_ERROR:
        return True
    if model == MODEL_FALLBACK:
        return get_client() is not None
    return expected_version is not None and existing.get("prompt_version") != expected_version


def generate_explanation(
    result_data: dict,
    test_def: dict,
    patient_history: list,
    patient: Optional[dict] = None,
    previous_results: Optional[List[dict]] = None,
) -> ExplanationCreate:
    """
    Generate a plain-English explanation for a single lab result.
    `patient` is the patients row; its age and sex are given to the model.
    `previous_results` are earlier results for the same test, oldest first.
    Falls back gracefully when no AI API key is configured.
    """
    # ── Fallback: no API configured ────────────────────────────────────────
    if get_client() is None:
        return ExplanationCreate(
            lab_result_id=result_data["id"],
            simple_explanation=(
                "AI explanations are not configured. This test measures "
                + (test_def.get("display_name") or "a biomarker")
                + "."
            ),
            why_it_matters=test_def.get("description"),
            model=MODEL_FALLBACK,
            prompt_version="none",
        )

    # ── Build prompt and call LLM ──────────────────────────────────────────
    prompt = build_explanation_prompt(result_data, test_def, patient_history, patient, previous_results)
    version = expected_prompt_version(patient_history, patient, previous_results)

    try:
        parsed = call_llm(prompt)
        if not parsed["simple_explanation"].strip():
            raise ValueError("LLM response had no simple_explanation")
        return ExplanationCreate(
            lab_result_id=result_data["id"],
            simple_explanation=parsed["simple_explanation"],
            why_it_matters=parsed["why_it_matters"],
            possible_reasons=parsed["possible_reasons"],
            doctor_questions=parsed["doctor_questions"],
            model=AI_MODEL,
            prompt_version=version,
        )
    except Exception:
        logger.exception("LLM explanation failed for result %s", result_data.get("id"))
        return ExplanationCreate(
            lab_result_id=result_data["id"],
            simple_explanation=(
                "We couldn't generate a clear explanation. "
                "Please discuss this result with your doctor."
            ),
            model=MODEL_ERROR,
            prompt_version=version,
        )
