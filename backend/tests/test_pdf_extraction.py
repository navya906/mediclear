"""
End-to-end extraction tests on generated digital PDFs: text layer -> parser.

Lab software usually draws every table cell as a separate text object, so
these build PDFs that way rather than as one string per row.
"""

import fitz  # PyMuPDF
import pytest

from app.ocr.pdf import extract_text_from_pdf
from app.parser.parser import normalise_text, parse_lab_text

# (name, value, unit, range) -> expected (value, ref_min, ref_max)
ROWS = [
    ("Hemoglobin (Hb)",       "11.2",     "g/dL",       "12.0 - 15.5",         (11.2, 12.0, 15.5)),
    ("Total Leucocyte Count", "7,800",    "cells/cumm", "4,000 - 11,000",      (7800, 4000, 11000)),
    ("Platelet Count",        "2,10,000", "/cumm",      "1,50,000 - 4,50,000", (210000, 150000, 450000)),
    ("Total Cholesterol",     "212",      "mg/dL",      "< 200",               (212, None, 200)),
    ("HDL Cholesterol",       "48",       "mg/dL",      "> 40",                (48, 40, None)),
    ("TSH",                   "3.20",     "mIU/L",      "0.40 - 4.00",         (3.2, 0.4, 4.0)),
]
COLUMN_X = [40, 220, 300, 400]


