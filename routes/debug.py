from fastapi import APIRouter, Query

from services.sheets import debug_dump_tab

router = APIRouter()


@router.get("/debug/sheets")
async def debug_sheets(tab: str = Query(..., description="Exact tab name, e.g. A1 or 'HALL 1'")):
    """Temporary endpoint, not for production use. Lets us confirm the real
    column layout and date formatting of a given tab before finalizing the
    parsing logic in services/sheets.py. Remove this route once Phase 3
    parsing is confirmed working.
    """
    rows = debug_dump_tab(tab)
    return {"tab": tab, "rows": rows}
