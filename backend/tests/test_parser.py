"""
Unit tests for app.parser.parser — lab text extraction.
"""

import pytest
from app.parser.parser import parse_lab_text


class TestParseLabText:

    def test_inline_pattern(self):
        text = "Hemoglobin 14.2 g/dL 13.0-17.0"
        results = parse_lab_text(text)
        assert len(results) == 1
        r = results[0]
        assert r["test_name_raw"] == "Hemoglobin"
        assert r["value"] == 14.2
        assert r["unit"] == "g/dL"
        assert r["reference_min"] == 13.0
        assert r["reference_max"] == 17.0
        assert r["extraction_confidence"] >= 0.85

    def test_colon_pattern(self):
        text = "TSH: 2.5 mIU/L (0.4-4.0)"
        results = parse_lab_text(text)
        assert len(results) == 1
        r = results[0]
        assert "TSH" in r["test_name_raw"]
        assert r["value"] == 2.5
        assert r["reference_min"] == 0.4
        assert r["reference_max"] == 4.0

    def test_no_reference_pattern(self):
        text = "WBC 7.5 K/uL"
        results = parse_lab_text(text)
        assert len(results) == 1
        r = results[0]
        assert r["reference_min"] is None
        assert r["extraction_confidence"] < 0.75

    def test_multiple_lines(self):
        text = (
            "Hemoglobin 14.2 g/dL 13.0-17.0\n"
            "WBC 7.5 K/uL 4.5-11.0\n"
            "Platelets 220 K/uL 150.0-400.0\n"
        )
        results = parse_lab_text(text)
        assert len(results) == 3

    def test_noise_lines_ignored(self):
        text = (
            "Patient Name: John Doe\n"
            "Date: 2026-01-01\n"
            "Hemoglobin 14.2 g/dL 13.0-17.0\n"
        )
        results = parse_lab_text(text)
        names = [r["test_name_raw"].lower() for r in results]
        assert all("date" not in n and "patient" not in n for n in names)
        assert any("hemoglobin" in n for n in names)

    def test_empty_text(self):
        assert parse_lab_text("") == []

    def test_duplicate_lines_deduplicated(self):
        text = (
            "Hemoglobin 14.2 g/dL 13.0-17.0\n"
            "Hemoglobin 14.2 g/dL 13.0-17.0\n"
        )
        results = parse_lab_text(text)
        assert len(results) == 1


class TestRealWorldFormats:

    def _one(self, line):
        results = parse_lab_text(line)
        assert len(results) == 1, results
        return results[0]

    def test_indian_comma_grouping(self):
        r = self._one("Platelet Count 1,50,000 /cumm 1,50,000 - 4,50,000")
        assert r["test_name_raw"] == "Platelet Count"
        assert r["value"] == 150000.0
        assert r["unit"] == "/cumm"
        assert (r["reference_min"], r["reference_max"]) == (150000.0, 450000.0)

    def test_western_comma_grouping(self):
        r = self._one("Total Leucocyte Count 7,200 cells/cumm 4000-11000")
        assert r["value"] == 7200.0
        assert r["unit"] == "cells/cumm"

    @pytest.mark.parametrize("line, unit", [
        ("WBC 7.2 10^3/uL 4.0-11.0", "10^3/uL"),
        ("RBC 4.8 x10^6/µL 4.5-5.5", "x10^6/µL"),
        ("eGFR 95 mL/min/1.73m2 60-120", "mL/min/1.73m2"),
    ])
    def test_units_with_digits(self, line, unit):
        r = self._one(line)
        assert r["unit"] == unit
        assert r["reference_min"] is not None

    def test_value_with_comparator(self):
        r = self._one("Glucose <70 mg/dL")
        assert r["value"] == 70.0
        assert r["unit"] == "mg/dL"
        assert r["extraction_confidence"] < 0.6

    @pytest.mark.parametrize("line, ref_min, ref_max, text", [
        ("LDL Cholesterol 130 mg/dL < 100", None, 100.0, "< 100"),
        ("Total Cholesterol 180 mg/dL (<200)", None, 200.0, "< 200"),
        ("HDL Cholesterol 45 mg/dL > 40", 40.0, None, "> 40"),
        ("Triglycerides 120 mg/dL Up to 150", None, 150.0, "< 150"),
    ])
    def test_one_sided_reference(self, line, ref_min, ref_max, text):
        r = self._one(line)
        assert (r["reference_min"], r["reference_max"], r["reference_text"]) == (ref_min, ref_max, text)
        assert r["extraction_confidence"] == 0.85

    def test_flag_and_to_range(self):
        r = self._one("Hemoglobin 10.1 L g/dL 13.0 to 17.0")
        assert r["value"] == 10.1
        assert r["unit"] == "g/dL"
        assert (r["reference_min"], r["reference_max"]) == (13.0, 17.0)

    @pytest.mark.parametrize("line, name", [
        ("Vitamin B12 450 pg/mL 200-900", "Vitamin B12"),
        ("Free T3 3.1 pg/mL 2.3-4.2", "Free T3"),
        ("HbA1c 5.6 % 4.0-5.6", "HbA1c"),
        ("Hemoglobin (Hb) 14.2 g/dL 13-17", "Hemoglobin (Hb)"),
        ("Cholesterol, Total 180 mg/dL <200", "Cholesterol, Total"),
        ("1. Hemoglobin 14.2 g/dL 13-17", "Hemoglobin"),
    ])
    def test_names_with_digits_and_punctuation(self, line, name):
        assert self._one(line)["test_name_raw"] == name

    def test_reference_without_unit(self):
        r = self._one("Hemoglobin 14.2 13.0-17.0")
        assert r["unit"] == ""
        assert r["reference_max"] == 17.0

    @pytest.mark.parametrize("line", [
        "Age 45 Years",
        "Page 1 of 2",
        "Sample Collected On 12/03/2026 10:15",
        "Report Date 12-03-2026",
        "Patient ID 102938",
        "Ref. Range Unit Result",
        "Hemoglobin",
        "Blood pressure 120/80",
    ])
    def test_metadata_lines_ignored(self, line):
        assert parse_lab_text(line) == []

    def test_full_report(self):
        text = """
        CITY DIAGNOSTICS LAB
        Patient Name : Jane Doe          Age / Sex : 34 Y / F
        Sample Collected On : 02/10/2026 09:12
        Test Name               Result   Unit        Bio. Ref. Interval
        COMPLETE BLOOD COUNT
        Hemoglobin (Hb)         11.2  L  g/dL        12.0 - 15.5
        Total Leucocyte Count   7,800    cells/cumm  4,000 - 11,000
        Platelet Count          2,10,000 /cumm       1,50,000 - 4,50,000
        LIPID PROFILE
        Cholesterol, Total      212   H  mg/dL       < 200
        HDL Cholesterol         48       mg/dL       > 40
        LDL Cholesterol         138      mg/dL       < 100
        THYROID
        TSH                     3.2      µIU/mL      0.4 - 4.0
        Page 1 of 1
        """
        results = parse_lab_text(text)
        by_name = {r["test_name_raw"]: r for r in results}
        assert list(by_name) == [
            "Hemoglobin (Hb)", "Total Leucocyte Count", "Platelet Count",
            "Cholesterol, Total", "HDL Cholesterol", "LDL Cholesterol", "TSH",
        ]
        assert by_name["Platelet Count"]["value"] == 210000.0
        assert by_name["Cholesterol, Total"]["reference_max"] == 200.0
        assert by_name["TSH"]["unit"] == "µIU/mL"


