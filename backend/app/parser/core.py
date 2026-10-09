"""
Parser Core — public entry point for text parsing and normalization.

Re-exports parse_lab_text and normalize_and_score from their dedicated modules
so existing imports continue to work without change.
"""

from app.parser.parser import parse_lab_text  # noqa: F401
from app.parser.normalizer import normalize_and_score  # noqa: F401

__all__ = ["parse_lab_text", "normalize_and_score"]
