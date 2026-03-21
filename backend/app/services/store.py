from collections import Counter
from uuid import uuid4

from app.schemas.common import CreateDishRequest, CreateVoteRequest, Dish, MenuItem, Vote, WeeklyMenuResponse

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


def list_dishes() -> list[Dish]:
    return list(_dishes.values())


def create_dish(payload: CreateDishRequest) -> Dish:
    dish = Dish(id=str(uuid4()), name=payload.name, tags=payload.tags)
    _dishes[dish.id] = dish
    return dish


def list_votes() -> list[Vote]:
    return _votes


def add_vote(payload: CreateVoteRequest) -> Vote:
    vote = Vote(user_name=payload.user_name, dish_id=payload.dish_id, day=payload.day)
    _votes.append(vote)
    return vote


def generate_weekly_menu() -> WeeklyMenuResponse:
    items: list[MenuItem] = []
    for day in WEEK_DAYS:
        day_votes = [v for v in _votes if v.day == day]
        if not day_votes:
            items.append(MenuItem(day=day, dish=None))
            continue

        ranking = Counter(v.dish_id for v in day_votes)
        winner_id = ranking.most_common(1)[0][0]
        items.append(MenuItem(day=day, dish=_dishes.get(winner_id)))
    return WeeklyMenuResponse(items=items)


def seed_data() -> None:
    if _dishes:
        return

    for name, tags in [
        ("Spaghetti Bolognese", ["pasta", "beef"]),
        ("Chicken Curry", ["spicy", "rice"]),
        ("Vegetable Stir Fry", ["veggie", "quick"]),
    ]:
        create_dish(CreateDishRequest(name=name, tags=tags))
