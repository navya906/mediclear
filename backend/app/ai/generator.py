"""
AI Generator — orchestrates explanation generation.

Calls app.ai.prompts to build the prompt and app.ai.explainer to call the LLM.
Handles the fallback case (no API key) and returns an ExplanationCreate schema.
"""

import logging
from typing import Optional

from app.ai.explainer import AI_MODEL, call_llm, get_client, get_prompt_version
from app.ai.prompts import build_explanation_prompt
from app.schemas.explanation import ExplanationCreate

logger = logging.getLogger(__name__)

# `model` values for explanations that were not produced by the LLM
MODEL_FALLBACK = "fallback"
MODEL_ERROR = "error"


def should_regenerate(existing: Optional[dict]) -> bool:
    """
    True if a stored explanation is a placeholder worth replacing:
    an LLM failure, or the no-API-key fallback now that a key is configured.
    """
    if not existing:
        return False
    model = existing.get("model")
    return model == MODEL_ERROR or (model == MODEL_FALLBACK and get_client() is not None)


def generate_explanation(
    result_data: dict,
    test_def: dict,
    patient_history: list,
    patient: Optional[dict] = None,
) -> ExplanationCreate:
    """
    Generate a plain-English explanation for a single lab result.
    `patient` is the patients row; its age and sex are given to the model.
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
    prompt = build_explanation_prompt(result_data, test_def, patient_history, patient)

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
            prompt_version=get_prompt_version(),
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
            prompt_version=get_prompt_version(),
        )
