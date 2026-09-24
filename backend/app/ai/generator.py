"""
AI Generator — orchestrates explanation generation.

Calls app.ai.prompts to build the prompt and app.ai.explainer to call the LLM.
Handles the fallback case (no API key) and returns an ExplanationCreate schema.
"""

from app.ai.explainer import call_llm, get_client, get_prompt_version
from app.ai.prompts import build_explanation_prompt
from app.schemas.explanation import ExplanationCreate


def generate_explanation(
    result_data: dict,
    test_def: dict,
    patient_history: list,
) -> ExplanationCreate:
    """
    Generate a plain-English explanation for a single lab result.
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
            model="fallback",
            prompt_version="none",
        )

    # ── Build prompt and call LLM ──────────────────────────────────────────
    prompt = build_explanation_prompt(result_data, test_def, patient_history)

    try:
        parsed = call_llm(prompt)
        return ExplanationCreate(
            lab_result_id=result_data["id"],
            simple_explanation=parsed.get("simple_explanation", ""),
            why_it_matters=parsed.get("why_it_matters", ""),
            possible_reasons=parsed.get("possible_reasons", []),
            doctor_questions=parsed.get("doctor_questions", []),
            model=str(get_client().models) if get_client() else "unknown",
            prompt_version=get_prompt_version(),
        )
    except Exception:
        return ExplanationCreate(
            lab_result_id=result_data["id"],
            simple_explanation=(
                "We couldn't generate a clear explanation. "
                "Please discuss this result with your doctor."
            ),
            model="error",
            prompt_version=get_prompt_version(),
        )