def _pdf(draw_rows, pages=1):
    doc = fitz.open()
    per_page = -(-len(ROWS) // pages)
    for p in range(pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((40, 50), "Patient Name : Jane Doe    Age / Sex : 34 Y / F", fontsize=9)
        page.insert_text((40, 64), "Sample Collected : 02/10/2026 09:12", fontsize=9)
        draw_rows(page, ROWS[p * per_page:(p + 1) * per_page])
        page.insert_text((40, 800), f"Page {p + 1} of {pages}", fontsize=9)
    return doc.tobytes()


def _cells(order=(0, 1, 2, 3)):
    def draw(page, rows):
        y = 100
        for name, value, unit, ref, _ in rows:
            cells = [name, value, unit, ref]
            for col, x in zip(order, COLUMN_X):
                page.insert_text((x, y), cells[col], fontsize=9)
            y += 15
    return draw


WRAPPED = {"Total Leucocyte Count": ("Total Leucocyte", "Count")}


def _jittered_wrapped(page, rows):
    """Bold, larger values slightly off the baseline; a long name wraps."""
    y = 100
    for name, value, unit, ref, _ in rows:
        first, second = WRAPPED.get(name, (name, None))
        page.insert_text((40, y), first, fontsize=9)
        page.insert_text((220, y + 1.5), value, fontsize=10.5, fontname="hebo")
        page.insert_text((300, y - 1), unit, fontsize=9)
        page.insert_text((400, y), ref, fontsize=9)
        if second:
            y += 11
            page.insert_text((40, y), second, fontsize=9)
        y += 15


def _assert_all_rows(results):
    by_name = {r["test_name_raw"]: r for r in results}
    assert list(by_name) == [r[0] for r in ROWS]
    for name, _, unit, _, (value, ref_min, ref_max) in ROWS:
        r = by_name[name]
        assert (r["value"], r["unit"], r["reference_min"], r["reference_max"]) == (value, unit, ref_min, ref_max), name


@pytest.mark.parametrize("label, draw, pages", [
    ("cells drawn separately", _cells(), 1),
    ("range column before unit", _cells(order=(0, 1, 3, 2)), 1),
    ("jittered values, wrapped names", _jittered_wrapped, 1),
    ("split across two pages", _cells(), 2),
])
def test_table_layouts(label, draw, pages):
    text = extract_text_from_pdf(_pdf(draw, pages))
    _assert_all_rows(parse_lab_text(text))


def test_cells_rebuilt_into_rows():
    text = extract_text_from_pdf(_pdf(_cells()))
    assert "Hemoglobin (Hb) 11.2 g/dL 12.0 - 15.5" in text


class TestLookAlikeCharacters:

    @pytest.mark.parametrize("raw", [
        "Hemoglobin (Hb) 11.2 g/dL 12.0 ­ 15.5",  # nbsp + soft hyphen
        "Hemoglobin (Hb) 11.2 g/dL 12.0 – 15.5",                              # en dash
        "Hemoglobin (Hb) 11.2 g/dL 12.0 − 15.5",                              # minus sign
        "Hemoglobin (Hb)\t11.2\tg/dL\t12.0-15.5",                                  # tabs
    ])
    def test_parsed_like_plain_text(self, raw):
        r = parse_lab_text(raw)[0]
        assert (r["test_name_raw"], r["value"], r["reference_min"], r["reference_max"]) == \
            ("Hemoglobin (Hb)", 11.2, 12.0, 15.5)

    def test_normalise_text(self):
        assert normalise_text("a b c 1– 2") == "a b c 1- 2"


class TestNameContinuation:

    def test_wrapped_name_is_joined(self):
        r = parse_lab_text("Total Leucocyte 7,800 cells/cumm 4000-11000\nCount")
        assert r[0]["test_name_raw"] == "Total Leucocyte Count"

    def test_bracketed_caps_joined(self):
        r = parse_lab_text("Hematocrit 36.5 % 36-46\n(PCV)")
        assert r[0]["test_name_raw"] == "Hematocrit (PCV)"

    @pytest.mark.parametrize("follow", [
        "LIPID PROFILE",                  # section heading
        "Method: Automated analyser",     # has a colon
        "Colorimetric",                   # test method printed under the name
        "(Photometry)",
        "Interpretation",                 # note, not part of the name
        "Page 1 of 2",                    # metadata
    ])
    def test_other_lines_are_not_joined(self, follow):
        r = parse_lab_text(f"Lymphocytes 30 % 20-40\n{follow}")
        assert r[0]["test_name_raw"] == "Lymphocytes"

    def test_text_before_a_result_is_not_joined(self):
        text = "Haematology\nHemoglobin 11.2 g/dL 12-15.5"
        assert [r["test_name_raw"] for r in parse_lab_text(text)] == ["Hemoglobin"]


def test_unit_after_range_needs_a_range():
    # without a range, a trailing word is not taken as the unit
    assert parse_lab_text("MCV 88.0 83 - 101 fL")[0]["unit"] == "fL"
    assert parse_lab_text("Hemoglobin 14.2 g/dL 13-17 H")[0]["unit"] == "g/dL"
    assert parse_lab_text("TSH 3.2 0.4 - 4.0")[0]["unit"] == ""


def _two_pieces(left, right, gap):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((40, 100), left, fontsize=9)
    page.insert_text((40 + fitz.get_text_length(left, fontsize=9) + gap, 100), right, fontsize=9)
    return doc, page


@pytest.mark.parametrize("gap", [1.6, 2.0])
def test_kerned_word_pieces_are_rejoined(gap):
    """Some PDFs draw "Total" as "T" + "otal" with a small kerning gap."""
    doc, page = _two_pieces("T", "otal Cholesterol", gap)
    assert [w[4] for w in page.get_text("words")][:2] == ["T", "otal"]  # PyMuPDF splits it
    assert extract_text_from_pdf(doc.tobytes()) == "Total Cholesterol"


@pytest.mark.parametrize("left, right, expected", [
    ("Hepatitis B", "surface Antigen", "Hepatitis B surface Antigen"),
    ("Vitamin", "D", "Vitamin D"),
    ("Free", "T4", "Free T4"),
])
def test_real_spaces_are_kept(left, right, expected):
    doc, _ = _two_pieces(left, right, fitz.get_text_length(" ", fontsize=9))
    assert extract_text_from_pdf(doc.tobytes()) == expected
