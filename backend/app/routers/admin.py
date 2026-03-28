from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.auth import (
    get_current_admin,
    is_admin_authenticated,
    login_admin,
    logout_admin,
)
from app.schemas.common import (
    AdminLoginRequest,
    AdminSessionResponse,
    CreateDishRequest,
    Dish,
    FamilyMember,
    Meal,
    SetMenuItemRequest,
    SetMenuSlotItemRequest,
    SetShortlistRequest,
    VoteSlot,
    WeeklyMenuResponse,
    DishCategory,
    Weekday,
)
from app.services import store

router = APIRouter()
protected_router = APIRouter(dependencies=[Depends(get_current_admin)])


@router.post("/login", response_model=AdminSessionResponse)
def post_admin_login(payload: AdminLoginRequest, response: Response) -> AdminSessionResponse:
    login_admin(response, payload.username, payload.password)
    return AdminSessionResponse(authenticated=True)


@router.post("/logout", response_model=AdminSessionResponse)
def post_admin_logout(response: Response) -> AdminSessionResponse:
    logout_admin(response)
    return AdminSessionResponse(authenticated=False)


@router.get("/session", response_model=AdminSessionResponse)
def get_admin_session(request: Request) -> AdminSessionResponse:
    return AdminSessionResponse(authenticated=is_admin_authenticated(request))


@protected_router.get("/members", response_model=list[str])
def get_members() -> list[str]:
    return store.list_members()


@protected_router.post("/members", response_model=str)
def post_member(payload: FamilyMember) -> str:
    try:
        return store.add_member(payload.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@protected_router.put("/members/{name}", response_model=str)
def put_member(name: str, payload: FamilyMember) -> str:
    try:
        return store.update_member(name, payload.name)
    except KeyError:
        raise HTTPException(status_code=404, detail="Member not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@protected_router.delete("/members/{name}", status_code=204)
def delete_member(name: str) -> None:
    try:
        store.delete_member(name)
    except KeyError:
        raise HTTPException(status_code=404, detail="Member not found")


@protected_router.get("/vote-availability", response_model=list[VoteSlot])
def get_vote_availability() -> list[VoteSlot]:
    return store.list_vote_availability()


@protected_router.put("/vote-availability", response_model=list[VoteSlot])
def put_vote_availability(payload: list[VoteSlot]) -> list[VoteSlot]:
    try:
        return store.set_vote_availability(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@protected_router.get("/dishes/categories", response_model=list[DishCategory])
def get_dish_categories() -> list[DishCategory]:
    return store.list_dish_categories()


@protected_router.get("/dishes", response_model=list[Dish])
def get_dishes() -> list[Dish]:
    return store.list_dishes()


@protected_router.post("/dishes", response_model=Dish)
def post_dish(payload: CreateDishRequest) -> Dish:
    try:
        return store.create_dish(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@protected_router.put("/dishes/{dish_id}", response_model=Dish)
def put_dish(dish_id: str, payload: CreateDishRequest) -> Dish:
    try:
        return store.update_dish(dish_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Dish not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@protected_router.delete("/dishes/{dish_id}", status_code=204)
def delete_dish(dish_id: str) -> None:
    try:
        store.delete_dish(dish_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Dish not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@protected_router.put("/menu/shortlist", response_model=WeeklyMenuResponse)
def put_shortlist(payload: list[SetShortlistRequest]) -> WeeklyMenuResponse:
    try:
        store.set_shortlists([slot.model_dump() for slot in payload])
        return store.generate_weekly_menu()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@protected_router.put("/menu/shortlist/{day}", response_model=WeeklyMenuResponse)
def put_shortlist_legacy(day: Weekday, dish_ids: list[str]) -> WeeklyMenuResponse:
    try:
        store.set_shortlist(day, "lunch", dish_ids)
        return store.generate_weekly_menu()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@protected_router.put("/menu/item", response_model=WeeklyMenuResponse)
def put_menu_item(payload: SetMenuSlotItemRequest) -> WeeklyMenuResponse:
    try:
        return store.set_menu_item(payload.day, payload.meal, payload.dish_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@protected_router.put("/menu/item/{day}", response_model=WeeklyMenuResponse)
def put_menu_item_legacy(day: Weekday, payload: SetMenuItemRequest) -> WeeklyMenuResponse:
    try:
        return store.set_menu_item(day, "lunch", payload.dish_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@protected_router.post("/menu/validate", response_model=WeeklyMenuResponse)
def post_validate_menu() -> WeeklyMenuResponse:
    try:
        return store.validate_menu()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@protected_router.delete("/menu/validate", response_model=WeeklyMenuResponse)
def delete_validate_menu() -> WeeklyMenuResponse:
    try:
        return store.unvalidate_menu()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


router.include_router(protected_router)
