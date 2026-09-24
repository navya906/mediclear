"""
AI Prompts — versioned prompt templates for lab result explanations.

Keeping prompts in a dedicated module makes it easy to A/B test prompt
wording without touching the calling code.
"""

PROMPT_VERSION = "v2"

SYSTEM_PROMPT = (
    "You are a friendly, empathetic medical explainer for patients. "
    "Your job is to translate lab results into plain, accessible English. "
    "You MUST NOT diagnose conditions, prescribe treatments, or make definitive "
    "statements like 'you have X disease'. Always encourage the patient to "
    "discuss results with their doctor."
)

RESULT_EXPLANATION_TEMPLATE = """\
Explain the following lab result to a patient in plain, empathetic English.

Test: {display_name}
Description: {description}
Result: {value} {unit}
Status: {status}
Reference Range: {reference_text}

{history_context}

Return ONLY a valid JSON object with these exact keys:
{{
  "simple_explanation": "1-2 sentences explaining what the result means in everyday terms",
  "why_it_matters": "Why this test is important for health",
  "possible_reasons": ["Possible reason 1", "Possible reason 2"],
  "doctor_questions": ["A useful question to ask your doctor about this result"]
}}
"""


def build_explanation_prompt(
    result_data: dict,
    test_def: dict,
    patient_history: list,
) -> str:
    """
    Build the user-facing prompt string for a single lab result explanation.
    """
    history_context = ""
    if patient_history:
        lines = []
        for h in patient_history:
            category = h.get("category", "").title()
            title = h.get("title", "")
            desc = h.get("description", "")
            lines.append(f"- {category}: {title} ({desc})")
        history_context = "Patient Medical History:\n" + "\n".join(lines)

    return RESULT_EXPLANATION_TEMPLATE.format(
        display_name=test_def.get("display_name") or result_data.get("test_name_raw", "Unknown"),
        description=test_def.get("description") or "No description available.",
        value=result_data.get("value", "N/A"),
        unit=result_data.get("unit", ""),
        status=result_data.get("status", "UNKNOWN"),
        reference_text=result_data.get("reference_text") or "Not available",
        history_context=history_context,
    )
