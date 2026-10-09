# MediClear Progress Tracker

_Last updated: 2026-10-09_

---

## Phase 1: Foundation ✅ COMPLETED

**Backend Tasks:**
- [x] Project setup (`requirements.txt`, `app/main.py`)
- [x] Supabase client (`app/database/client.py`)
- [x] Auth middleware (`app/utils/auth.py`)
- [x] `POST /auth/register` (`app/api/auth.py`)
- [x] `GET /patients/me`, `PATCH /patients/me` (`app/api/patients.py`)
- [x] Patient history CRUD (`app/api/history.py`)
- [x] Schemas (`app/schemas/patient.py`, `app/schemas/history.py`)
- [x] Seed script (`data/seed_test_definitions.py`)

**Frontend Tasks:**
- [x] Project setup (`package.json`, `vite.config.js`, `index.html`)
- [x] Global CSS (`src/index.css`)
- [x] API & Supabase services (`src/services/api.js`, `src/services/supabase.js`)
- [x] Auth Hook (`src/hooks/useAuth.js`)
- [x] Routing & AuthGuard (`src/App.jsx`, `src/main.jsx`, `src/components/AuthGuard.jsx`)
- [x] Login page (`src/pages/LoginPage.jsx`)
- [x] Signup page (`src/pages/SignupPage.jsx`)
- [x] Profile page (`src/pages/ProfilePage.jsx`)
- [x] Medical history page (`src/pages/HistoryPage.jsx`)
- [x] Navigation bar (`src/components/NavBar.jsx`)
- [x] `.env.local.example`

> **Note:** `npm install` must be run manually in `frontend/` before starting the dev server.

---

## Phase 2: Core Pipeline ✅ COMPLETED

**Backend Tasks:**
- [x] Dependencies (`PyMuPDF`, `pytesseract`, `Pillow`, `python-multipart` added to `requirements.txt`)
- [x] Schemas (`app/schemas/report.py`, `app/schemas/result.py`)
- [x] OCR extraction module (`app/ocr/core.py`) — PyMuPDF text extraction with Tesseract image/scanned-PDF fallback
- [x] Regex parser + normalizer in `app/parser/core.py` — extracts test name, value, unit, reference range; computes LOW / NORMAL / HIGH status
- [x] Reports endpoints (`app/api/reports.py`):
  - `POST /reports/upload` — Supabase Storage upload + async background processing
  - `GET /reports` — list patient reports
  - `GET /reports/{id}` — single report status
  - `GET /reports/{id}/results` — extracted lab results with `test_definitions` join
- [x] Background pipeline: OCR → parse → normalize → insert `lab_results` → mark `completed` / `failed`

**Frontend Tasks:**
- [x] Report upload page with file picker and processing-status feedback (`src/pages/UploadPage.jsx`)
- [x] Reports list page with status badges (`src/pages/ReportsPage.jsx`)
- [x] Report details page with structured lab results table (`src/pages/ReportDetailsPage.jsx`)
- [x] Polling mechanism for background processing status

**Stub files created but currently empty:**
- [ ] `app/ocr/pdf.py` — empty (PDF-specific helpers not yet extracted)
- [ ] `app/ocr/image.py` — empty (image-specific helpers not yet extracted)
- [ ] `app/ocr/preprocessing.py` — empty (image enhancement / deskew not yet implemented)
- [ ] `app/parser/parser.py` — empty (expanded parser not yet extracted)
- [ ] `app/parser/normalizer.py` — empty (fuzzy normalizer not yet separated)
- [ ] `app/parser/reference_ranges.py` — empty (fallback range table not yet added)
- [ ] `app/services/report_service.py` — empty (background task not yet moved here)
- [ ] `app/services/history_service.py` — empty (history DB logic not yet extracted)

---

## Phase 3: AI & Dashboard ✅ COMPLETED

**Backend Tasks:**
- [x] Dependency (`openai` added to `requirements.txt`)
- [x] Explanation schema (`app/schemas/explanation.py`)
- [x] AI generator (`app/ai/generator.py`) — prompt building, LLM call, JSON parsing, safety validator
- [x] Explanation endpoints (`app/api/results.py`):
  - `POST /results/{id}/explain` — generate & save AI explanation (idempotent)
  - `GET /results/{id}/explanation` — retrieve existing explanation
