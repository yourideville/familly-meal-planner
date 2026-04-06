from fastapi import APIRouter, HTTPException

from app.schemas.common import CreateVoteRequest, Vote, VoteSlot
from app.services import store

router = APIRouter()


@router.get("/availability", response_model=list[VoteSlot])
def get_vote_availability() -> list[VoteSlot]:
    return store.list_vote_availability()


@router.get("", response_model=list[Vote])
def get_votes() -> list[Vote]:
    return store.list_votes()


@router.post("", response_model=Vote)
def post_vote(payload: CreateVoteRequest) -> Vote:
    try:
        return store.add_vote(payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Dish not found")
    except ValueError as exc:
        detail = str(exc)
        if detail == "Member not found":
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=409, detail=detail)
