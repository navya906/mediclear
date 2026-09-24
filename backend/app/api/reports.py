from fastapi import APIRouter

router = APIRouter(prefix="/api/reports", tags=["reports"])

REPORTS = [
	{"id": "wellness-2026", "name": "Annual wellness panel", "date": "Sep 18, 2026", "tests": 24, "status": "Reviewed", "tone": "green", "summary": "All results are in range."},
	{"id": "lipid-2026", "name": "Lipid profile", "date": "Aug 04, 2026", "tests": 8, "status": "Needs attention", "tone": "amber", "summary": "2 results may need attention."},
	{"id": "cbc-2026", "name": "Complete blood count", "date": "Jun 21, 2026", "tests": 16, "status": "Reviewed", "tone": "green", "summary": "All results are in range."},
]


@router.get("")
async def list_reports():
	return {"reports": REPORTS}


@router.get("/{report_id}")
async def get_report(report_id: str):
	return next((report for report in REPORTS if report["id"] == report_id), {"detail": "Report not found"})
