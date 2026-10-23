"""
AI Prompts — versioned prompt templates for lab result explanations.

Keeping prompts in a dedicated module makes it easy to A/B test prompt
wording without touching the calling code.
"""

import hashlib
import json
from datetime import date
from typing import List, Optional

PROMPT_VERSION = "v4"

# How many earlier results for the same test are shown to the model
MAX_PREVIOUS_RESULTS = 3

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
{previous_context}

Return ONLY a valid JSON object with these exact keys:
{{
  "simple_explanation": "1-2 sentences explaining what the result means in everyday terms. If earlier results are listed, say whether the value has gone up, gone down or stayed about the same",
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


def build_previous_results_context(previous_results: Optional[List[dict]]) -> str:
    """Earlier results for the same test, oldest first, or "" if there are none."""
    if not previous_results:
        return ""
    lines = []
    for r in previous_results[-MAX_PREVIOUS_RESULTS:]:
        unit = f" {r['unit']}" if r.get("unit") else ""
        status = f" ({r['status']})" if r.get("status") else ""
        lines.append(f"- {r.get('date') or 'Unknown date'}: {r.get('value')}{unit}{status}")
    return "Earlier results for this test (oldest first):\n" + "\n".join(lines)


def context_fingerprint(
    patient: Optional[dict],
    patient_history: Optional[list],
    previous_results: Optional[List[dict]] = None,
) -> str:
    """
    Short hash of everything about the patient that goes into the prompt.
    Stored with each explanation so it can be regenerated when the patient's
    age, sex, medical history or earlier results change.
    """
    patient = patient or {}
    history = sorted(
        (h.get("category") or "", h.get("title") or "", h.get("description") or "")
        for h in (patient_history or [])
    )
    previous = [
        (r.get("date"), r.get("value"), r.get("unit"), r.get("status"))
        for r in (previous_results or [])[-MAX_PREVIOUS_RESULTS:]
    ]
    payload = json.dumps(
        [_age_in_years(patient.get("date_of_birth")), patient.get("sex"), history, previous],
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def build_explanation_prompt(
    result_data: dict,
    test_def: dict,
    patient_history: list,
    patient: Optional[dict] = None,
    previous_results: Optional[List[dict]] = None,
) -> str:
    """
    Build the user-facing prompt string for a single lab result explanation.
    `patient` is the patients row (date_of_birth, sex), used for context.
    `previous_results` are earlier results for the same test, oldest first.
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
        previous_context=build_previous_results_context(previous_results),
    )
