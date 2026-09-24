# MediClear

## Plain-English Medical Lab Report Translator

MediClear is a healthcare application that helps patients understand laboratory reports in simple language. It supports **PDF, JPG, JPEG, PNG, and scanned reports**, extracts results using text extraction/OCR, compares values with laboratory reference ranges, considers patient history and previous reports, and generates patient-friendly explanations.

> **Disclaimer:** MediClear is an informational tool. It does not diagnose conditions, prescribe treatment, or replace a healthcare professional.

## Tech Stack

- Frontend: React + Vite + Tailwind CSS + Recharts
- Backend: Python + FastAPI
- Database: PostgreSQL via Supabase
- Authentication: Supabase Auth
- Storage: Supabase Storage
- OCR: Tesseract / EasyOCR
- AI: LLM API
- Version Control: Git + GitHub

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
```

These credentials point to the **existing shared Supabase project**.

Do NOT create another Supabase project or recreate the database.

### 3. Configure Backend

Create:

```text
backend/.env
```

Add:

```env
SUPABASE_URL=<shared-supabase-url>
SUPABASE_ANON_KEY=<shared-anon-key>
AI_API_KEY=<your-ai-key>
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
```

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
http://localhost:5173
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
pip install pytest
pytest tests/ -v
```

Current test coverage:
- `tests/test_parser.py` — lab text extraction (inline, colon, no-ref patterns)
- `tests/test_normalizer.py` — status logic (LOW/NORMAL/HIGH/CRITICAL), fuzzy matching, fallback ranges

---

## Full Environment Variable Reference

### `backend/.env`

| Variable              | Required | Description                                              |
|-----------------------|----------|----------------------------------------------------------|
| `SUPABASE_URL`        | ✅        | Supabase project URL                                     |
| `SUPABASE_SERVICE_KEY`| ✅        | Supabase service-role key (backend only, never frontend) |
| `JWT_SECRET`          | ✅        | Supabase JWT secret (from project settings)              |
| `AI_API_KEY`          | optional | OpenAI (or compatible) API key for AI explanations       |
| `AI_BASE_URL`         | optional | AI API base URL (default: `https://api.openai.com/v1`)   |
| `AI_MODEL`            | optional | Model name (default: `gpt-3.5-turbo`)                    |
| `CORS_ALLOW_ORIGINS`  | optional | Comma-separated allowed origins (default: localhost:5173) |

### `frontend/.env.local`

| Variable                | Required | Description                        |
|-------------------------|----------|------------------------------------|
| `VITE_SUPABASE_URL`     | ✅        | Supabase project URL               |
| `VITE_SUPABASE_ANON_KEY`| ✅        | Supabase anon/public key           |
| `VITE_API_BASE_URL`     | optional | Backend URL (default: `http://127.0.0.1:8000`) |