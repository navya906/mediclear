"""
Seed test_definitions table with standard tests for CBC, Lipid Profile, and Thyroid Profile.

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
