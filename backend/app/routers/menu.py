from fastapi import APIRouter, HTTPException

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

    # If a specific period is requested, fetch that period's menu
    if period:
        period_data = store.get_period(period)
        if not period_data:
            raise HTTPException(status_code=404, detail=f"Period not found: {period}")
        # Return menu for the requested period
        # Note: This will be enhanced when historical menu storage is implemented
        return period_data.menu or store.generate_weekly_menu()

    return store.generate_weekly_menu()

