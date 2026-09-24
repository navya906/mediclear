# MediClear — Architecture Documentation

> Suitable for college project presentation

---

## Overview

MediClear is a full-stack web application that lets patients upload medical lab reports and receive plain-English explanations of their results. The system combines OCR (text extraction from images/PDFs), a structured PostgreSQL database, and an AI language model to translate medical jargon into something a patient can actually understand.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React + Vite + Tailwind CSS + Recharts |
| **Backend** | Python + FastAPI |
| **Database** | PostgreSQL via Supabase |
| **Authentication** | Supabase Auth |
| **File Storage** | Supabase Storage |
| **OCR** | Tesseract / EasyOCR |
| **AI** | LLM API (OpenAI-compatible) |
| **Version Control** | Git + GitHub |

---

## High-Level Architecture

```
                         ┌─────────────────────┐
                         │       PATIENT       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │     React + Vite UI       │
                    │  Login / Upload / History │
                    │  Dashboard / Trends       │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │       FastAPI Backend     │
                    │                           │
                    │  Authentication           │
                    │  Report Processing        │
                    │  History Management       │
                    │  Lab Result Processing    │
                    └─────────────┬─────────────┘
                                  │
             ┌────────────────────┼────────────────────┐
             │                    │                    │
             ▼                    ▼                    ▼
   ┌────────────────┐   ┌─────────────────┐   ┌─────────────────┐
   │ Supabase       │   │ OCR + Parser    │   │ AI Layer        │
   │ Storage        │   │                 │   │                 │
   │                │   │ Tesseract /     │   │ Claude / Gemini │
   │ Medical PDFs   │   │ EasyOCR         │   │                 │
   │ JPG / PNG      │   │                 │   │ Plain-English   │
   └────────────────┘   └────────┬────────┘   │ explanations    │
                                 │            └────────┬────────┘
                                 ▼                     │
                       ┌──────────────────┐            │
                       │ Lab Result        │◄───────────┘
                       │ Extraction        │
                       └────────┬─────────┘
                                │
                                ▼
                    ┌──────────────────────────┐
                    │ PostgreSQL / Supabase    │
                    │                          │
                    │ patients                 │
                    │ patient_history          │
                    │ reports                  │
                    │ test_definitions         │
                    │ lab_results              │
                    │ explanations             │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Patient Dashboard   │
                    │                          │
                    │ • Plain-English results  │
                    │ • High/Low indicators    │
                    │ • Historical trends      │
                    │ • Report history         │
                    │ • Doctor questions       │
                    └──────────────────────────┘
```

---

## Component Breakdown

### 1. React Frontend

The user-facing web interface. Built with **React + Vite** for fast development and hot reloading.

**Key responsibilities:**
- Login / signup via Supabase Auth (JWT handled automatically)
- File upload form (PDF, JPG, JPEG, PNG, scanned documents)
- Patient dashboard showing all uploaded reports
- Per-report view: individual lab results with color-coded status (low / normal / high) and AI explanations
- Charts for trending values across multiple reports (using Recharts)

**Communicates with:**
- FastAPI backend over REST (`VITE_API_BASE_URL`)
- Supabase Auth directly for session management

---

### 2. FastAPI Backend

The Python backend that orchestrates all processing. It is a **REST API** that the frontend calls.

**Key responsibilities:**
- Verify the user's JWT token (issued by Supabase Auth) on every request
- Accept uploaded files and save them to Supabase Storage
- Create records in PostgreSQL (`reports`, `lab_results`, `explanations`)
- Run the **OCR → Parser → AI pipeline** (either synchronously or as a background task)
- Return structured JSON to the frontend

**Internal modules:**

| Module | Responsibility |
|---|---|
| `api/` | Route definitions (upload, results, auth, patients) |
| `ocr/` | Tesseract / EasyOCR integration; extracts raw text from files |
| `parser/` | Finds test names and numeric values in raw text |
| `models/` | SQLAlchemy / Pydantic data models |
| `schemas/` | Request/response schemas for the API |
| `services/` | Business logic (report processing, explanation generation) |
| `ai/` | Prompt construction, LLM API call, safety filtering |
| `database/` | Supabase client and database connection helpers |
| `utils/` | Shared utilities |

---

### 3. Supabase Auth

