"""
Seed test_definitions table with every test that has a fallback reference range
(CBC, lipid, thyroid, liver, kidney, glucose, electrolytes, iron, vitamins).

After seeding, run data/rematch_lab_results.py --apply so results from
reports uploaded earlier are linked to the new definitions and show up in trends.

Run once from the project root (with the backend venv activated):
    cd backend
    python ../data/seed_test_definitions.py

Requires backend/.env to be present with SUPABASE_URL and SUPABASE_ANON_KEY.
"""

import os
import sys

# Allow importing from backend/app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from app.database.client import get_supabase  # noqa: E402

TEST_DEFINITIONS = [
    # ── CBC ──────────────────────────────────────────────────────────────
    {
        "canonical_name": "hemoglobin",
        "display_name": "Hemoglobin",
        "category": "CBC",
        "default_unit": "g/dL",
        "description": "Measures the protein in red blood cells that carries oxygen around your body.",
    },
    {
        "canonical_name": "wbc",
        "display_name": "White Blood Cell Count (WBC)",
        "category": "CBC",
        "default_unit": "10³/µL",
        "description": "Counts the white blood cells that fight infection and disease.",
    },
    {
        "canonical_name": "rbc",
        "display_name": "Red Blood Cell Count (RBC)",
        "category": "CBC",
        "default_unit": "10⁶/µL",
        "description": "Counts the red blood cells that carry oxygen from your lungs to your body.",
    },
    {
        "canonical_name": "platelets",
        "display_name": "Platelet Count",
        "category": "CBC",
        "default_unit": "10³/µL",
        "description": "Counts the tiny cells that help your blood clot when you have a cut or injury.",
    },
    {
        "canonical_name": "hematocrit",
        "display_name": "Hematocrit",
        "category": "CBC",
        "default_unit": "%",
        "description": "The percentage of your blood volume made up of red blood cells.",
    },
    # ── Lipid Profile ────────────────────────────────────────────────────
    {
        "canonical_name": "total_cholesterol",
        "display_name": "Total Cholesterol",
        "category": "Lipid Profile",
        "default_unit": "mg/dL",
        "description": "Measures all cholesterol in your blood. High levels can raise heart disease risk.",
    },
    {
        "canonical_name": "ldl_cholesterol",
        "display_name": "LDL Cholesterol",
        "category": "Lipid Profile",
        "default_unit": "mg/dL",
        "description": "Often called 'bad' cholesterol. High LDL can build up in artery walls.",
    },
    {
        "canonical_name": "hdl_cholesterol",
        "display_name": "HDL Cholesterol",
        "category": "Lipid Profile",
        "default_unit": "mg/dL",
        "description": "Often called 'good' cholesterol. HDL helps remove other forms of cholesterol.",
    },
    {
        "canonical_name": "triglycerides",
        "display_name": "Triglycerides",
        "category": "Lipid Profile",
        "default_unit": "mg/dL",
        "description": "A type of fat in your blood. High levels are linked to heart disease.",
    },
    # ── Thyroid Profile ──────────────────────────────────────────────────
    {
        "canonical_name": "tsh",
        "display_name": "TSH (Thyroid Stimulating Hormone)",
        "category": "Thyroid Profile",
        "default_unit": "mIU/L",
        "description": "Controls how much thyroid hormone your body makes. A key indicator of thyroid health.",
    },
    {
        "canonical_name": "free_t3",
        "display_name": "Free T3 (Triiodothyronine)",
        "category": "Thyroid Profile",
        "default_unit": "pg/mL",
        "description": "The active form of thyroid hormone that regulates metabolism and energy.",
    },
    {
        "canonical_name": "free_t4",
        "display_name": "Free T4 (Thyroxine)",
        "category": "Thyroid Profile",
        "default_unit": "ng/dL",
        "description": "The main thyroid hormone. It converts to T3 and helps control many body functions.",
    },
    # ── CBC ───────────────────────────────────────────────────────────────
    {
        "canonical_name": "mcv",
        "display_name": "MCV (Mean Corpuscular Volume)",
        "category": "CBC",
        "default_unit": "fL",
        "description": "The average size of your red blood cells.",
    },
    {
        "canonical_name": "mch",
        "display_name": "MCH (Mean Corpuscular Hemoglobin)",
        "category": "CBC",
        "default_unit": "pg",
        "description": "The average amount of hemoglobin inside each red blood cell.",
    },
    {
        "canonical_name": "mchc",
        "display_name": "MCHC (Mean Corpuscular Hemoglobin Concentration)",
        "category": "CBC",
        "default_unit": "g/dL",
        "description": "How concentrated the hemoglobin is inside your red blood cells.",
    },
    {
        "canonical_name": "neutrophils",
        "display_name": "Neutrophils",
        "category": "CBC",
        "default_unit": "%",
        "description": "The most common white blood cell; the first responders to bacterial infections.",
    },
    {
        "canonical_name": "lymphocytes",
        "display_name": "Lymphocytes",
        "category": "CBC",
        "default_unit": "%",
        "description": "White blood cells that fight viruses and make antibodies.",
    },
    {
        "canonical_name": "monocytes",
        "display_name": "Monocytes",
        "category": "CBC",
        "default_unit": "%",
        "description": "White blood cells that clean up damaged cells and fight infection.",
    },
    {
        "canonical_name": "eosinophils",
        "display_name": "Eosinophils",
        "category": "CBC",
        "default_unit": "%",
        "description": "White blood cells involved in allergies and fighting parasites.",
    },
    {
        "canonical_name": "basophils",
        "display_name": "Basophils",
        "category": "CBC",
        "default_unit": "%",
        "description": "A small group of white blood cells involved in allergic reactions.",
    },
    # ── Thyroid Profile ───────────────────────────────────────────────────
    {
        "canonical_name": "t3",
        "display_name": "Total T3",
        "category": "Thyroid Profile",
        "default_unit": "ng/dL",
        "description": "The total amount of the active thyroid hormone T3 in your blood.",
    },
    {
        "canonical_name": "t4",
        "display_name": "Total T4",
        "category": "Thyroid Profile",
        "default_unit": "ug/dL",
        "description": "The total amount of the main thyroid hormone T4 in your blood.",
    },
    # ── Liver Function ────────────────────────────────────────────────────
    {
        "canonical_name": "alt",
        "display_name": "ALT (SGPT)",
        "category": "Liver Function",
        "default_unit": "U/L",
        "description": "A liver enzyme. Higher levels can be a sign that liver cells are irritated or damaged.",
    },
    {
        "canonical_name": "ast",
        "display_name": "AST (SGOT)",
        "category": "Liver Function",
        "default_unit": "U/L",
        "description": "An enzyme found in the liver, heart and muscles that can rise when these are stressed.",
    },
    {
        "canonical_name": "alp",
        "display_name": "Alkaline Phosphatase (ALP)",
        "category": "Liver Function",
        "default_unit": "U/L",
        "description": "An enzyme from the liver and bones; it can change with liver, bile duct or bone conditions.",
    },
    {
        "canonical_name": "bilirubin_total",
        "display_name": "Bilirubin Total",
        "category": "Liver Function",
        "default_unit": "mg/dL",
        "description": "A yellow substance made when old red blood cells break down; the liver clears it.",
    },
    {
        "canonical_name": "bilirubin_direct",
        "display_name": "Bilirubin Direct",
        "category": "Liver Function",
        "default_unit": "mg/dL",
        "description": "The part of bilirubin the liver has already processed.",
    },
    {
        "canonical_name": "albumin",
        "display_name": "Albumin",
        "category": "Liver Function",
        "default_unit": "g/dL",
        "description": "The main protein made by the liver. It keeps fluid in your blood vessels.",
    },
    {
        "canonical_name": "total_protein",
        "display_name": "Total Protein",
        "category": "Liver Function",
        "default_unit": "g/dL",
        "description": "The total amount of protein in your blood, mainly albumin and globulins.",
    },
    # ── Kidney Function ───────────────────────────────────────────────────
    {
        "canonical_name": "blood_urea_nitrogen",
        "display_name": "Blood Urea Nitrogen (BUN)",
        "category": "Kidney Function",
        "default_unit": "mg/dL",
        "description": "A waste product the kidneys filter out; it reflects kidney function and hydration.",
    },
    {
        "canonical_name": "creatinine",
        "display_name": "Creatinine",
        "category": "Kidney Function",
        "default_unit": "mg/dL",
        "description": "A muscle waste product cleared by the kidneys; used to check how well they filter.",
    },
    {
        "canonical_name": "egfr",
        "display_name": "eGFR (Estimated Glomerular Filtration Rate)",
        "category": "Kidney Function",
        "default_unit": "mL/min/1.73m²",
        "description": "An estimate of how much blood your kidneys filter each minute.",
    },
    {
        "canonical_name": "uric_acid",
        "display_name": "Uric Acid",
        "category": "Kidney Function",
        "default_unit": "mg/dL",
        "description": "A waste product from breaking down purines; high levels can cause gout.",
    },
    # ── Blood Glucose ─────────────────────────────────────────────────────
    {
        "canonical_name": "fasting_glucose",
        "display_name": "Fasting Glucose",
        "category": "Blood Glucose",
        "default_unit": "mg/dL",
        "description": "Your blood sugar level after not eating for at least 8 hours.",
    },
    {
        "canonical_name": "postprandial_glucose",
        "display_name": "Postprandial Glucose",
        "category": "Blood Glucose",
        "default_unit": "mg/dL",
        "description": "Your blood sugar level about 2 hours after a meal.",
    },
    {
        "canonical_name": "hba1c",
        "display_name": "HbA1c (Glycated Hemoglobin)",
        "category": "Blood Glucose",
        "default_unit": "%",
        "description": "Your average blood sugar over the past 2-3 months.",
    },
    # ── Electrolytes ──────────────────────────────────────────────────────
    {
        "canonical_name": "sodium",
        "display_name": "Sodium",
        "category": "Electrolytes",
        "default_unit": "mEq/L",
        "description": "A mineral that controls fluid balance and helps nerves and muscles work.",
    },
    {
        "canonical_name": "potassium",
        "display_name": "Potassium",
        "category": "Electrolytes",
        "default_unit": "mEq/L",
        "description": "A mineral that keeps your heart rhythm and muscles working properly.",
    },
    {
        "canonical_name": "chloride",
        "display_name": "Chloride",
        "category": "Electrolytes",
        "default_unit": "mEq/L",
        "description": "A mineral that works with sodium to keep fluids and acidity in balance.",
    },
    {
        "canonical_name": "calcium",
        "display_name": "Calcium",
        "category": "Electrolytes",
        "default_unit": "mg/dL",
        "description": "A mineral needed for strong bones, muscle movement and nerve signals.",
    },
    {
        "canonical_name": "magnesium",
        "display_name": "Magnesium",
        "category": "Electrolytes",
        "default_unit": "mg/dL",
        "description": "A mineral used by muscles, nerves and the heart.",
    },
    {
        "canonical_name": "phosphorus",
        "display_name": "Phosphorus",
        "category": "Electrolytes",
        "default_unit": "mg/dL",
        "description": "A mineral that works with calcium to build bones and teeth.",
    },
    # ── Iron Studies ──────────────────────────────────────────────────────
    {
        "canonical_name": "serum_iron",
        "display_name": "Serum Iron",
        "category": "Iron Studies",
        "default_unit": "ug/dL",
        "description": "The amount of iron circulating in your blood.",
    },
    {
        "canonical_name": "tibc",
        "display_name": "TIBC (Total Iron Binding Capacity)",
        "category": "Iron Studies",
        "default_unit": "ug/dL",
        "description": "How well your blood can carry iron; it often rises when iron stores are low.",
    },
    {
        "canonical_name": "ferritin",
        "display_name": "Ferritin",
        "category": "Iron Studies",
        "default_unit": "ng/mL",
        "description": "A protein that stores iron; it shows how much iron your body has in reserve.",
    },
    # ── Vitamins ──────────────────────────────────────────────────────────
    {
        "canonical_name": "vitamin_d",
        "display_name": "Vitamin D (25-OH)",
        "category": "Vitamins",
        "default_unit": "ng/mL",
        "description": "Vitamin D helps your body absorb calcium and keeps bones strong.",
    },
    {
        "canonical_name": "vitamin_b12",
        "display_name": "Vitamin B12",
        "category": "Vitamins",
        "default_unit": "pg/mL",
        "description": "A vitamin needed for nerves and for making red blood cells.",
    },
    {
        "canonical_name": "folate",
        "display_name": "Folate",
        "category": "Vitamins",
        "default_unit": "ng/mL",
        "description": "A B vitamin needed to make healthy cells, including red blood cells.",
    },
]


def seed():
    supabase = get_supabase()

    print(f"Seeding {len(TEST_DEFINITIONS)} test definitions...")

    for test in TEST_DEFINITIONS:
        # upsert on canonical_name so re-running is safe
        result = (
            supabase.table("test_definitions")
            .upsert(test, on_conflict="canonical_name")
            .execute()
        )
        name = test["display_name"]
        if result.data:
            print(f"  ✓  {name}")
        else:
            print(f"  ✗  {name} — no data returned")

    print("\nDone.")


if __name__ == "__main__":
    seed()
