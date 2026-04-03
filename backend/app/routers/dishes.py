from fastapi import APIRouter

from app.schemas.common import CreateDishRequest, Dish
from app.services import store

router = APIRouter()


@router.get("", response_model=list[Dish])
def get_dishes() -> list[Dish]:
    return store.list_dishes()


@router.post("", response_model=Dish)
def post_dish(payload: CreateDishRequest) -> Dish:
    return store.create_dish(payload)
