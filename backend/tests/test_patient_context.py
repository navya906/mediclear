"""
Tests that patient data reaches the AI and the dashboard trends:
  - earlier results for the same test are put in the prompt
  - explanations are regenerated when age, sex, history or earlier results change
  - the extra seeded test definitions match common lab-report spellings
  - the trends endpoints return what the dashboard needs with little data
"""

import importlib.util
import os
import uuid
from types import SimpleNamespace

import pytest

from app.ai import generator, prompts
from app.api import patients as patients_api
from app.parser.normalizer import match_definition
from app.services import explanation_service

PATIENT = {"id": "p1", "sex": "female", "date_of_birth": "1990-05-01"}
HISTORY = [{"category": "condition", "title": "Hypothyroidism", "description": "Since 2020"}]
EARLIER = [
    {"date": "2026-01-10", "value": 5.8, "unit": "mIU/L", "status": "HIGH"},
    {"date": "2026-04-02", "value": 4.9, "unit": "mIU/L", "status": "HIGH"},
]


# ── Prompt content ────────────────────────────────────────────────────────────

class TestPrompt:

    def test_profile_history_and_earlier_results_are_all_in_prompt(self):
        prompt = prompts.build_explanation_prompt(
            {"value": 4.1, "unit": "mIU/L", "status": "HIGH"},
            {"display_name": "TSH"},
            HISTORY,
            PATIENT,
            EARLIER,
        )
        assert "Sex: female" in prompt
        assert "Age:" in prompt
        assert "Condition: Hypothyroidism (Since 2020)" in prompt
        assert "Earlier results for this test (oldest first):" in prompt
        assert "- 2026-01-10: 5.8 mIU/L (HIGH)" in prompt
        assert "- 2026-04-02: 4.9 mIU/L (HIGH)" in prompt

    def test_no_earlier_results_section_when_none(self):
        prompt = prompts.build_explanation_prompt({"value": 4.1}, {}, [], None, [])
        assert "Earlier results" not in prompt

    def test_only_the_most_recent_earlier_results_are_used(self):
        many = [{"date": f"2025-0{i}-01", "value": i} for i in range(1, 7)]
        context = prompts.build_previous_results_context(many)
        assert context.count("\n- ") == prompts.MAX_PREVIOUS_RESULTS
        assert "2025-06-01" in context and "2025-01-01" not in context


# ── Regenerating explanations when patient data changes ──────────────────────

class TestFingerprint:

    def test_stable_for_same_context(self):
        a = prompts.context_fingerprint(PATIENT, HISTORY, EARLIER)
        b = prompts.context_fingerprint(dict(PATIENT), list(reversed(HISTORY)), list(EARLIER))
        assert a == b

    @pytest.mark.parametrize("patient, history, earlier", [
        ({**PATIENT, "sex": "male"}, HISTORY, EARLIER),
        ({**PATIENT, "date_of_birth": "1970-05-01"}, HISTORY, EARLIER),
        (PATIENT, HISTORY + [{"category": "medication", "title": "Levothyroxine"}], EARLIER),
        (PATIENT, [], EARLIER),
        (PATIENT, HISTORY, EARLIER[:1]),
    ])
    def test_changes_when_patient_data_changes(self, patient, history, earlier):
        assert prompts.context_fingerprint(patient, history, earlier) != \
            prompts.context_fingerprint(PATIENT, HISTORY, EARLIER)

    def test_good_explanation_for_old_context_is_regenerated(self):
        old_version = generator.expected_prompt_version([], PATIENT, [])
        new_version = generator.expected_prompt_version(HISTORY, PATIENT, [])
        existing = {"model": "gpt-4o-mini", "prompt_version": old_version}
        assert generator.should_regenerate(existing, old_version) is False
        assert generator.should_regenerate(existing, new_version) is True

    def test_legacy_explanation_without_fingerprint_is_regenerated(self):
        existing = {"model": "gpt-4o-mini", "prompt_version": "v3"}
        assert generator.should_regenerate(existing, generator.expected_prompt_version([], None)) is True

    def test_fallback_without_key_is_not_regenerated_for_context(self, monkeypatch):
        monkeypatch.setattr(generator, "get_client", lambda: None)
        existing = {"model": generator.MODEL_FALLBACK, "prompt_version": "none"}
        assert generator.should_regenerate(existing, "v4+abc") is False


