from collections import Counter
from uuid import uuid4

from app.schemas.common import (
    CreateDishRequest,
    CreateVoteRequest,
    Dish,
    FamilyMember,
    Meal,
    MenuItem,
    Vote,
    VoteSlot,
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
MEALS: list[Meal] = ["lunch", "dinner"]

_dishes: dict[str, Dish] = {}
_votes: list[Vote] = []
_members: list[str] = []
_vote_availability: dict[str, dict[Meal, bool]] = {}
_finalized: bool = False
_final_weekly_menu: WeeklyMenuResponse | None = None
_shortlists: dict[str, dict[Meal, set[str]]] = {}
_manual_menu: dict[str, dict[Meal, str | None]] = {}


def reset_store() -> None:
    global _dishes, _votes, _members, _vote_availability, _finalized, _final_weekly_menu, _shortlists, _manual_menu

    _dishes.clear()
    _votes.clear()
    _members.clear()
    _finalized = False
    _final_weekly_menu = None
    _vote_availability = {
        day: {meal: True for meal in MEALS} for day in WEEK_DAYS
    }
    _shortlists = {day: {meal: set() for meal in MEALS} for day in WEEK_DAYS}
    _manual_menu = {day: {meal: None for meal in MEALS} for day in WEEK_DAYS}


def list_dishes() -> list[Dish]:
    return list(_dishes.values())


def list_votes() -> list[Vote]:
    return _votes


def create_dish(payload: CreateDishRequest) -> Dish:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    dish = Dish(id=str(uuid4()), name=payload.name, tags=payload.tags, category=payload.category)
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
    dish.category = payload.category
    _dishes[dish_id] = dish
    return dish


def delete_dish(dish_id: str) -> None:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if dish_id not in _dishes:
        raise KeyError("Dish not found")

    _dishes.pop(dish_id)


def list_members() -> list[str]:
    return list(_members)


def add_member(name: str) -> str:
    if not name.strip():
        raise ValueError("Member name cannot be empty")
    if name in _members:
        raise ValueError("Member already exists")
    _members.append(name)
    return name


def update_member(current_name: str, new_name: str) -> str:
    if current_name not in _members:
        raise KeyError("Member not found")
    if not new_name.strip():
        raise ValueError("Member name cannot be empty")
    if new_name != current_name and new_name in _members:
        raise ValueError("Member already exists")
    index = _members.index(current_name)
    _members[index] = new_name
    for vote in _votes:
        if vote.user_name == current_name:
            vote.user_name = new_name
    return new_name


def delete_member(name: str) -> None:
    if name not in _members:
        raise KeyError("Member not found")
    _members.remove(name)
    global _votes
    _votes = [vote for vote in _votes if vote.user_name != name]


def list_vote_availability() -> list[VoteSlot]:
    slots: list[VoteSlot] = []
    for day in WEEK_DAYS:
        for meal in MEALS:
            slots.append(VoteSlot(day=day, meal=meal, available=_vote_availability[day][meal]))
    return slots


def set_vote_availability(slots: list[VoteSlot]) -> list[VoteSlot]:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    for slot in slots:
        if slot.day not in WEEK_DAYS or slot.meal not in MEALS:
            raise ValueError("Invalid vote slot")
        _vote_availability[slot.day][slot.meal] = slot.available
    return list_vote_availability()


def list_dish_categories() -> list[str]:
    return ["lunch", "dinner", "weekends_lunch", "saturday_dinner"]


def add_vote(payload: CreateVoteRequest) -> Vote:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus recevoir de votes")
    if payload.dish_id not in _dishes:
        raise KeyError("Dish not found")
    if payload.user_name not in _members:
        raise ValueError("Member not found")
    if not _vote_availability[payload.day][payload.meal]:
        raise ValueError("Slot not available")

    existing_vote = next(
        (vote for vote in _votes if vote.user_name == payload.user_name and vote.day == payload.day and vote.meal == payload.meal),
        None,
    )
    if existing_vote is not None:
        existing_vote.dish_id = payload.dish_id
        return existing_vote

    vote = Vote(user_name=payload.user_name, dish_id=payload.dish_id, day=payload.day, meal=payload.meal)
    _votes.append(vote)
    return vote


def set_shortlist(day: str, meal: Meal, dish_ids: list[str]) -> None:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if day not in WEEK_DAYS or meal not in MEALS:
        raise ValueError("Invalid vote slot")

    for dish_id in dish_ids:
        if dish_id not in _dishes:
            raise KeyError(f"Dish not found: {dish_id}")

    _shortlists[day][meal] = set(dish_ids)


def set_shortlists(slots: list[dict]) -> None:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    for slot in slots:
        day = slot["day"]
        meal = slot["meal"]
        dish_ids = slot["dish_ids"]
        set_shortlist(day, meal, dish_ids)


def set_menu_item(day: str, meal: Meal, dish_id: str | None) -> WeeklyMenuResponse:
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if day not in WEEK_DAYS or meal not in MEALS:
        raise ValueError("Invalid vote slot")
    if dish_id is not None and dish_id not in _dishes:
        raise KeyError("Dish not found")
    _manual_menu[day][meal] = dish_id
    return generate_weekly_menu()


def validate_menu() -> WeeklyMenuResponse:
    global _finalized, _final_weekly_menu

    if _finalized and _final_weekly_menu is not None:
        return _final_weekly_menu

    _final_weekly_menu = generate_weekly_menu(allow_generate_final=True)
    _finalized = True
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


def get_slot_category(day: str, meal: Meal) -> str:
    if meal == "lunch":
        return "weekends_lunch" if day in ["saturday", "sunday"] else "lunch"
    if meal == "dinner":
        return "saturday_dinner" if day == "saturday" else "dinner"
    return "dinner"


def generate_weekly_menu(allow_generate_final: bool = False) -> WeeklyMenuResponse:
    global _finalized, _final_weekly_menu

    if _finalized and _final_weekly_menu is not None and not allow_generate_final:
        return _final_weekly_menu

    items: list[MenuItem] = []
    for day in WEEK_DAYS:
        for meal in MEALS:
            manual_dish_id = _manual_menu[day][meal]
            if manual_dish_id is not None:
                items.append(MenuItem(day=day, meal=meal, dish=_dishes.get(manual_dish_id)))
                continue

            day_meal_votes = [v for v in _votes if v.day == day and v.meal == meal]
            whitelist = _shortlists[day][meal]

            if whitelist:
                day_meal_votes = [v for v in day_meal_votes if v.dish_id in whitelist]

            if not day_meal_votes:
                items.append(MenuItem(day=day, meal=meal, dish=None))
                continue

            slot_category = get_slot_category(day, meal)
            eligible_dish_ids = [dish.id for dish in _dishes.values() if dish.category == slot_category]
            if eligible_dish_ids:
                day_meal_votes = [v for v in day_meal_votes if v.dish_id in eligible_dish_ids]

            if not day_meal_votes:
                items.append(MenuItem(day=day, meal=meal, dish=None))
                continue

            ranking = Counter(v.dish_id for v in day_meal_votes)
            winner_id = ranking.most_common(1)[0][0]
            items.append(MenuItem(day=day, meal=meal, dish=_dishes.get(winner_id)))

    response = WeeklyMenuResponse(
        items=items,
        finalized=_finalized,
        shortlists={day: {meal: list(_shortlists[day][meal]) for meal in MEALS} for day in WEEK_DAYS},
    )
    return response


def seed_data() -> None:
    if _dishes:
        return

    reset_store()

    for name, tags, category in [
        ("Spaghetti Bolognese", ["pasta", "beef"], "lunch"),
        ("Chicken Curry", ["spicy", "rice"], "dinner"),
        ("Vegetable Stir Fry", ["veggie", "quick"], "weekends_lunch"),
        ("Grilled Salmon", ["fish", "healthy"], "saturday_dinner"),
    ]:
        create_dish(CreateDishRequest(name=name, tags=tags, category=category))

    for member in ["Alice", "Bob", "Cara"]:
        add_member(member)
