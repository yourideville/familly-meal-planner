import logging
import os
from collections import Counter
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Attr

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

logger = logging.getLogger(__name__)

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

BACKEND_PERSISTENCE_MODE = os.getenv("BACKEND_PERSISTENCE_MODE", "inmemory").lower()
_USE_DYNAMODB = BACKEND_PERSISTENCE_MODE == "dynamodb"

_dishes_table = None
_members_table = None
_votes_table = None
_vote_ids: dict[tuple[str, str, str], str] = {}
_persistence_loaded = False

if _USE_DYNAMODB:
    logger.info("Backend persistence mode set to dynamodb")
    try:
        dynamodb_resource = boto3.resource("dynamodb")
        _dishes_table = dynamodb_resource.Table(os.environ["DISHES_TABLE_NAME"])
        _members_table = dynamodb_resource.Table(os.environ["MEMBERS_TABLE_NAME"])
        _votes_table = dynamodb_resource.Table(os.environ["VOTES_TABLE_NAME"])
    except KeyError as exc:
        raise RuntimeError("DynamoDB table names must be configured in environment variables") from exc


def _scan_table(table):
    items = []
    response = table.scan()
    items.extend(response.get("Items", []))
    while response.get("LastEvaluatedKey"):
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response.get("Items", []))
    return items


def _ensure_store_loaded() -> None:
    global _persistence_loaded
    if not _USE_DYNAMODB or _persistence_loaded:
        return
    logger.info("Loading persistent state from DynamoDB")
    reset_store()
    _load_dishes_from_db()
    _load_members_from_db()
    _load_votes_from_db()
    _persistence_loaded = True


def _load_dishes_from_db() -> None:
    for item in _scan_table(_dishes_table):
        dish = Dish(
            id=item["dish_id"],
            name=item["name"],
            tags=item.get("tags", []),
            category=item["category"],
        )
        _dishes[dish.id] = dish


def _load_members_from_db() -> None:
    for item in _scan_table(_members_table):
        _members.append(item["member_id"])


def _load_votes_from_db() -> None:
    for item in _scan_table(_votes_table):
        vote = Vote(
            user_name=item["user_name"],
            dish_id=item["dish_id"],
            day=item["day"],
            meal=item["meal"],
        )
        _votes.append(vote)
        _vote_ids[(vote.user_name, vote.day, vote.meal)] = item["vote_id"]


def _persist_dish(dish: Dish) -> None:
    if not _USE_DYNAMODB:
        return
    _dishes_table.put_item(
        Item={
            "dish_id": dish.id,
            "name": dish.name,
            "tags": dish.tags,
            "category": dish.category,
        }
    )


def _delete_dish_from_db(dish_id: str) -> None:
    if not _USE_DYNAMODB:
        return
    _dishes_table.delete_item(Key={"dish_id": dish_id})


def _persist_member(name: str) -> None:
    if not _USE_DYNAMODB:
        return
    _members_table.put_item(Item={"member_id": name})


def _delete_member_from_db(name: str) -> None:
    if not _USE_DYNAMODB:
        return
    _members_table.delete_item(Key={"member_id": name})


def _persist_vote(vote: Vote, vote_id: str | None = None) -> str:
    if not _USE_DYNAMODB:
        return ""
    if vote_id is None:
        vote_id = _vote_ids.get((vote.user_name, vote.day, vote.meal), str(uuid4()))
    _votes_table.put_item(
        Item={
            "vote_id": vote_id,
            "user_name": vote.user_name,
            "dish_id": vote.dish_id,
            "day": vote.day,
            "meal": vote.meal,
        }
    )
    _vote_ids[(vote.user_name, vote.day, vote.meal)] = vote_id
    return vote_id


def _delete_vote_from_db(vote_id: str) -> None:
    if not _USE_DYNAMODB:
        return
    _votes_table.delete_item(Key={"vote_id": vote_id})


def _delete_votes_for_member(name: str) -> None:
    if not _USE_DYNAMODB:
        return
    votes_to_remove = [
        (vote, _vote_ids[(vote.user_name, vote.day, vote.meal)])
        for vote in _votes
        if vote.user_name == name and (vote.user_name, vote.day, vote.meal) in _vote_ids
    ]
    for vote, vote_id in votes_to_remove:
        _delete_vote_from_db(vote_id)
        _vote_ids.pop((vote.user_name, vote.day, vote.meal), None)


def _update_votes_member_name(current_name: str, new_name: str) -> None:
    for vote in _votes:
        if vote.user_name == current_name:
            vote_id = _vote_ids.pop((vote.user_name, vote.day, vote.meal), None)
            vote.user_name = new_name
            if _USE_DYNAMODB and vote_id is not None:
                _persist_vote(vote, vote_id)
                _vote_ids[(new_name, vote.day, vote.meal)] = vote_id