class FakeExplanations:
    def __init__(self, existing):
        self.rows, self.updated = [existing], []

    def table(self, name):
        store = self

        class Query:
            op = "select"

            def select(self, *_):
                return self

            def eq(self, *_):
                return self

            def limit(self, *_):
                return self

            def update(self, payload):
                self.op, self.payload = "update", payload
                return self

            def execute(self):
                if self.op == "update":
                    store.updated.append(self.payload)
                    return SimpleNamespace(data=[{**store.rows[0], **self.payload}])
                return SimpleNamespace(data=store.rows)

        return Query()


def test_service_refreshes_explanation_after_history_is_added(monkeypatch):
    monkeypatch.setattr(generator, "get_client", lambda: object())
    seen_prompts = []

    def fake_llm(prompt):
        seen_prompts.append(prompt)
        return {"simple_explanation": "Updated", "why_it_matters": "", "possible_reasons": [], "doctor_questions": []}

    monkeypatch.setattr(generator, "call_llm", fake_llm)
    stale = {"id": "e1", "model": "gpt-4o-mini", "simple_explanation": "Old",
             "prompt_version": generator.expected_prompt_version([], PATIENT, [])}
    fake = FakeExplanations(stale)
    result = {"id": str(uuid.uuid4()), "value": 4.1, "status": "HIGH"}

    saved = explanation_service.get_or_create_explanation(fake, result, {}, HISTORY, PATIENT, EARLIER)

    assert saved["simple_explanation"] == "Updated"
    assert saved["prompt_version"] == generator.expected_prompt_version(HISTORY, PATIENT, EARLIER)
    assert "Hypothyroidism" in seen_prompts[0] and "2026-04-02" in seen_prompts[0]


# ── Picking earlier results ───────────────────────────────────────────────────

def _row(rid, test, value, created, report_date=None):
    return {"id": rid, "test_definition_id": test, "value": value, "unit": "g/dL", "status": "NORMAL",
            "reports": {"created_at": created, "report_date": report_date}}


class TestPreviousResultsFor:

    ROWS = [
        _row("a", "hb", 11.0, "2026-01-01T10:00:00+00:00"),
        _row("b", "hb", 11.5, "2026-03-01T10:00:00+00:00"),
        _row("c", "hb", 12.0, "2026-06-01T10:00:00+00:00"),   # the current result
        _row("d", "hb", 12.5, "2026-09-01T10:00:00+00:00"),   # a later report
        _row("e", "tsh", 3.0, "2026-02-01T10:00:00+00:00"),   # a different test
        _row("f", "hb", None, "2026-02-01T10:00:00+00:00"),   # no numeric value
    ]

    def test_only_earlier_results_for_same_test_oldest_first(self):
        current = self.ROWS[2]
        out = explanation_service.previous_results_for(self.ROWS, current, current["reports"]["created_at"])
        assert [r["value"] for r in out] == [11.0, 11.5]
        assert out[0]["date"] == "2026-01-01"

    def test_printed_report_date_wins_over_upload_date(self):
        rows = [_row("x", "hb", 10.0, "2026-10-01T00:00:00+00:00", report_date="2025-12-01")]
        out = explanation_service.previous_results_for(rows, {"id": "y", "test_definition_id": "hb"},
                                                        "2026-06-01T00:00:00+00:00")
        assert [r["value"] for r in out] == [10.0]

    def test_unmatched_result_has_no_history(self):
        assert explanation_service.previous_results_for(self.ROWS, {"id": "z"}, None) == []


# ── Seeded definitions match common report spellings ─────────────────────────