class TestExplanatoryText:
    """Interpretation paragraphs printed under a result must not become results."""

    VITAMIN_D_REPORT = (
        "25-OH Vitamin D (Total)          22.4    ng/mL     30 - 100\n"
        "Interpretation\n"
        "Deficiency < 20 ng/mL, Insufficiency 20 - 30 ng/mL, Sufficiency 30 - 100 ng/mL, Toxicity > 100 ng/mL\n"
        "Vitamin D promotes absorption of calcium and phosphorus and mineralization of bones and\n"
        "teeth. Deficiency in children causes rickets and in adults leads to osteomalacia.\n"
        "Optimal calcium absorption (34 ng/mL). Neuromuscular peak performance is associated with levels approximately\n"
        "38 ng/mL. Vitamin D supplementation in elderly people reduces the risk of falls by 20 % in subjects\n"
        "increasing mean baseline levels from 29 to 38 ng/mL.\n"
        "Levels above 150 ng/mL are toxic.\n"
        "Serum Calcium 9.4 mg/dL 8.5 - 10.5\n"
        "S. Creatinine 0.9 mg/dL 0.6 - 1.1\n"
    )

    def test_only_real_results_kept(self):
        names = [r["test_name_raw"] for r in parse_lab_text(self.VITAMIN_D_REPORT)]
        assert names == ["25-OH Vitamin D (Total)", "Serum Calcium", "S. Creatinine"]

    @pytest.mark.parametrize("line", [
        "increasing mean baseline levels from 29 to 38 ng/mL.",
        "Levels above 150 ng/mL are toxic.",
        "Neuromuscular peak performance is associated with levels approximately 38 ng/mL.",
        "Deficiency < 20 ng/mL, Insufficiency 20 - 30 ng/mL",
        "Desirable < 200 mg/dL",
        "Borderline 200 - 239 mg/dL",
    ])
    def test_sentences_and_legends_ignored(self, line):
        assert parse_lab_text(line) == []

    def test_english_word_is_not_a_unit(self):
        assert parse_lab_text("Ferritin 29 to") == []

    def test_trailing_comment_allowed_when_range_present(self):
        r = parse_lab_text("HbA1c 6.8 % 4.0 - 5.6 Diabetic range as per ADA guidelines")[0]
        assert (r["test_name_raw"], r["value"], r["reference_max"]) == ("HbA1c", 6.8, 5.6)

    @pytest.mark.parametrize("line, name", [
        ("25-OH Vitamin D (Total) 22.4 ng/mL 30 - 100", "25-OH Vitamin D (Total)"),
        ("1,25-Dihydroxy Vitamin D 45 pg/mL 19.9 - 79.3", "1,25-Dihydroxy Vitamin D"),
        ("Mean Corpuscular Hemoglobin Concentration (MCHC) 33.1 g/dL 32 - 36",
         "Mean Corpuscular Hemoglobin Concentration (MCHC)"),
    ])
    def test_longer_real_names_kept(self, line, name):
        assert parse_lab_text(line)[0]["test_name_raw"] == name
