from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.history import router as history_router
from app.api.reports import router as reports_router

app = FastAPI(
    title="MediClear API",
    description="Plain-English Medical Lab Report Translator",
    version="0.1.0",
)

# Allow frontend (Vite dev server) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports_router)
app.include_router(history_router)


@app.get("/")
async def root():
    return {"message": "MediClear API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
