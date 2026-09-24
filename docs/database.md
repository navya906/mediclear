# MediClear — Database Documentation

> Suitable for college project presentation

---

## Overview

MediClear uses **PostgreSQL** hosted on **Supabase**. All team members share one Supabase project and one database. The database is organized into **six main tables**, each with a clear, focused responsibility.

File storage (actual PDFs/images) is handled separately by **Supabase Storage**, while the database only stores metadata and file paths — keeping the database lean and fast.

---

## Tables at a Glance

| Table | What it stores |
|---|---|
| `patients` | Patient profile linked to the logged-in user |
| `patient_history` | Individual medical history entries (conditions, medications, allergies, etc.) |
| `reports` | Metadata of each uploaded lab report file |
| `test_definitions` | Standard reference data for lab tests (canonical name, unit, category) |
| `lab_results` | Individual test values extracted from a report |
| `explanations` | AI-generated plain-English explanation for each lab result |

---

## Table Details

### 1. `patients`

Stores the personal profile of every registered patient.

**Key columns:**

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` PK | Unique patient identifier |
| `auth_user_id` | `uuid` FK → `auth.users.id` | Links to Supabase Auth (unique per user) |
| `date_of_birth` | `date` | Patient's date of birth |
| `sex` | `text` | One of: `male`, `female`, `other`, `prefer_not_to_say` |
| `created_at` | `timestamptz` | When the profile was created |
| `updated_at` | `timestamptz` | Last updated timestamp |

**How it connects to authentication:**
When a user signs up, Supabase Auth creates a record in the built-in `auth.users` table and issues a unique UUID. The `patients` table stores that same UUID as `auth_user_id` (with a `UNIQUE` constraint and foreign key), so every patient profile is tied to exactly one authenticated account — and one user can never have two profiles.

---

### 2. `patient_history`

Stores individual medical history entries for a patient. Instead of storing arrays, each piece of history is its own row with a `category` tag. This makes the data easy to filter, update, and extend.

**Key columns:**

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` PK | Unique history entry identifier |
| `patient_id` | `uuid` FK → `patients.id` | Which patient this belongs to |
| `category` | `text` | One of: `condition`, `medication`, `allergy`, `symptom`, `surgery`, `family_history`, `other` |
| `title` | `text` | Short label (e.g., `"Type 2 Diabetes"`, `"Metformin"`) |
| `description` | `text` | Detailed description of the entry |
| `start_date` | `date` | When this condition / medication started (optional) |
| `end_date` | `date` | When it ended — `NULL` means it is ongoing (optional) |
| `created_at` | `timestamptz` | When this entry was created |
| `updated_at` | `timestamptz` | Last updated timestamp |

**Example rows for one patient:**

| category | title | description |
|---|---|---|
| `condition` | Type 2 Diabetes | Diagnosed 2019 |
| `medication` | Metformin | 500 mg twice daily |
| `allergy` | Penicillin | Causes rash |
| `surgery` | Appendectomy | 2015 |

---

### 3. `reports`

Every time a patient uploads a lab report file, a record is created in this table. The actual file lives in Supabase Storage; this table stores only the metadata.

**Key columns:**

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` PK | Unique report identifier |
| `patient_id` | `uuid` FK → `patients.id` | Which patient uploaded this |
| `file_name` | `text` | Original file name (e.g., `bloodwork_june.pdf`) |
| `file_type` | `text` | One of: `pdf`, `jpg`, `jpeg`, `png` |
| `storage_path` | `text` | Path in the Supabase Storage bucket |
| `report_date` | `date` | Date printed on the lab report (optional) |
| `processing_status` | `text` | One of: `uploaded`, `processing`, `completed`, `failed`, `needs_review` |
| `error_message` | `text` | Error details if processing failed (optional) |
| `created_at` | `timestamptz` | Upload timestamp |
| `updated_at` | `timestamptz` | Last status change timestamp |

**Processing status lifecycle:**
```
uploaded → processing → completed
                     ↘ failed
                     ↘ needs_review