def reset_store() -> None:
    global _dishes, _votes, _members, _vote_availability, _finalized, _final_weekly_menu, _shortlists, _manual_menu, _vote_ids, _persistence_loaded

    _dishes.clear()
    _votes.clear()
    _members.clear()
    _vote_ids.clear()
    _finalized = False
    _final_weekly_menu = None
    _vote_availability = {
        day: {meal: True for meal in MEALS} for day in WEEK_DAYS
    }
    _shortlists = {day: {meal: set() for meal in MEALS} for day in WEEK_DAYS}
    _manual_menu = {day: {meal: None for meal in MEALS} for day in WEEK_DAYS}
    _persistence_loaded = False


def list_dishes() -> list[Dish]:
    _ensure_store_loaded()
    return list(_dishes.values())


def list_votes() -> list[Vote]:
    _ensure_store_loaded()
    return _votes


def create_dish(payload: CreateDishRequest) -> Dish:
    _ensure_store_loaded()
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    dish = Dish(id=str(uuid4()), name=payload.name, tags=payload.tags, category=payload.category)
    _dishes[dish.id] = dish
    _persist_dish(dish)
    return dish


def update_dish(dish_id: str, payload: CreateDishRequest) -> Dish:
    _ensure_store_loaded()
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if dish_id not in _dishes:
        raise KeyError("Dish not found")

    dish = _dishes[dish_id]
    dish.name = payload.name
    dish.tags = payload.tags
    dish.category = payload.category
    _dishes[dish_id] = dish
    _persist_dish(dish)
    return dish


def delete_dish(dish_id: str) -> None:
    _ensure_store_loaded()
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if dish_id not in _dishes:
        raise KeyError("Dish not found")

    _dishes.pop(dish_id)
    _delete_dish_from_db(dish_id)


def list_members() -> list[str]:
    _ensure_store_loaded()
    return list(_members)


def add_member(name: str) -> str:
    _ensure_store_loaded()
    if not name.strip():
        raise ValueError("Member name cannot be empty")
    if name in _members:
        raise ValueError("Member already exists")
    _members.append(name)
    _persist_member(name)
    return name


def update_member(current_name: str, new_name: str) -> str:
    _ensure_store_loaded()
    if current_name not in _members:
        raise KeyError("Member not found")
    if not new_name.strip():
        raise ValueError("Member name cannot be empty")
    if new_name != current_name and new_name in _members:
        raise ValueError("Member already exists")
    index = _members.index(current_name)
    _members[index] = new_name
    if _USE_DYNAMODB:
        _delete_member_from_db(current_name)
        _persist_member(new_name)
    _update_votes_member_name(current_name, new_name)
    return new_name


def delete_member(name: str) -> None:
    _ensure_store_loaded()
    if name not in _members:
        raise KeyError("Member not found")
    _delete_votes_for_member(name)
    _members.remove(name)
    _votes[:] = [vote for vote in _votes if vote.user_name != name]
    _delete_member_from_db(name)


def list_vote_availability() -> list[VoteSlot]:
    _ensure_store_loaded()
    slots: list[VoteSlot] = []
    for day in WEEK_DAYS:
        for meal in MEALS:
            slots.append(VoteSlot(day=day, meal=meal, available=_vote_availability[day][meal]))
    return slots


def set_vote_availability(slots: list[VoteSlot]) -> list[VoteSlot]:
    _ensure_store_loaded()
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
    _ensure_store_loaded()
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
        _persist_vote(existing_vote)
        return existing_vote

    vote = Vote(user_name=payload.user_name, dish_id=payload.dish_id, day=payload.day, meal=payload.meal)
    _votes.append(vote)
    _persist_vote(vote)
    return vote


def set_shortlist(day: str, meal: Meal, dish_ids: list[str]) -> None:
    _ensure_store_loaded()
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if day not in WEEK_DAYS or meal not in MEALS:
        raise ValueError("Invalid vote slot")

    for dish_id in dish_ids:
        if dish_id not in _dishes:
            raise KeyError(f"Dish not found: {dish_id}")

    _shortlists[day][meal] = set(dish_ids)


def set_shortlists(slots: list[dict]) -> None:
    _ensure_store_loaded()
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    for slot in slots:
        day = slot["day"]
        meal = slot["meal"]
        dish_ids = slot["dish_ids"]
        set_shortlist(day, meal, dish_ids)


def set_menu_item(day: str, meal: Meal, dish_id: str | None) -> WeeklyMenuResponse:
    _ensure_store_loaded()
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if day not in WEEK_DAYS or meal not in MEALS:
        raise ValueError("Invalid vote slot")
    if dish_id is not None and dish_id not in _dishes:
        raise KeyError("Dish not found")
    _manual_menu[day][meal] = dish_id
    return generate_weekly_menu()


def validate_menu() -> WeeklyMenuResponse:
    _ensure_store_loaded()
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
    _ensure_store_loaded()
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
    _ensure_store_loaded()
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
