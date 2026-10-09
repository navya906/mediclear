# MediClear

## Plain-English Medical Lab Report Translator

MediClear is a healthcare application that helps patients understand laboratory reports in simple language. It supports **PDF, JPG, JPEG, PNG, and scanned reports**, extracts results using text extraction/OCR, compares values with laboratory reference ranges, considers patient history and previous reports, and generates patient-friendly explanations.

> **Disclaimer:** MediClear is an informational tool. It does not diagnose conditions, prescribe treatment, or replace a healthcare professional.

## Tech Stack

### Frontend
- **Framework & Runtime:** [React 18](https://react.dev/) (Single Page Application)
- **Build Tool & Dev Server:** [Vite 5](https://vitejs.dev/)
- **Routing:** [React Router v6](https://reactrouter.com/) (`react-router-dom`)
- **Styling:** [Tailwind CSS v4](https://tailwindcss.com/) & Vanilla CSS with CSS Variables (Modern Glassmorphic UI)
- **Data Visualization & Charts:** Hand-built SVG line chart with hover tooltips for biomarker trends (no charting library)
- **Client SDK:** [@supabase/supabase-js](https://supabase.com/docs/reference/javascript/introduction) (Auth state management & storage integration)

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+) — High-performance asynchronous REST API
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/) (Standard with uvloop)
- **Data Validation & Schemas:** [Pydantic v2](https://docs.pydantic.dev/) (Email & schema validation)
- **Database & Auth Client:** [Supabase Python SDK](https://supabase.com/docs/reference/python/introduction) (PostgREST & Service Role integration)
- **Security & Tokens:** Supabase JWTs, verified on each request through Supabase Auth
- **File Uploads:** `python-multipart`

### Document Processing & OCR
- **PDF Extraction:** [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) — Fast vector text extraction from digital PDF lab reports
- **Optical Character Recognition (OCR):** [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) via [pytesseract](https://pypi.org/project/pytesseract/) — Text extraction from scanned medical images & documents
- **Image Processing:** [Pillow (PIL)](https://python-pillow.org/) — Image pre-processing, contrast enhancement, and format conversion (PNG, JPG, JPEG)
- **Parsing Engine:** Custom multi-regex pattern parser supporting tabular, inline, and key-value lab report layouts
- **Medical Normalizer:** Automated biomarker matching with reference range validation and status classification (`LOW`, `NORMAL`, `HIGH`, `CRITICAL`) for CBC, Lipid, and Thyroid profiles

### Artificial Intelligence & NLP
- **LLM Client:** [OpenAI Python SDK](https://github.com/openai/openai-python) — Configurable for OpenAI, Groq (`openai/gpt-oss-120b`), or any OpenAI-compatible provider
- **Prompt Engineering:** Strict JSON schema generation with clinical safety validation, patient context injection, and diagnostic disclaimer guardrails
- **Fallback Engine:** Rule-based explainer providing baseline biomarker context if an external LLM is offline or unconfigured

### Database, Auth & Storage
- **Database:** [PostgreSQL](https://www.postgresql.org/) (Hosted via Supabase)
- **Security:** Row Level Security (RLS) policies ensuring strict patient data privacy
- **Authentication:** Supabase Auth (JWT-based session authentication with email confirmation)
- **File Storage:** Supabase Storage (Private S3-compatible `lab-reports` bucket with signed URLs)

### DevOps, Containerization & Testing
- **Containers:** [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) (Multi-stage builds: Nginx Alpine for frontend, Debian-based Python + Tesseract for backend)
- **Testing:** [Pytest](https://docs.pytest.org/) (Unit tests for the parser, normalizer, AI safety layer and report pipeline, plus registration endpoint tests)
- **Version Control:** Git & GitHub


## Architecture

```text
React Frontend
      |
      | HTTP / REST
      v
FastAPI Backend
      |
      +---- Supabase Auth
      +---- PostgreSQL
      +---- Supabase Storage
      |
      +---- OCR -> Parser -> Validation
      |
      +---- AI -> Safety Validation
      |
      v
Patient Dashboard
```

## Database

The **Supabase project and PostgreSQL database are already created**. All team members must use the same Supabase project.

```text
auth.users
    |
patients
    |
    +-- patient_history
    |
    +-- reports
          |
          +-- lab_results
                |
                +-- test_definitions
                +-- explanations
```

Uploaded reports are stored in the private Supabase Storage bucket:

```text
lab-reports/
    <patient_id>/
        <report_id>/
            report.pdf
```

The database stores the file's `storage_path`, not the actual file.

## Connecting a New PC

### 1. Clone the repository

```bash
git clone <REPOSITORY_URL>
cd mediclear
```

### 2. Get shared Supabase credentials

The project owner must privately provide:

```text
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_KEY   (backend only)
```

These credentials point to the **existing shared Supabase project**.

Do NOT create another Supabase project or recreate the database.

### 3. Configure Backend

Create:

```text
backend/.env
```

Copy `.env.example` from the repo root to `backend/.env` and fill it in:

```env
SUPABASE_URL=<shared-supabase-url>
SUPABASE_ANON_KEY=<shared-anon-key>
SUPABASE_SERVICE_KEY=<shared-service-role-key>
AI_API_KEY=<your-ai-key>
```

See [Full Environment Variable Reference](#full-environment-variable-reference) for the optional settings.

### 4. Configure Frontend

Create:

```text
frontend/.env.local
```

Add:

```env
VITE_SUPABASE_URL=<shared-supabase-url>
VITE_SUPABASE_ANON_KEY=<shared-anon-key>
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 5. Backend Setup

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

### 6. Frontend Setup

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

## Environment Rules

Each developer has their own local:

```text
backend/.env
frontend/.env.local
```

These files must **never** be committed.

Never commit:

- API keys
- Supabase service-role keys
- `.env` files
- Patient information
- Medical reports

The repository contains `.env.example` only.

The Supabase **service-role key must never be used in the frontend**.

## Team Responsibilities

| Member | 
|---|---|
| **Navya Ghatta** 
| **Anup Chalmale** 
| **Ishita Anant** 


## Git Workflow

```bash
git checkout dev
git pull
git checkout -b feature/your-feature
```

After changes:

```bash
git add .
git commit -m "Describe change"
git push -u origin feature/your-feature
```

Create a Pull Request into `dev`. Keep `main` stable.

## Development Pipeline

```text
Upload
  ↓
PDF/Image Processing
  ↓
OCR / Text Extraction
  ↓
Parser
  ↓
Normalization
  ↓
Reference Range Analysis
  ↓
Patient History + Previous Reports
  ↓
AI Explanation
  ↓
Safety Validation
  ↓
Dashboard
```

Initial laboratory support:

- CBC
- Lipid Profile
- Thyroid Profile

## Project Structure

```text
mediclear/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   ├── api/
│   │   ├── database/
│   │   ├── models/
│   │   ├── ocr/
│   │   ├── parser/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── .env
│   └── requirements.txt
├── frontend/
│   ├── public/
│   └── src/
├── data/
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

## Important

**One GitHub repository + one shared Supabase project + one shared database schema.**

Every developer uses their own PC, local environment, virtual environment, and `.env` files, but all development instances connect to the same Supabase project.

---

## Running with Docker (optional)

Requires Docker Desktop installed.

```bash
# From the repo root
docker-compose up --build
```

| Service  | URL                     |
|----------|-------------------------|
| Backend  | http://localhost:8000   |
| Frontend | http://localhost:3000   |
| API docs | http://localhost:8000/docs |

The backend reads `backend/.env` automatically via `env_file` in docker-compose.

---

## Running Tests

From the `backend/` directory with the virtual environment active:

```powershell
pip install -r requirements-dev.txt
pytest -v
```

The tests need no network or Supabase connection.

Current test coverage:
- `tests/test_parser.py` — lab text extraction: comma-grouped values, units with digits, one-sided ranges, metadata lines
- `tests/test_normalizer.py` — status logic (LOW/NORMAL/HIGH/CRITICAL, one-sided ranges), test name matching, fallback ranges and unit checks
- `tests/test_ai.py` — AI safety filter, patient context in prompts, explanation reuse and regeneration
- `tests/test_report_service.py` — sex-specific ranges, saving lab results with and without the `needs_review` column
- `tests/test_auth_api.py` — `POST /auth/register`: duplicate emails, rollback, validation

Not yet covered: OCR, the remaining API endpoints, and the frontend.

---

## Database Migrations

Schema changes made after the initial setup live in `data/migrations/`, numbered in the order they must be applied. Run each one once in the **Supabase SQL Editor** for the shared project (they are safe to re-run):

| Migration | What it does |
|---|---|
| `001_lab_results_needs_review.sql` | Adds `lab_results.needs_review` so uncertain results are flagged per row |

When you add a migration, add a row here and tell the team so nobody's code expects a column that isn't there yet.

---

## Full Environment Variable Reference

### `backend/.env`

| Variable              | Required | Description                                              |
|-----------------------|----------|----------------------------------------------------------|
| `SUPABASE_URL`        | ✅        | Supabase project URL                                     |
| `SUPABASE_ANON_KEY`   | ✅        | Supabase anon/public key (the backend won't start without it) |
| `SUPABASE_SERVICE_KEY`| recommended | Service-role key (backend only, never frontend). Without it the backend uses the anon key, so writes blocked by Row Level Security fail and failed registrations can't be rolled back |
| `AI_API_KEY`          | optional | OpenAI (or compatible) API key; without it explanations use a basic fallback text |
| `AI_BASE_URL`         | optional | AI API base URL (default: `https://api.openai.com/v1`)   |
| `AI_MODEL`            | optional | Model name (default: `gpt-3.5-turbo`)                    |
| `CORS_ALLOW_ORIGINS`  | optional | Comma-separated allowed origins (default: localhost:3000) |

### `frontend/.env.local`

| Variable                | Required | Description                        |
|-------------------------|----------|------------------------------------|
| `VITE_SUPABASE_URL`     | ✅        | Supabase project URL               |
| `VITE_SUPABASE_ANON_KEY`| ✅        | Supabase anon/public key           |
| `VITE_API_BASE_URL`     | optional | Backend URL (default: `http://127.0.0.1:8000`) |
