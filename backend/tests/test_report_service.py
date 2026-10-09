"""
Tests for report_service helpers and sex-aware fallback ranges.
"""

from types import SimpleNamespace

import pytest
from postgrest.exceptions import APIError

from app.parser.normalizer import normalize_and_score
from app.parser.reference_ranges import get_fallback_range
from app.services.report_service import _insert_lab_results


class TestSexSpecificRanges:

    @pytest.mark.parametrize("sex, expected", [
        ("male", (13.0, 17.0)),
        ("female", (12.0, 15.5)),
        (None, (12.0, 17.0)),                 # unknown: span covering both
        ("prefer_not_to_say", (12.0, 17.0)),
    ])
    def test_hemoglobin(self, sex, expected):
        assert get_fallback_range("hemoglobin", sex)[:2] == expected

    def test_non_sex_specific_unchanged(self):
        assert get_fallback_range("tsh", "female") == get_fallback_range("tsh")

    def test_same_value_scores_differently_by_sex(self):
        defs = [{"id": "hb", "canonical_name": "hemoglobin", "display_name": "Hemoglobin"}]

        def status(sex):
            parsed = {"test_name_raw": "Hemoglobin", "value": 12.5, "unit": "g/dL",
                      "extraction_confidence": 0.6}
            return normalize_and_score(parsed, defs, sex)["status"]

        assert status("male") == "LOW"
        assert status("female") == "NORMAL"
        assert status(None) == "NORMAL"


MISSING_COLUMN = APIError({
    "code": "PGRST204",
    "message": "Could not find the 'needs_review' column of 'lab_results' in the schema cache",
})


class FakeLabResults:
    """Stand-in for supabase.table('lab_results').insert(...).execute()."""

    def __init__(self, error_when_flag_present=None):
        self.error = error_when_flag_present
        self.attempts = []

    def table(self, name):
        store = self

        class Query:
            def insert(self, payload):
                self.payload = payload
                return self

            def execute(self):
                store.attempts.append(self.payload)
                if store.error and any("needs_review" in p for p in self.payload):
                    raise store.error
                return SimpleNamespace(data=self.payload)

        return Query()


class TestInsertLabResults:

    ROWS = [{"test_name_raw": "Hemoglobin", "needs_review": True}]

    def test_includes_needs_review_when_column_exists(self):
        fake = FakeLabResults()
        assert _insert_lab_results(fake, self.ROWS) == self.ROWS
        assert len(fake.attempts) == 1

    def test_retries_without_column_before_migration(self):
        fake = FakeLabResults(MISSING_COLUMN)
        assert _insert_lab_results(fake, self.ROWS) == [{"test_name_raw": "Hemoglobin"}]
        assert len(fake.attempts) == 2

    def test_other_errors_are_raised(self):
        fake = FakeLabResults(APIError({"code": "23503", "message": "foreign key violation"}))
        with pytest.raises(APIError):
            _insert_lab_results(fake, self.ROWS)

    def test_empty_payload_skips_insert(self):
        fake = FakeLabResults()
        assert _insert_lab_results(fake, []) == []
        assert fake.attempts == []