def _seed_definitions():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "seed_test_definitions.py")
    spec = importlib.util.spec_from_file_location("seed_test_definitions", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [{**d, "id": d["canonical_name"]} for d in module.TEST_DEFINITIONS]


SEEDED = _seed_definitions()


def test_every_fallback_range_has_a_definition():
    from app.parser.reference_ranges import FALLBACK_RANGES, SEX_SPECIFIC_RANGES
    seeded = {d["canonical_name"] for d in SEEDED}
    assert set(FALLBACK_RANGES) | set(SEX_SPECIFIC_RANGES) <= seeded


@pytest.mark.parametrize("raw, expected", [
    ("SGPT", "alt"), ("ALT (SGPT)", "alt"), ("SGOT", "ast"), ("Alkaline Phosphatase", "alp"),
    ("Bilirubin Total", "bilirubin_total"), ("Bilirubin Direct", "bilirubin_direct"),
    ("Bilirubin Indirect", None),
    ("Serum Creatinine", "creatinine"), ("Blood Urea Nitrogen", "blood_urea_nitrogen"), ("BUN", "blood_urea_nitrogen"),
    ("Fasting Blood Sugar", "fasting_glucose"), ("Glucose Fasting", "fasting_glucose"), ("FBS", "fasting_glucose"),
    ("PPBS", "postprandial_glucose"), ("HbA1c", "hba1c"), ("Hemoglobin A1c", "hba1c"),
    ("Glycated Hemoglobin (HbA1c)", "hba1c"),
    ("Hemoglobin", "hemoglobin"), ("MCH", "mch"), ("MCHC", "mchc"),
    ("Mean Corpuscular Hemoglobin Concentration", "mchc"),
    ("T3", "t3"), ("Total T3", "t3"), ("Free T3", "free_t3"), ("T4 Total", "t4"), ("FT4", "free_t4"),
    ("25-OH Vitamin D", "vitamin_d"), ("Vitamin D3", "vitamin_d"), ("Vitamin B12", "vitamin_b12"),
    ("Serum Iron", "serum_iron"), ("Total Iron Binding Capacity", "tibc"), ("Ferritin", "ferritin"),
    ("Sodium", "sodium"), ("Potassium", "potassium"), ("Neutrophils", "neutrophils"),
    ("Non-HDL Cholesterol", None), ("HDL Cholesterol", "hdl_cholesterol"), ("Total Cholesterol", "total_cholesterol"),
])
def test_report_spellings_match_seeded_definitions(raw, expected):
    matched = match_definition(raw, SEEDED)
    assert (matched["canonical_name"] if matched else None) == expected


# ── Trends endpoints ──────────────────────────────────────────────────────────

class FakeLabResultsQuery:
    def __init__(self, rows):
        self.rows = rows

    def table(self, name):
        assert name == "lab_results"
        return self

    def select(self, *_):
        return self

    def eq(self, *_):
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


def _trend_row(value, created, name="tsh", label="TSH"):
    return {"value": value, "unit": "mIU/L", "status": "NORMAL", "reference_min": 0.4, "reference_max": 4.0,
            "reports": {"id": "r-" + created, "file_name": "report.pdf", "patient_id": "p1",
                        "report_date": None, "created_at": created},
            "test_definitions": {"canonical_name": name, "display_name": label, "category": "Thyroid"}}


@pytest.fixture
def patient_rows(monkeypatch):
    def install(rows):
        monkeypatch.setattr(patients_api, "get_supabase", lambda: FakeLabResultsQuery(rows))
        monkeypatch.setattr(patients_api, "_get_patient_by_auth_user", lambda _uid: {"id": "p1"})
    return install


def test_trend_tests_lists_only_tests_with_data_most_readings_first(patient_rows):
    patient_rows([
        _trend_row(2.0, "2026-01-01T00:00:00"),
        _trend_row(2.5, "2026-05-01T00:00:00"),
        _trend_row(13.1, "2026-05-01T00:00:00", "hemoglobin", "Hemoglobin"),
        _trend_row(None, "2026-05-01T00:00:00", "ferritin", "Ferritin"),  # no value
    ])
    out = patients_api.get_trend_tests(user_id="u1")
    assert [t["value"] for t in out] == ["tsh", "hemoglobin"]
    assert out[0]["count"] == 2 and out[0]["latest_date"] == "2026-05-01"


def test_trend_points_carry_unit_status_and_range_in_date_order(patient_rows):
    patient_rows([
        _trend_row(2.5, "2026-05-01T09:00:00"),
        _trend_row(2.0, "2026-01-01T00:00:00"),
        _trend_row(2.2, "2026-05-01T08:00:00"),   # same day, uploaded earlier
    ])
    out = patients_api.get_patient_trends(test_name="tsh", user_id="u1")
    assert [p["value"] for p in out] == [2.0, 2.2, 2.5]
    assert out[0]["unit"] == "mIU/L" and out[0]["reference_min"] == 0.4 and out[0]["reference_max"] == 4.0
    assert "sort_key" not in out[0]


def test_single_reading_still_returns_a_point(patient_rows):
    patient_rows([_trend_row(2.0, "2026-01-01T00:00:00")])
    assert len(patients_api.get_patient_trends(test_name="tsh", user_id="u1")) == 1
