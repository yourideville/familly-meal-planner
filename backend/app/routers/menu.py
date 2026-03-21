from fastapi import APIRouter

from app.schemas.common import WeeklyMenuResponse
from app.services import store

router = APIRouter()


@router.get("", response_model=WeeklyMenuResponse)
def get_weekly_menu() -> WeeklyMenuResponse:
    return store.generate_weekly_menu()
