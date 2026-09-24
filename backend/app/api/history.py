from fastapi import APIRouter

router = APIRouter(prefix="/api/history", tags=["history"])

HISTORY = [
	{"date": "Sep 18, 2026", "title": "Annual wellness panel", "detail": "24 tests reviewed", "tone": "green"},
	{"date": "Aug 04, 2026", "title": "Lipid profile", "detail": "8 tests added", "tone": "amber"},
	{"date": "Jun 21, 2026", "title": "Complete blood count", "detail": "16 tests reviewed", "tone": "green"},
]


@router.get("")
async def list_history():
	return {"events": HISTORY}
