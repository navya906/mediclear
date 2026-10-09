"""
Tests for the AI layer: safety filtering, prompt context, and regeneration.
No network: the LLM client is patched out.
"""

import uuid
from datetime import date
from types import SimpleNamespace

import pytest

from app.ai import explainer, generator, prompts
from app.services import explanation_service


class TestSafetyFilter:

    @pytest.mark.parametrize("text", [
        "You have diabetes.",
        "You probably have an iron deficiency.",
        "You are diagnosed with anemia.",
        "This means you have a thyroid problem.",
        "You should take iron supplements.",
        "You need to stop your medication.",
        "The treatment is surgery.",
        "There is no cure.",
    ])
    def test_flags_diagnosis_and_treatment(self, text):
        assert explainer.is_unsafe(text)

    @pytest.mark.parametrize("text", [
        "If you have questions, ask your doctor.",
        "Low hemoglobin can be linked to anemia.",
        "Should I take iron supplements?",
        "A doctor may check whether this suggests hypothyroidism.",
        "This is accurate and secure.",
    ])
    def test_allows_ordinary_wording(self, text):
        assert not explainer.is_unsafe(text)

    def test_every_field_is_sanitised(self, monkeypatch):
        content = """{
            "simple_explanation": "You have anemia.",
            "why_it_matters": "The treatment is iron tablets.",
            "possible_reasons": ["Low iron intake", "You have a bleeding disorder", 42],
            "doctor_questions": "Could my diet be a factor?"
        }"""
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw: response))
        )
        monkeypatch.setattr(explainer, "get_client", lambda: fake_client)

        out = explainer.call_llm("prompt")
        assert out["simple_explanation"] == explainer._SAFE_FALLBACK_TEXT
        assert out["why_it_matters"] == explainer._SAFE_FALLBACK_TEXT
        assert out["possible_reasons"] == ["Low iron intake"]
        assert out["doctor_questions"] == ["Could my diet be a factor?"]


class TestPatientContext:

    def test_age_and_sex(self):
        dob = date(date.today().year - 34, 1, 1).isoformat()
        context = prompts.build_patient_context({"date_of_birth": dob, "sex": "female"})
        assert context == "Patient: Age: 34, Sex: female"

    def test_age_before_birthday(self):
        assert prompts._age_in_years("1990-12-31", today=date(2026, 6, 1)) == 35

    def test_unknown_or_undisclosed(self):
        assert prompts.build_patient_context(None) == ""
        assert prompts.build_patient_context({"date_of_birth": None, "sex": "prefer_not_to_say"}) == ""

    def test_context_is_in_prompt(self):
        prompt = prompts.build_explanation_prompt(
            {"value": 11.2, "unit": "g/dL", "status": "LOW"},
            {"display_name": "Hemoglobin"},
            [],
            {"sex": "female"},
        )
        assert "Patient: Sex: female" in prompt


def _llm_answer(text):
    return lambda prompt: {
        "simple_explanation": text,
        "why_it_matters": "",
        "possible_reasons": [],
        "doctor_questions": [],
    }


class TestGenerator:

    def test_saves_configured_model_name(self, monkeypatch):
        monkeypatch.setattr(generator, "get_client", lambda: object())
        monkeypatch.setattr(generator, "call_llm", _llm_answer("ok"))
        out = generator.generate_explanation({"id": str(uuid.uuid4())}, {}, [])
        assert out.model == generator.AI_MODEL

    def test_empty_llm_answer_is_an_error(self, monkeypatch):
        monkeypatch.setattr(generator, "get_client", lambda: object())
        monkeypatch.setattr(generator, "call_llm", _llm_answer("  "))
        out = generator.generate_explanation({"id": str(uuid.uuid4())}, {}, [])
        assert out.model == generator.MODEL_ERROR

    @pytest.mark.parametrize("model, has_key, expected", [
        ("error", False, True),
        ("error", True, True),
        ("fallback", True, True),
        ("fallback", False, False),
        ("gpt-4o-mini", True, False),
    ])
    def test_should_regenerate(self, monkeypatch, model, has_key, expected):
        monkeypatch.setattr(generator, "get_client", lambda: object() if has_key else None)
        assert generator.should_regenerate({"model": model}) is expected


class FakeExplanations:
    """Minimal stand-in for supabase.table('explanations')."""

    def __init__(self, existing=None):
        self.rows = [existing] if existing else []
        self.inserted = []
        self.updated = []

    def table(self, name):
        assert name == "explanations"
        store = self

        class Query:
            op = "select"
            payload = None

            def select(self, *_):
                return self

            def eq(self, *_):
                return self

            def limit(self, *_):
                return self

            def insert(self, payload):
                self.op, self.payload = "insert", payload
                return self

            def update(self, payload):
                self.op, self.payload = "update", payload
                return self

            def execute(self):
                if self.op == "insert":
                    store.inserted.append(self.payload)
                    return SimpleNamespace(data=[self.payload])
                if self.op == "update":
                    store.updated.append(self.payload)
                    return SimpleNamespace(data=[{**store.rows[0], **self.payload}])
                return SimpleNamespace(data=store.rows)

        return Query()


class TestExplanationService:

    RESULT = {"id": str(uuid.uuid4()), "value": 11.2, "status": "LOW"}

    @pytest.fixture(autouse=True)
    def stub_llm(self, monkeypatch):
        monkeypatch.setattr(generator, "get_client", lambda: object())
        monkeypatch.setattr(generator, "call_llm", _llm_answer("Fresh explanation"))

    def test_new_explanation_insert_is_json_serialisable(self):
        fake = FakeExplanations()
        saved = explanation_service.get_or_create_explanation(fake, self.RESULT, {}, [])
        assert saved["simple_explanation"] == "Fresh explanation"
        assert isinstance(fake.inserted[0]["lab_result_id"], str)  # not a UUID object

    def test_good_explanation_is_reused(self):
        existing = {"id": "e1", "model": "gpt-4o-mini", "simple_explanation": "Old"}
        fake = FakeExplanations(existing)
        assert explanation_service.get_or_create_explanation(fake, self.RESULT, {}, []) == existing
        assert fake.inserted == []
        assert fake.updated == []

    def test_error_placeholder_is_replaced_in_place(self):
        fake = FakeExplanations({"id": "e1", "model": "error", "simple_explanation": "We could not..."})
        saved = explanation_service.get_or_create_explanation(fake, self.RESULT, {}, [])
        assert saved["id"] == "e1"
        assert saved["simple_explanation"] == "Fresh explanation"
        assert fake.inserted == []