```

**Storage path format:**
```
lab-reports/<patient_id>/<report_id>/report.pdf
```

The `storage_path` column stores this path so the backend can retrieve the file from the private `lab-reports` bucket when needed.

---

### 4. `test_definitions`

A **reference / lookup table** that standardizes lab test information. Instead of repeating test names and units in every result row, they are stored once here and referenced by ID.

**Key columns:**

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` PK | Unique test identifier |
| `canonical_name` | `text` UNIQUE | Machine-readable standard name (e.g., `hemoglobin`, `tsh`) |
| `display_name` | `text` | Human-readable name (e.g., `Hemoglobin`, `TSH`) |
| `category` | `text` | Test panel (e.g., `CBC`, `Lipid Profile`, `Thyroid`) |
| `default_unit` | `text` | Default unit of measurement (e.g., `g/dL`, `mIU/L`) |
| `description` | `text` | Plain-English description of what the test measures |
| `created_at` | `timestamptz` | When this definition was added |

> **Note:** Reference ranges (normal min/max) are **not** stored here — they are stored per result in `lab_results` because reference ranges vary by lab, age, and sex. `test_definitions` is a stable dictionary of *what* the test is, not *what is normal*.

This table acts like a dictionary: when a lab result is extracted from a report, the parser matches the raw test name to a `canonical_name` here to get the standardized `display_name`, `category`, and `default_unit`.

---

### 5. `lab_results`

Stores each individual test result extracted from an uploaded report. One report produces many lab results — **one row per test**.

**Key columns:**

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` PK | Unique result identifier |
| `report_id` | `uuid` FK → `reports.id` | Which report this result came from |
| `test_definition_id` | `uuid` FK → `test_definitions.id` | Matched standard test (nullable — may be unmatched) |
| `test_name_raw` | `text` | The test name exactly as it appeared in the report |
| `value` | `numeric` | The extracted numeric value |
| `unit` | `text` | Unit as printed in the report |
| `reference_min` | `numeric` | Lower bound of the reference range from this report |
| `reference_max` | `numeric` | Upper bound of the reference range from this report |
| `reference_text` | `text` | Reference range as raw text (e.g., `"3.5 - 5.0"`) |
| `status` | `text` | One of: `LOW`, `HIGH`, `NORMAL`, `CRITICAL`, `UNKNOWN` |
| `extraction_confidence` | `numeric` | OCR confidence score (0.0 – 1.0) |
| `created_at` | `timestamptz` | When the result was extracted |

**Key design decisions:**
- `test_name_raw` always preserves the original text from the report, even if matching to `test_definitions` fails.
- `test_definition_id` is **nullable** — if the parser cannot confidently match a test name to a known definition, the result is still stored without a match.
- `reference_min` / `reference_max` come from the report itself (not from `test_definitions`) because lab-printed ranges vary.
- `extraction_confidence` lets the system flag low-confidence extractions for human review (`needs_review` status on the report).

**How `reports` connects to `lab_results`:**
After a file is uploaded (`reports`), the backend runs OCR/text extraction on it and identifies individual test values. Each value is saved as a separate row in `lab_results`, with `report_id` pointing back to the source report.

---

### 6. `explanations`

Stores the AI-generated plain-English explanation for each lab result. One `lab_result` has one `explanation`.

**Key columns:**

| Column | Type | Description |
|---|---|---|
| `id` | `uuid` PK | Unique explanation identifier |
| `lab_result_id` | `uuid` FK → `lab_results.id` | The result this explains |
| `language` | `text` | Language code (default `en`) |
| `simple_explanation` | `text` | A plain sentence about the result (e.g., *"Your hemoglobin is slightly low."*) |
| `why_it_matters` | `text` | Why this test is important for health |
| `possible_reasons` | `jsonb` | JSON array of possible reasons for an abnormal result |
| `doctor_questions` | `jsonb` | JSON array of suggested questions to ask a doctor |
| `model` | `text` | Which AI model generated this explanation |
| `prompt_version` | `text` | Version of the prompt template used (for reproducibility) |
| `created_at` | `timestamptz` | When the AI generated this |

**Example `possible_reasons` value:**
```json
["Iron deficiency", "Vitamin B12 deficiency", "Chronic inflammation"]
```

**Example `doctor_questions` value:**
```json
["Should I take an iron supplement?", "Do I need further blood tests?"]
```

Storing `model` and `prompt_version` means the team can trace exactly which AI setup produced any given explanation — useful for debugging and iterating on the AI prompts.

---

## Relationships Diagram

```
auth.users
    │
    │  auth_user_id (unique FK)
    ▼
