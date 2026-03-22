from collections import Counter
from uuid import uuid4

from app.schemas.common import (
    CreateDishRequest,
    CreateVoteRequest,
    Dish,
    MenuItem,
    Vote,
    WeeklyMenuResponse,
)

WEEK_DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

_dishes: dict[str, Dish] = {}
_votes: list[Vote] = []
_finalized: bool = False
_final_weekly_menu: WeeklyMenuResponse | None = None
_shortlists: dict[str, set[str]] = {day: set() for day in WEEK_DAYS}
_manual_menu: dict[str, str | None] = {day: None for day in WEEK_DAYS}


def reset_store() -> None:
    global _dishes, _votes, _finalized, _final_weekly_menu, _shortlists, _manual_menu

    _dishes.clear()
    _votes.clear()
    _finalized = False
    _final_weekly_menu = None
    _shortlists = {day: set() for day in WEEK_DAYS}
    _manual_menu = {day: None for day in WEEK_DAYS}


def list_dishes() -> list[Dish]:
    return list(_dishes.values())


def create_dish(payload: CreateDishRequest) -> Dish:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    dish = Dish(id=str(uuid4()), name=payload.name, tags=payload.tags)
    _dishes[dish.id] = dish
    return dish


def update_dish(dish_id: str, payload: CreateDishRequest) -> Dish:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if dish_id not in _dishes:
        raise KeyError("Dish not found")

    dish = _dishes[dish_id]
    dish.name = payload.name
    dish.tags = payload.tags
    _dishes[dish_id] = dish
    return dish


def delete_dish(dish_id: str) -> None:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if dish_id not in _dishes:
        raise KeyError("Dish not found")

    _dishes.pop(dish_id)


def list_votes() -> list[Vote]:
    return _votes


def add_vote(payload: CreateVoteRequest) -> Vote:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus recevoir de votes")
    if payload.dish_id not in _dishes:
        raise KeyError("Dish not found")

    vote = Vote(user_name=payload.user_name, dish_id=payload.dish_id, day=payload.day)
    _votes.append(vote)
    return vote


def set_shortlist(day: str, dish_ids: list[str]) -> None:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if day not in WEEK_DAYS:
        raise ValueError("Day not supported")

    for dish_id in dish_ids:
        if dish_id not in _dishes:
            raise KeyError(f"Dish not found: {dish_id}")

    _shortlists[day] = set(dish_ids)


def set_menu_item(day: str, dish_id: str | None) -> WeeklyMenuResponse:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if dish_id is not None and dish_id not in _dishes:
        raise KeyError("Dish not found")
    _manual_menu[day] = dish_id
    return generate_weekly_menu()


def validate_menu() -> WeeklyMenuResponse:
    global _finalized, _final_weekly_menu

    if _finalized and _final_weekly_menu is not None:
        return _final_weekly_menu

    _final_weekly_menu = generate_weekly_menu(allow_generate_final=True)
    _finalized = True
    # Update the finalized status
    _final_weekly_menu = WeeklyMenuResponse(
        items=_final_weekly_menu.items,
        finalized=True,
        shortlists=_final_weekly_menu.shortlists,
    )
    return _final_weekly_menu


def unvalidate_menu() -> WeeklyMenuResponse:
    global _finalized, _final_weekly_menu

    _finalized = False
    _final_weekly_menu = None
    return generate_weekly_menu()


def generate_weekly_menu(allow_generate_final: bool = False) -> WeeklyMenuResponse:
    global _finalized, _final_weekly_menu

    if _finalized and _final_weekly_menu is not None and not allow_generate_final:
        return _final_weekly_menu

    items: list[MenuItem] = []
    for day in WEEK_DAYS:
        manual_dish_id = _manual_menu.get(day)
        if manual_dish_id is not None:
            items.append(MenuItem(day=day, dish=_dishes.get(manual_dish_id)))
            continue

        day_votes = [v for v in _votes if v.day == day]
        whitelist = _shortlists.get(day, set())

        if whitelist:
            day_votes = [v for v in day_votes if v.dish_id in whitelist]

        if not day_votes:
            items.append(MenuItem(day=day, dish=None))
            continue

        ranking = Counter(v.dish_id for v in day_votes)
        winner_id = ranking.most_common(1)[0][0]
        items.append(MenuItem(day=day, dish=_dishes.get(winner_id)))

    response = WeeklyMenuResponse(
        items=items,
        finalized=_finalized,
        shortlists={day: list(_shortlists.get(day, [])) for day in WEEK_DAYS},
    )
    return response


def seed_data() -> None:
    if _dishes:
        return

    reset_store()

    for name, tags in [
        ("Spaghetti Bolognese", ["pasta", "beef"]),
        ("Chicken Curry", ["spicy", "rice"]),
        ("Vegetable Stir Fry", ["veggie", "quick"]),
    ]:
        create_dish(CreateDishRequest(name=name, tags=tags))
