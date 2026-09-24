"""
Unit tests for app.parser.normalizer — status computation and test definition matching.
"""

import pytest
from app.parser.normalizer import normalize_and_score, _compute_status


class TestComputeStatus:

    def test_normal(self):
        assert _compute_status(14.2, 13.0, 17.0) == "NORMAL"

    def test_low(self):
        assert _compute_status(10.0, 13.0, 17.0) == "LOW"

    def test_high(self):
        assert _compute_status(20.0, 13.0, 17.0) == "HIGH"

    def test_critical_low(self):
        # 4.0 is (13.0 - 4.0) = 9 below min; range = 4; 1.5*range = 6 → critical
        assert _compute_status(4.0, 13.0, 17.0) == "CRITICAL"

    def test_critical_high(self):
        # 25.0 is 8 above max; range = 4; 1.5*range = 6 → critical
        assert _compute_status(25.0, 13.0, 17.0) == "CRITICAL"

    def test_unknown_when_no_range(self):
        assert _compute_status(14.2, None, None) == "UNKNOWN"


class TestNormalizeAndScore:

    FAKE_TEST_DEFS = [
        {"id": "td-1", "canonical_name": "hemoglobin", "display_name": "Hemoglobin"},
        {"id": "td-2", "canonical_name": "tsh",        "display_name": "TSH"},
    ]

    def _make_parsed(self, name, value, ref_min=None, ref_max=None, confidence=0.9):
        return {
            "test_name_raw": name,
            "value": value,
            "unit": "g/dL",
            "reference_min": ref_min,
            "reference_max": ref_max,
            "reference_text": f"{ref_min} - {ref_max}" if ref_min else None,
            "extraction_confidence": confidence,
        }

    def test_exact_match_and_normal(self):
        parsed = self._make_parsed("Hemoglobin", 14.2, 13.0, 17.0)
        result = normalize_and_score(parsed, self.FAKE_TEST_DEFS)
        assert result["test_definition_id"] == "td-1"
        assert result["status"] == "NORMAL"
        assert result["needs_review"] is False

    def test_token_match(self):
        parsed = self._make_parsed("Serum Hemoglobin Level", 14.2, 13.0, 17.0)
        result = normalize_and_score(parsed, self.FAKE_TEST_DEFS)
        assert result["test_definition_id"] == "td-1"

    def test_unmatched_definition(self):
        parsed = self._make_parsed("SomeUnknownTest", 5.0, 1.0, 10.0)
        result = normalize_and_score(parsed, self.FAKE_TEST_DEFS)
        assert result["test_definition_id"] is None

    def test_needs_review_low_confidence(self):
        parsed = self._make_parsed("Hemoglobin", 14.2, 13.0, 17.0, confidence=0.5)
        result = normalize_and_score(parsed, self.FAKE_TEST_DEFS)
        assert result["needs_review"] is True

    def test_fallback_range_applied(self):
        """When ref range is missing, fallback ranges should fill it in."""
        parsed = self._make_parsed("Hemoglobin", 14.2, None, None, confidence=0.6)
        result = normalize_and_score(parsed, self.FAKE_TEST_DEFS)
        # Fallback ranges exist for hemoglobin, so status should not be UNKNOWN
        assert result["status"] != "UNKNOWN"
