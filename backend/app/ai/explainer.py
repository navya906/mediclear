"""
AI Explainer — LLM call logic, separated from orchestration.

This module is responsible only for talking to the OpenAI-compatible API
and returning a parsed JSON dict. It knows nothing about DB persistence.
"""

import json
import os
import re
from typing import List, Optional

from openai import OpenAI

from app.ai.prompts import SYSTEM_PROMPT, PROMPT_VERSION

AI_API_KEY = os.environ.get("AI_API_KEY", "")
AI_BASE_URL = os.environ.get("AI_BASE_URL", "https://api.openai.com/v1")
AI_MODEL = os.environ.get("AI_MODEL", "gpt-3.5-turbo")

# Patterns that indicate a definitive diagnosis or a treatment instruction.
# Kept specific so ordinary phrasing ("if you have questions...") still passes.
_CONDITION_WORDS = (
    r"(?:disease|disorder|syndrome|cancer|tumou?r|diabetes|an(?:a)?emia|infection|"
    r"deficiency|failure|hypo\w+|hyper\w+|condition)"
)
_UNSAFE_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        # "you have diabetes", "you probably have an infection"
        rf"\byou (?:\w+ )?(?:have|are suffering from|suffer from) (?:a |an )?(?:\w+ ){{0,2}}{_CONDITION_WORDS}\b",
        r"\b(?:you are|you're|you've been) diagnosed\b",
        r"\bdiagnos(?:ed|is) (?:with|of)\b",
        r"\bthis (?:means|confirms|shows) (?:that )?you have\b",
        # "you should take iron", "you need to stop your medication"
        r"\byou (?:should|must|need to) (?:take|start|stop|increase|decrease|reduce) \w+",
        r"\btake this medication\b",
        r"\b(?:the )?treatment (?:is|should be)\b",
        r"\b(?:cure|cures|cured)\b",
    )
]

_SAFE_FALLBACK_TEXT = "This result is worth discussing with your doctor."

_client: Optional[OpenAI] = None


def get_client() -> Optional[OpenAI]:
    """Return the OpenAI client, or None if no API key is configured."""
    global _client
    if _client is None and AI_API_KEY:
        _client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client


def is_unsafe(text: str) -> bool:
    """True if the text makes a diagnostic claim or gives treatment instructions."""
    return any(p.search(text) for p in _UNSAFE_PATTERNS)


def _sanitise(text) -> str:
    """Return the text, or a safe fallback if it contains unsafe phrasing."""
    if not isinstance(text, str):
        return ""
    return _SAFE_FALLBACK_TEXT if is_unsafe(text) else text


def _sanitise_list(items) -> List[str]:
    """Drop unsafe or non-string items; a lone string is treated as one item."""
    if isinstance(items, str):
        items = [items]
    if not isinstance(items, list):
        return []
    return [i for i in items if isinstance(i, str) and i.strip() and not is_unsafe(i)]


def call_llm(user_prompt: str) -> dict:
    """
    Call the LLM with the given user prompt and system prompt.
    Returns a parsed dict with keys: simple_explanation, why_it_matters,
    possible_reasons, doctor_questions.
    Raises RuntimeError if the API is unavailable.
    """
    client = get_client()
    if client is None:
        raise RuntimeError("AI_API_KEY is not configured.")

    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    content = response.choices[0].message.content
    parsed = json.loads(content)

    # Sanitise every field the patient will see
    return {
        "simple_explanation": _sanitise(parsed.get("simple_explanation", "")),
        "why_it_matters":     _sanitise(parsed.get("why_it_matters", "")),
        "possible_reasons":   _sanitise_list(parsed.get("possible_reasons", [])),
        "doctor_questions":   _sanitise_list(parsed.get("doctor_questions", [])),
    }


def get_prompt_version() -> str:
    return PROMPT_VERSION
