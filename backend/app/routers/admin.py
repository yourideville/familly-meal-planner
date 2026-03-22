from fastapi import APIRouter, HTTPException

from app.schemas.common import (
    CreateDishRequest,
    Dish,
    SetMenuItemRequest,
    WeeklyMenuResponse,
    Weekday,
)
from app.services import store

router = APIRouter()


@router.get("/dishes", response_model=list[Dish])
def get_dishes() -> list[Dish]:
    return store.list_dishes()


@router.post("/dishes", response_model=Dish)
def post_dish(payload: CreateDishRequest) -> Dish:
    try:
        return store.create_dish(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.put("/dishes/{dish_id}", response_model=Dish)
def put_dish(dish_id: str, payload: CreateDishRequest) -> Dish:
    try:
        return store.update_dish(dish_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Dish not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete("/dishes/{dish_id}", status_code=204)
def delete_dish(dish_id: str) -> None:
    try:
        store.delete_dish(dish_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Dish not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.put("/menu/shortlist/{day}", response_model=WeeklyMenuResponse)
def put_shortlist(day: Weekday, dish_ids: list[str]) -> WeeklyMenuResponse:
    try:
        store.set_shortlist(day, dish_ids)
        return store.generate_weekly_menu()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/menu/item/{day}", response_model=WeeklyMenuResponse)
def put_menu_item(day: Weekday, payload: SetMenuItemRequest) -> WeeklyMenuResponse:
    try:
        return store.set_menu_item(day, payload.dish_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/menu/validate", response_model=WeeklyMenuResponse)
def post_validate_menu() -> WeeklyMenuResponse:
    try:
        return store.validate_menu()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.delete("/menu/validate", response_model=WeeklyMenuResponse)
def delete_validate_menu() -> WeeklyMenuResponse:
    try:
        return store.unvalidate_menu()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
