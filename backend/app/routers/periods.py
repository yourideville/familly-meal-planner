"""Menu periods API endpoints.

Provides access to historical menu periods for the public weekly menu page.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.common import MenuPeriod, WeeklyMenuResponse
from app.services import store

router = APIRouter()


@router.get("/periods", response_model=list[MenuPeriod])
def list_menu_periods(limit: int = 12):
    """List available menu periods, most recent first.
    
    Args:
        limit: Maximum number of periods to return (default 12)
    
    Returns:
        List of MenuPeriod objects (without full menu content)
    """
    store.auto_finalize_if_needed()
    return store.list_periods(limit=limit)


@router.get("/periods/{period_id}", response_model=MenuPeriod)
def get_menu_period(period_id: str):
    """Get a specific menu period by ID.
    
    Args:
        period_id: The period ID (YYYY-MM-DD format)
    
    Returns:
        MenuPeriod with full menu content
    """
    store.auto_finalize_if_needed()
    period = store.get_period(period_id)
    if not period:
        raise HTTPException(status_code=404, detail=f"Period not found: {period_id}")
    
    # If period doesn't have menu, generate it
    if not period.menu:
        # For historical periods, we need to regenerate or retrieve stored menu
        # For now, return period without menu (can be enhanced later)
        pass
    
    return period


@router.get("/current-period", response_model=MenuPeriod)
def get_current_period():
    """Get the currently active menu period.
    
    Returns:
        Current MenuPeriod
    """
    store.auto_finalize_if_needed()
    store.ensure_active_period()
    period = store.get_active_period()
    if not period:
        raise HTTPException(status_code=500, detail="Failed to create current period")
    return period
