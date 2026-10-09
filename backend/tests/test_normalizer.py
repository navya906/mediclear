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


class TestDefinitionMatching:
    """Matching against the definitions seeded by data/seed_test_definitions.py."""

    SEEDED_DEFS = [
        {"id": "hb",   "canonical_name": "hemoglobin",        "display_name": "Hemoglobin"},
        {"id": "wbc",  "canonical_name": "wbc",               "display_name": "White Blood Cell Count (WBC)"},
        {"id": "plt",  "canonical_name": "platelets",         "display_name": "Platelet Count"},
        {"id": "tc",   "canonical_name": "total_cholesterol", "display_name": "Total Cholesterol"},
        {"id": "ldl",  "canonical_name": "ldl_cholesterol",   "display_name": "LDL Cholesterol"},
        {"id": "hdl",  "canonical_name": "hdl_cholesterol",   "display_name": "HDL Cholesterol"},
        {"id": "tsh",  "canonical_name": "tsh",               "display_name": "TSH (Thyroid Stimulating Hormone)"},
        {"id": "ft3",  "canonical_name": "free_t3",           "display_name": "Free T3 (Triiodothyronine)"},
        {"id": "ft4",  "canonical_name": "free_t4",           "display_name": "Free T4 (Thyroxine)"},
    ]

    def _match(self, name):
        parsed = {"test_name_raw": name, "value": 50.0, "extraction_confidence": 0.9}
        return normalize_and_score(parsed, self.SEEDED_DEFS)["test_definition_id"]

    @pytest.mark.parametrize("name, expected", [
        ("HDL Cholesterol", "hdl"),
        ("Cholesterol HDL Direct", "hdl"),
        ("LDL Cholesterol", "ldl"),
        ("LDL", "ldl"),
        ("Total Cholesterol", "tc"),
        ("Cholesterol, Total", "tc"),
        ("Serum Cholesterol", "tc"),
        ("Free T4", "ft4"),
        ("Free T3", "ft3"),
        ("FT4", "ft4"),
        ("TSH", "tsh"),
        ("Thyroid Stimulating Hormone", "tsh"),
        ("WBC", "wbc"),
        ("Total Leucocyte Count", "wbc"),
        ("Hb", "hb"),
        ("Haemoglobin", "hb"),
        ("Platelet Count", "plt"),
    ])
    def test_matches_expected_definition(self, name, expected):
        assert self._match(name) == expected

    @pytest.mark.parametrize("name", [
        "Hemoglobin A1c",   # HbA1c is not plain hemoglobin
        "T3",               # total T3 is not free T3
        "Vitamin D",
    ])
    def test_does_not_force_a_wrong_match(self, name):
        assert self._match(name) is None

    def test_lipid_fallback_range_uses_seeded_canonical_name(self):
        parsed = {"test_name_raw": "HDL Cholesterol", "value": 30.0, "extraction_confidence": 0.6}
        result = normalize_and_score(parsed, self.SEEDED_DEFS)
        assert (result["reference_min"], result["reference_max"]) == (40.0, 60.0)
        assert result["status"] == "LOW"


class TestOneSidedAndUnits:

    @pytest.mark.parametrize("value, ref_min, ref_max, expected", [
        (180, None, 200, "NORMAL"),
        (212, None, 200, "HIGH"),
        (48, 40, None, "NORMAL"),
        (35, 40, None, "LOW"),
    ])
    def test_one_sided_status(self, value, ref_min, ref_max, expected):
        assert _compute_status(value, ref_min, ref_max) == expected

    DEFS = [{"id": "plt", "canonical_name": "platelets", "display_name": "Platelet Count"},
            {"id": "tc", "canonical_name": "total_cholesterol", "display_name": "Total Cholesterol"}]

    def test_one_sided_report_range_not_replaced_by_fallback(self):
        parsed = {"test_name_raw": "Total Cholesterol", "value": 212.0, "unit": "mg/dL",
                  "reference_min": None, "reference_max": 200.0, "reference_text": "< 200",
                  "extraction_confidence": 0.85}
        result = normalize_and_score(parsed, self.DEFS)
        assert (result["reference_min"], result["reference_max"]) == (None, 200.0)
        assert result["status"] == "HIGH"

    def test_fallback_skipped_when_units_differ(self):
        # 2,10,000 /cumm must not be compared against the 150-400 K/uL fallback
        parsed = {"test_name_raw": "Platelet Count", "value": 210000.0, "unit": "/cumm",
                  "extraction_confidence": 0.6}
        result = normalize_and_score(parsed, self.DEFS)
        assert result["status"] == "UNKNOWN"
        assert result["needs_review"] is True

    def test_fallback_used_for_equivalent_unit(self):
        parsed = {"test_name_raw": "Platelet Count", "value": 210.0, "unit": "10^3/µL",
                  "extraction_confidence": 0.6}
        result = normalize_and_score(parsed, self.DEFS)
        assert (result["reference_min"], result["reference_max"]) == (150.0, 400.0)
        assert result["status"] == "NORMAL"