- [x] Patient historical trends endpoint: `GET /patients/me/trends?test_name=...` (`app/api/patients.py`)
- [x] Router registrations in `app/api/__init__.py` and `app/main.py`

**Frontend Tasks:**
- [x] AI explanation cards on `ReportDetailsPage.jsx` (simple explanation, why it matters, possible factors, doctor questions)
- [x] Educational / informational-tool-only disclaimer banner
- [x] Health dashboard (`src/pages/DashboardPage.jsx`) — zero-dependency SVG line chart with gradient fill, interactive hover tooltips, and date axis labels
- [x] Trends test selector (Hemoglobin, Total Cholesterol, TSH)
- [x] Recent reports summary panel with direct links
- [x] `/dashboard` route in `src/App.jsx` + NavBar link

**Stub files created but currently empty:**
- [ ] `app/ai/explainer.py` — empty (LLM call logic not yet separated from generator)
- [ ] `app/ai/prompts.py` — empty (prompt templates not yet extracted)

---

## Phase 4: Polish & Robustness ✅ COMPLETED

**Goal:** Fill all empty stubs, harden the pipeline, improve UX, and make the app fully demo-ready.

### Backend Tasks

- [x] Fill `app/ocr/pdf.py` — PDF extraction with native text + scanned-PDF Tesseract fallback
- [x] Fill `app/ocr/image.py` — image extraction delegating to preprocessing pipeline
- [x] Fill `app/ocr/preprocessing.py` — contrast enhancement, sharpening, and noise reduction before Tesseract
- [x] Fill `app/parser/parser.py` — 3-pattern regex (inline, colon, no-ref) with noise filtering and deduplication
- [x] Fill `app/parser/normalizer.py` — exact + token-overlap matching, CRITICAL detection, `needs_review` flag
- [x] Fill `app/parser/reference_ranges.py` — 50+ hard-coded fallback ranges across CBC, Lipid, Thyroid, Liver, Kidney, Glucose, Electrolytes, Vitamins
- [x] Fill `app/ai/prompts.py` — versioned system prompt + parameterised explanation template
- [x] Fill `app/ai/explainer.py` — LLM call logic, safety sanitiser, separated from orchestration
- [x] Fill `app/services/report_service.py` — full background pipeline with auto-explanation batch and logging
- [x] Fill `app/services/history_service.py` — history CRUD service layer extracted from router
- [x] Add `CRITICAL` status for values > 1.5× the reference range width outside the boundary
- [x] Add `needs_review` flag for extractions with confidence < 0.75 or UNKNOWN status _(computed but discarded until the gap fixes below)_
- [x] Auto-generate AI explanations for all results in batch after report processing completes _(saving failed on every insert until the gap fixes below)_
- [x] Add input validation: `validate_file()` rejects files > 10 MB and unsupported types
- [x] Configure CORS `allow_origins` from `CORS_ALLOW_ORIGINS` env variable _(the variable was read but ignored until the gap fixes below)_
- [x] Add startup env-var validation — `main.py` exits with clear error if required keys are missing
- [x] Write unit tests: `tests/test_parser.py`, `tests/test_normalizer.py`

### Frontend Tasks

- [x] Fill `src/utils/helpers.js` — date formatters, status badge helpers, file size, file type validation, truncate
- [x] Fill `src/types/constants.js` — lab statuses, history categories, report states, upload limits, full TREND_TESTS list
- [x] Add drag-and-drop to `UploadPage.jsx` — full drop zone with drag-active state
- [x] Show upload progress bar with animated gradient fill
- [x] Dashboard: trends test selector now uses full 15-test `TREND_TESTS` list from constants
- [x] Dashboard: added "Stats at a Glance" panel (Total Reports, Processed, Trend Points)
- [x] Add `src/pages/NotFoundPage.jsx` — 404 page with back/dashboard navigation
- [x] Register `*` catch-all route to `NotFoundPage` in `App.jsx`
- [x] Improve mobile responsiveness — nav wraps, smaller padding/font on ≤560px
- [x] Replace spinners with skeleton loaders on Dashboard (shimmer animation)
- [x] `error_message` already shown in `ReportsPage.jsx` — confirmed working

