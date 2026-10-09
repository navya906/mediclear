"""
AI Prompts — versioned prompt templates for lab result explanations.

Keeping prompts in a dedicated module makes it easy to A/B test prompt
wording without touching the calling code.
"""

from datetime import date
from typing import Optional

PROMPT_VERSION = "v3"

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

{patient_context}
{history_context}

Return ONLY a valid JSON object with these exact keys:
{{
  "simple_explanation": "1-2 sentences explaining what the result means in everyday terms",
  "why_it_matters": "Why this test is important for health",
  "possible_reasons": ["Possible reason 1", "Possible reason 2"],
  "doctor_questions": ["A useful question to ask your doctor about this result"]
}}
"""


def _age_in_years(date_of_birth, today: Optional[date] = None) -> Optional[int]:
    if not date_of_birth:
        return None
    if isinstance(date_of_birth, str):
        try:
            date_of_birth = date.fromisoformat(date_of_birth[:10])
        except ValueError:
            return None
    today = today or date.today()
    had_birthday = (today.month, today.day) >= (date_of_birth.month, date_of_birth.day)
    return today.year - date_of_birth.year - (0 if had_birthday else 1)


def build_patient_context(patient: Optional[dict]) -> str:
    """One line describing the patient's age and sex, or "" if neither is known."""
    if not patient:
        return ""
    parts = []
    age = _age_in_years(patient.get("date_of_birth"))
    if age is not None:
        parts.append(f"Age: {age}")
    if patient.get("sex") in ("male", "female"):
        parts.append(f"Sex: {patient['sex']}")
    return "Patient: " + ", ".join(parts) if parts else ""


def build_explanation_prompt(
    result_data: dict,
    test_def: dict,
    patient_history: list,
    patient: Optional[dict] = None,
) -> str:
    """
    Build the user-facing prompt string for a single lab result explanation.
    `patient` is the patients row (date_of_birth, sex), used for context.
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
        patient_context=build_patient_context(patient),
        history_context=history_context,
    )
