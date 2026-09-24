"""
MediClear FastAPI application.
"""

import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, history, patients, reports, results

# ---------------------------------------------------------------------------
# Startup validation — fail fast if required env vars are missing
# ---------------------------------------------------------------------------
REQUIRED_ENV_VARS = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
]

missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
if missing:
    print(
        f"[MediClear] STARTUP ERROR: Missing required environment variables: {missing}\n"
        "Copy .env.example to backend/.env and fill in the values.",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="MediClear API",
    description="Plain-English Medical Lab Report Translator — Backend API",
    version="0.2.0",
)

# ---------------------------------------------------------------------------
# CORS — read allowed origins from env; fall back to localhost dev server
# ---------------------------------------------------------------------------
_cors_origins_raw = os.environ.get("CORS_ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(history.router)
app.include_router(reports.router)
app.include_router(results.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"], summary="Health check")
def health():
    return {"status": "ok", "version": app.version}
