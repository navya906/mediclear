# MediClear — Development Phases

> College project development plan divided into three structured phases.

---

## Overview

The project is divided into **three phases**, each building on top of the previous one. Every phase ends with something testable and demonstrable.

```
Phase 1: Foundation
  └─ Auth + Patient profile + Patient history + Project skeleton

Phase 2: Core Pipeline
  └─ Report upload + OCR + Parser + Lab results + test_definitions

Phase 3: AI & Dashboard
  └─ AI explanations + Safety validation + Dashboard + Trends
```

---

## Phase 1 — Foundation

**Goal:** Users can sign up, log in, create their patient profile, and manage their medical history. No report processing yet — just the backbone of the app.

### Backend Tasks

| Task | Details |
|---|---|
| Project setup | FastAPI app skeleton, folder structure, `requirements.txt`, `uvicorn` runner |
| Supabase client | Connect to shared Supabase project using `.env` credentials |
| Auth middleware | Verify Supabase JWT on every protected route |
| `POST /auth/register` | Create `auth.users` entry + insert a `patients` row |
| `GET /patients/me` | Return the logged-in patient's profile |
| `PATCH /patients/me` | Update `date_of_birth`, `sex` |
| Patient history CRUD | `POST`, `GET`, `PATCH`, `DELETE` for `patient_history` rows |
| RLS verification | Confirm Row Level Security blocks cross-patient access |

### Frontend Tasks

| Task | Details |
|---|---|
| Project setup | React + Vite + Tailwind CSS scaffold, routing |
| Login page | Email + password login via Supabase Auth JS client |
| Signup page | Registration form → triggers backend `/auth/register` |
| Auth guard | Redirect unauthenticated users to login |
| Profile page | View and edit `date_of_birth`, `sex` |
| Medical history page | Add / view / delete history entries by category |

### Database Tasks

| Task | Details |
|---|---|
| Seed `test_definitions` | Populate standard tests for CBC, Lipid Profile, Thyroid Profile |
| Verify RLS policies | All six tables locked to `auth.uid()` |

### Phase 1 Deliverable

> A working login/signup flow where a patient can create their profile and add medical history entries. No file upload yet.

---

## Phase 2 — Core Pipeline

**Goal:** Patients can upload a lab report (PDF, JPG, JPEG, PNG). The system extracts text using OCR, parses individual test results, matches them to `test_definitions`, and stores structured `lab_results` rows.

### Backend Tasks

| Task | Details |
|---|---|
| `POST /reports/upload` | Accept file → save to Supabase Storage → create `reports` row (`processing_status = "uploaded"`) |
| `GET /reports` | List all reports for the logged-in patient |
| `GET /reports/{id}` | Return a single report's metadata and status |
| OCR module | Detect file type; use PyMuPDF for text PDFs; fall back to Tesseract / EasyOCR for images and scanned PDFs |
| Parser module | Extract test name (`test_name_raw`), numeric value, unit, and reference range from raw OCR text |
| Normalizer | Match `test_name_raw` to `test_definitions.canonical_name`; set `test_definition_id` (or leave `NULL` if unmatched) |
| Status logic | Compute `LOW` / `HIGH` / `NORMAL` / `CRITICAL` by comparing `value` to `reference_min` / `reference_max`; flag low-confidence extractions as `needs_review` |
| `GET /reports/{id}/results` | Return all `lab_results` for a report |
| Background processing | Run OCR → Parser → Save pipeline after upload (async task or background thread) |
| Error handling | Set `processing_status = "failed"` with `error_message` on exceptions |

### Frontend Tasks

| Task | Details |
|---|---|
| Upload page | Drag-and-drop or file picker for PDF / JPG / JPEG / PNG |
| Upload progress | Show `processing_status` with polling or real-time update |
| Reports list | Show all uploaded reports with status badges |
| Results view | List extracted `lab_results` for a report — test name, value, unit, status badge (LOW / HIGH / NORMAL / CRITICAL) |

### Phase 2 Deliverable

> A patient can upload a blood report and see a table of extracted test values with colour-coded LOW / NORMAL / HIGH status labels. No AI explanations yet.

---

## Phase 3 — AI & Dashboard

**Goal:** Every lab result gets a plain-English AI explanation. The patient dashboard shows results, explanations, suggested doctor questions, and historical trend charts across multiple reports.

### Backend Tasks

| Task | Details |
|---|---|
| AI module | Build prompt using `lab_results` + `test_definitions.description` + `patient_history` entries + previous values for the same test |
| `POST /results/{id}/explain` | Call AI API, run safety validator, save to `explanations` table |
| Batch explanation | After pipeline completes, auto-generate explanations for all results in a report |
| Safety validator | Strip any diagnostic claims, treatment prescriptions, or definitive disease statements from AI output |
| `GET /results/{id}/explanation` | Return the `explanations` row for a result |
| Trends endpoint | `GET /patients/me/trends?test=hemoglobin` — return historical values across reports |

### Frontend Tasks

| Task | Details |
|---|---|
| Explanation cards | For each lab result: show `simple_explanation`, `why_it_matters`, `possible_reasons`, `doctor_questions` |
| Dashboard page | Summary view of the most recent report's results |
| Historical trends | Line charts (Recharts) showing value over time per test |
| Report history | List of past reports with date and summary |
| Disclaimer banner | Display the "informational tool only" disclaimer on all result pages |

### Phase 3 Deliverable

> The complete, working application: a patient can upload a report, see colour-coded results, read plain-English AI explanations, get suggested doctor questions, and view trends from previous reports.

---

## Summary Timeline

| Phase | Focus | Ends With |
|---|---|---|
| **Phase 1** | Foundation — Auth, profiles, medical history | Working login + patient history UI |
| **Phase 2** | Core pipeline — Upload, OCR, parsing, lab results | Working upload + results table |
| **Phase 3** | AI & dashboard — Explanations, trends, polish | Full working application |

---

## Supported Lab Tests (All Phases)

Initial `test_definitions` coverage (seeded in Phase 1):

| Panel | Examples |
|---|---|
| **CBC** | Hemoglobin, WBC, RBC, Platelets, Hematocrit |
| **Lipid Profile** | Total Cholesterol, LDL, HDL, Triglycerides |
| **Thyroid Profile** | TSH, Free T3, Free T4 |
