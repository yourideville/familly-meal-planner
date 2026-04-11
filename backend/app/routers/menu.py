from fastapi import APIRouter

from app.schemas.common import WeeklyMenuResponse
from app.services import store

router = APIRouter()


@router.get("", response_model=WeeklyMenuResponse)
def get_weekly_menu(period: str | None = None) -> WeeklyMenuResponse:
    """Get the weekly menu, optionally for a specific period.
    
    Args:
        period: Optional period ID (YYYY-MM-DD). If not provided, returns current period menu.
    
    Returns:
        WeeklyMenuResponse with period metadata
    """
    # Auto-finalize if needed
    store.auto_finalize_if_needed()
    
    # Ensure we have an active period
    store.ensure_active_period()
    
    return store.generate_weekly_menu()