Handles user **signup and login** without the team needing to build an authentication system from scratch.

- Supports email + password login
- Issues a **JWT (JSON Web Token)** on successful login
- The frontend stores and sends this token with every API request
- The backend verifies the token before processing any request
- Supabase also maintains the `auth.users` table, which the `patients` table references

---

### 4. PostgreSQL Database (via Supabase)

A shared, cloud-hosted **PostgreSQL** database. All team members connect to the same Supabase project.

Six main tables store all structured data:

```
auth.users → patients → patient_history
                    └──→ reports → lab_results → explanations
                                        └──→ test_definitions
```

**Row Level Security (RLS)** is enabled on all tables so patients can only access their own data.

See [`database.md`](./database.md) for the full schema breakdown.

---

### 5. Supabase Storage

A private file storage service for the actual report files (PDFs, images).

```
lab-reports/
  <patient_id>/
    <report_id>/
      report.pdf
```

- Files are stored in the **`lab-reports`** bucket (private — not publicly accessible)
- The backend generates **signed URLs** to retrieve files securely
- The PostgreSQL `reports` table stores only the `storage_path` (a text string), not the file itself

---

### 6. OCR Pipeline

Extracts text from uploaded files before the parser and AI can work on them.

```
Uploaded file
      │
      ├── PDF?  → Extract text layer with PyMuPDF / pdfminer
      │            └── If text layer is empty → fall back to OCR
      │
      └── Image (JPG/PNG)? → Tesseract or EasyOCR
                              └── Returns raw text string
```

The OCR output is raw, unstructured text — the parser step cleans it up.

---

### 7. Parser + Normalizer

Converts raw OCR text into structured data.

**Steps:**
1. Identify test names (e.g., "Hemoglobin", "TSH", "LDL Cholesterol")
2. Extract associated numeric values and units
3. Match each test to a `test_definitions` record for the reference range
4. Flag each result as `low`, `normal`, or `high`
5. Save each result as a row in `lab_results`

---

### 8. AI Explanation Generator

Takes a structured lab result and generates a plain-English explanation for the patient.

**Input to the AI model:**
- Test name and value
- Whether it is low, normal, or high
- Normal reference range
- Patient's medical history (conditions, medications) from `patient_history`
- Previous results for the same test (for trend context)

**Output:**
- A short, friendly paragraph that a non-medical person can understand
- Severity rating (`normal`, `mild`, `moderate`, `severe`)

The explanation is then passed through a **safety validator** that removes any diagnostic claims or treatment recommendations before it is stored and shown to the patient.

---

## Data Flow — End to End

```
User logs in
      │
      ▼
Supabase Auth issues JWT
      │
      ▼
Patient uploads report (PDF / image)
      │
      ├── File saved to Supabase Storage (lab-reports bucket)
      ├── reports row created in PostgreSQL (status = "pending")
      │
      ▼
Backend processes file
      │
      ├── OCR extracts raw text
      ├── Parser identifies test names and values
      ├── Values matched to test_definitions (reference ranges)
      ├── lab_results rows saved (one per test)
      │
      ▼
AI generates explanations
      │
      ├── One explanation per lab_result
      ├── Safety validator filters output
      ├── explanations rows saved in PostgreSQL
      │
      ▼
Frontend fetches data for dashboard
      │
      ├── Reports list
      ├── Lab results (with low/normal/high status)
      ├── Plain-English explanations
      └── Charts for historical trends
```

---

## Security Considerations

| Risk | Mitigation |
|---|---|
| Unauthorized data access | Row Level Security on all PostgreSQL tables |
| Exposed API keys | Keys stored in `.env` files, never committed to Git |
| Insecure file access | Supabase Storage bucket is private; signed URLs used |
| Frontend misusing service-role key | Only anon key used in frontend; service-role key stays server-side |
| AI giving medical advice | Safety validator strips diagnostic / treatment language |

---

## Development Setup Summary

| Service | URL |
|---|---|
| Frontend | `http://localhost:5173` |
| Backend API | `http://127.0.0.1:8000` |
| API Docs (Swagger) | `http://127.0.0.1:8000/docs` |
| Database | Shared Supabase PostgreSQL project |

All developers share **one Supabase project** and use their own local `.env` files to connect to it.
