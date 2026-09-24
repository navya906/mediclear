"""
AI Explainer — LLM call logic, separated from orchestration.

This module is responsible only for talking to the OpenAI-compatible API
and returning a parsed JSON dict. It knows nothing about DB persistence.
"""

import json
import os
from typing import Optional

from openai import OpenAI

from app.ai.prompts import SYSTEM_PROMPT, PROMPT_VERSION

AI_API_KEY = os.environ.get("AI_API_KEY", "")
AI_BASE_URL = os.environ.get("AI_BASE_URL", "https://api.openai.com/v1")
AI_MODEL = os.environ.get("AI_MODEL", "gpt-3.5-turbo")

# Phrases that indicate a definitive diagnostic claim — strip if found
_UNSAFE_PHRASES = [
    "you have",
    "you are diagnosed",
    "diagnosed with",
    "take this medication",
    "you should take",
    "cure",
    "treatment is",
]

_client: Optional[OpenAI] = None


def get_client() -> Optional[OpenAI]:
    """Return the OpenAI client, or None if no API key is configured."""
    global _client
    if _client is None and AI_API_KEY:
        _client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL)
    return _client


def _sanitise(text: str) -> str:
    """Replace any unsafe diagnostic phrasing with a safe fallback."""
    lower = text.lower()
    for phrase in _UNSAFE_PHRASES:
        if phrase in lower:
            return "This result is worth discussing with your doctor."
    return text


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

    # Sanitise output
    if "simple_explanation" in parsed:
        parsed["simple_explanation"] = _sanitise(parsed["simple_explanation"])

    return parsed


def get_prompt_version() -> str:
    return PROMPT_VERSION
