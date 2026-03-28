from fastapi import APIRouter

from app.services import store

router = APIRouter()


@router.get("", response_model=list[str])
def list_members() -> list[str]:
    return store.list_members()
