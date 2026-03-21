from fastapi import APIRouter, HTTPException

from app.schemas.common import CreateVoteRequest, Vote
from app.services import store

router = APIRouter()


@router.get("", response_model=list[Vote])
def get_votes() -> list[Vote]:
    return store.list_votes()


@router.post("", response_model=Vote)
def post_vote(payload: CreateVoteRequest) -> Vote:
    dish_ids = {dish.id for dish in store.list_dishes()}
    if payload.dish_id not in dish_ids:
        raise HTTPException(status_code=404, detail="Dish not found")
    return store.add_vote(payload)
