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
