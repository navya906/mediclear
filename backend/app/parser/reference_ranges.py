"""
Reference Ranges — fallback reference ranges when OCR cannot extract them.

Maps canonical test names to (min, max, unit) tuples.
These are population-level reference ranges for adults and are used ONLY
as a last resort when the parsed reference range is missing from the report.
"""

from typing import Optional, Tuple

# (reference_min, reference_max, unit)
FALLBACK_RANGES: dict[str, Tuple[float, float, str]] = {
    # ── Complete Blood Count (CBC) ──────────────────────────────────────────
    "hemoglobin":               (13.0, 17.0,  "g/dL"),  # male range; female 12.0-15.5
    "hematocrit":               (39.0, 50.0,  "%"),
    "rbc":                      (4.5,  5.9,   "M/uL"),
    "wbc":                      (4.5,  11.0,  "K/uL"),
    "platelets":                (150.0, 400.0, "K/uL"),
    "mcv":                      (80.0, 100.0, "fL"),
    "mch":                      (27.0, 33.0,  "pg"),
    "mchc":                     (32.0, 36.0,  "g/dL"),
    "neutrophils":              (40.0, 70.0,  "%"),
    "lymphocytes":              (20.0, 40.0,  "%"),
    "monocytes":                (2.0,  10.0,  "%"),
    "eosinophils":              (1.0,  6.0,   "%"),
    "basophils":                (0.0,  1.0,   "%"),

    # ── Lipid Profile ────────────────────────────────────────────────────────
    "total_cholesterol":        (0.0,  200.0, "mg/dL"),
    "ldl":                      (0.0,  100.0, "mg/dL"),
    "hdl":                      (40.0, 60.0,  "mg/dL"),
    "triglycerides":            (0.0,  150.0, "mg/dL"),

    # ── Thyroid Profile ──────────────────────────────────────────────────────
    "tsh":                      (0.4,  4.0,   "mIU/L"),
    "free_t3":                  (2.3,  4.2,   "pg/mL"),
    "free_t4":                  (0.8,  1.8,   "ng/dL"),
    "t3":                       (80.0, 200.0, "ng/dL"),
    "t4":                       (5.1,  14.1,  "ug/dL"),

    # ── Liver Function Tests ─────────────────────────────────────────────────
    "alt":                      (7.0,  56.0,  "U/L"),
    "ast":                      (10.0, 40.0,  "U/L"),
    "alp":                      (44.0, 147.0, "U/L"),
    "bilirubin_total":          (0.1,  1.2,   "mg/dL"),
    "bilirubin_direct":         (0.0,  0.3,   "mg/dL"),
    "albumin":                  (3.5,  5.0,   "g/dL"),
    "total_protein":            (6.3,  8.2,   "g/dL"),

    # ── Kidney Function ──────────────────────────────────────────────────────
    "creatinine":               (0.6,  1.2,   "mg/dL"),
    "blood_urea_nitrogen":      (7.0,  20.0,  "mg/dL"),
    "uric_acid":                (3.5,  7.2,   "mg/dL"),
    "egfr":                     (60.0, 120.0, "mL/min/1.73m²"),

    # ── Blood Glucose ────────────────────────────────────────────────────────
    "fasting_glucose":          (70.0, 100.0, "mg/dL"),
    "hba1c":                    (4.0,  5.7,   "%"),
    "postprandial_glucose":     (70.0, 140.0, "mg/dL"),

    # ── Electrolytes ─────────────────────────────────────────────────────────
    "sodium":                   (136.0, 145.0, "mEq/L"),
    "potassium":                (3.5,  5.0,   "mEq/L"),
    "chloride":                 (98.0, 107.0, "mEq/L"),
    "calcium":                  (8.5,  10.5,  "mg/dL"),
    "magnesium":                (1.7,  2.2,   "mg/dL"),
    "phosphorus":               (2.5,  4.5,   "mg/dL"),

    # ── Iron Studies ─────────────────────────────────────────────────────────
    "serum_iron":               (60.0, 170.0, "ug/dL"),
    "ferritin":                 (12.0, 300.0, "ng/mL"),
    "tibc":                     (240.0, 450.0, "ug/dL"),

    # ── Vitamins ─────────────────────────────────────────────────────────────
    "vitamin_d":                (20.0, 50.0,  "ng/mL"),
    "vitamin_b12":              (200.0, 900.0, "pg/mL"),
    "folate":                   (2.7,  17.0,  "ng/mL"),
}


def get_fallback_range(canonical_name: str) -> Optional[Tuple[float, float, str]]:
    """
    Return (min, max, unit) for a canonical test name, or None if not found.
    Normalises the key by lowercasing and replacing spaces/hyphens with underscores.
    """
    key = canonical_name.lower().replace(" ", "_").replace("-", "_")
    return FALLBACK_RANGES.get(key)