### DevOps / Config

- [x] Create `backend/Dockerfile` — Python 3.11 slim with Tesseract + PyMuPDF system deps
- [x] Create `docker-compose.yml` — one-command local full-stack setup (backend:8000, frontend:3000)
- [x] Create `frontend/Dockerfile` — multi-stage build (Node → nginx) with SPA routing config
- [x] Create `frontend/nginx.conf` — SPA fallback for React client-side routing
- [x] Update `README.md` — Docker, pytest, full env variable reference table



---

## Gap Fixes (2026-10-09) ✅ COMPLETED

A review of the repo found several features marked complete above that did not work. Fixed on `navya-dev`:

**Broken features**
- [x] Trends endpoint crashed on every call (invalid `order(asc=True)`), so dashboard charts were always empty
- [x] Missing rows returned HTTP 500 instead of 404 (`.single()` raises on zero rows); replaced with `fetch_one()`
- [x] "HDL Cholesterol" was matched to Total Cholesterol; matcher now prefers the most specific name and knows common abbreviations (Hb, TLC, FT4, PCV…)
- [x] LDL/HDL keys didn't match the seeded names (`ldl_cholesterol` / `hdl_cholesterol`), so they never got fallback ranges or trends
- [x] CORS ignored `CORS_ALLOW_ORIGINS`
- [x] AI explanations failed to save (UUID not JSON-serialisable), and the saved model name was a Python object repr
- [x] Report details page never refreshed while processing (polling read a stale state value)

**Registration**
- [x] Duplicate email returns 409 instead of 500
- [x] Auth user is deleted if the patient profile can't be created
- [x] Server-side 8-character password minimum; friendly "confirm your email" message on login

**Parser & scoring**
- [x] Handles `1,50,000`, units like `10^3/uL`, `<70` values, H/L flags, `13 to 17` and one-sided ranges (`< 200`, `> 40`)
- [x] Skips date, time and patient-metadata lines
- [x] Fallback ranges only used when units match, and sex-specific for Hb, Hct, RBC, creatinine, uric acid, ferritin

**Review flag & AI**
- [x] `needs_review` saved per result (migration `data/migrations/001_lab_results_needs_review.sql`); report status becomes `needs_review` when any result is uncertain, with "Check" badges in the UI
- [x] Patient age and sex included in the AI prompt (prompt v3)
- [x] Safety filter covers every explanation field with targeted patterns
- [x] Explanations left by an AI error, or created before an API key was set, are regenerated on next request

**Docs & config**
- [x] `.env.example` uses the variable names the code actually reads
- [x] README tech stack, env reference and test instructions corrected; migrations documented
- [x] Removed unused `python-jose`; added `requirements-dev.txt` (pytest)
- [x] 118 backend tests (was 18)

**Still open**
- [ ] Run migration `001_lab_results_needs_review.sql` on the shared Supabase project
- [ ] Seed test definitions for ALT, AST, creatinine, fasting glucose and HbA1c (they're in the trends dropdown but never match)
- [ ] Show auto-generated explanations on the report page without clicking "Explain"
- [ ] Uploads: stream size check, sanitise file names, verify file content, clean up storage if the DB insert fails
- [ ] Recover reports stuck in `processing` after a server restart; add retry and delete endpoints
- [ ] Signed URLs to view the original report file
- [ ] Remove the unused `recharts` dependency from `frontend/package.json`
- [ ] `.gitignore` ignores all `*.pdf` / `*.png` / `*.jpg`, so sample reports can't be committed as test fixtures
- [ ] Tests for OCR, the remaining API endpoints and the frontend

---

## Phase 5: Stretch Goals 🔲 OPTIONAL

> Nice-to-haves if time permits — not required for the core project submission.

- [ ] Multi-page PDF chunking (process and label results by page)
- [ ] Support non-English lab reports via EasyOCR swap
- [ ] Report comparison view — side-by-side results across two uploads
- [ ] PDF export of results + AI explanations for a single report
- [ ] Email notification when report processing completes
- [ ] Admin panel to manage `test_definitions`
- [ ] Dark / light mode toggle (CSS custom properties already in place; just needs a toggle)
- [ ] PWA manifest + basic offline support