patients ──────────────────────── patient_history (many rows, one per entry)
    │
    │  patient_id
    ▼
reports
    │
    │  report_id
    ▼
lab_results ──────── test_definitions (nullable FK — may be unmatched)
    │
    │  lab_result_id
    ▼
explanations
```

---

## File Storage — Supabase Storage

Medical report files (PDFs, images) are **not** stored in PostgreSQL. They are stored in a **private Supabase Storage bucket** called `lab-reports`.

```
lab-reports/              ← private bucket (not publicly accessible)
  <patient_id>/
    <report_id>/
      report.pdf
```

- **PostgreSQL** (`reports.storage_path`) stores the text path to the file.
- **Supabase Storage** holds the actual binary file.
- The backend generates a **signed URL** to read or display a file securely — patients cannot access files directly through a public URL.

This separation keeps the database fast (no binary blobs) and file retrieval secure.

---

## Row Level Security (RLS)

Supabase enforces **Row Level Security** on all tables. Each table has an RLS policy that checks the authenticated user's ID against the `auth_user_id` / `patient_id` chain.

**Effect:** A patient can only read and write their own data. Even if someone obtained the API key, they cannot access another patient's records, reports, or results.

Example policy (simplified):
```sql
-- Patients can only select their own row
CREATE POLICY "Patients select own row"
ON patients
FOR SELECT
USING (auth_user_id = auth.uid());
```

All downstream tables (`patient_history`, `reports`, `lab_results`, `explanations`) inherit the same privacy guarantee through their `patient_id` or `report_id` chain.

---

## Complete Data Flow

This is the end-to-end journey of data through the system:

```
1. User Authentication
   └─ User signs up / logs in via Supabase Auth
   └─ auth.users record is created / verified
   └─ JWT token issued to the frontend

2. Patient Profile
   └─ A patients row is created, auth_user_id = auth.uid()
   └─ Patient fills in medical history
   └─ Each item (condition, medication, allergy…) → one patient_history row

3. Report Upload
   └─ Patient uploads a PDF or image from the frontend
   └─ File is saved to Supabase Storage (lab-reports bucket)
   └─ A reports row is created with storage_path and processing_status = "uploaded"

4. OCR / Parsing (Backend)
   └─ Backend sets processing_status = "processing"
   └─ Retrieves the file from Supabase Storage via signed URL
   └─ Tesseract / EasyOCR extracts raw text from the file
   └─ Parser identifies test names (stored in test_name_raw) and numeric values
   └─ Each test name is matched to a test_definitions canonical_name (if possible)
   └─ reference_min / reference_max are read from the report's own printed ranges

5. Lab Results Stored
   └─ Each extracted test value → one lab_results row
   └─ status is set to LOW / HIGH / NORMAL / CRITICAL / UNKNOWN
   └─ extraction_confidence recorded; low-confidence results may trigger needs_review
   └─ processing_status on reports updated to "completed" (or "failed" / "needs_review")

6. AI Explanation Generated
   └─ AI model receives: lab result + test_definition description + patient_history entries
   └─ Generates: simple_explanation, why_it_matters, possible_reasons, doctor_questions
   └─ model and prompt_version are recorded for traceability
   └─ Explanation saved to explanations table (one row per lab_results row)

7. Dashboard
   └─ Frontend fetches reports, lab_results, and explanations for the patient
   └─ Patient sees results with plain-English summaries and color-coded status
   └─ Suggested doctor questions are displayed per result
   └─ Historical results are available for trend comparison across reports
```

---

## Summary

| Concern | Solution |
|---|---|
| User identity | Supabase Auth (`auth.users`) |
| Patient profile | `patients` table linked by `auth_user_id` |
| Medical background | `patient_history` table (one row per entry, categorized) |
| Report metadata | `reports` table with `processing_status` lifecycle |
| Actual report files | Supabase Storage (`lab-reports` private bucket) |
| Standardized test info | `test_definitions` table (`canonical_name` + `display_name`) |
| Extracted test values | `lab_results` table (with per-report reference ranges) |
| AI explanations | `explanations` table (with `possible_reasons` + `doctor_questions` as JSON) |
| Data privacy | Row Level Security (RLS) on all tables |
