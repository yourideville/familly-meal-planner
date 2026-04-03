import json
import logging
import os
from collections import Counter
from uuid import uuid4

from app.schemas.common import (
    CreateDishRequest,
    CreateVoteRequest,
    DishCategory,
    Dish,
    FamilyMember,
    Meal,
    MenuItem,
    SetShortlistRequest,
    Vote,
    VoteSlot,
    Weekday,
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

# ---------------------------------------------------------------------------
# In-memory state (used for both inmemory and dynamodb modes)
# ---------------------------------------------------------------------------
_dishes: dict[str, Dish] = {}
_votes: list[Vote] = []
_members: list[str] = []
_vote_availability: dict[str, dict[Meal, bool]] = {}
_finalized: bool = False
_final_weekly_menu: WeeklyMenuResponse | None = None
_shortlists: dict[str, dict[Meal, set[str]]] = {}
_manual_menu: dict[str, dict[Meal, str | None]] = {}

# ---------------------------------------------------------------------------
# DynamoDB single-table setup
# ---------------------------------------------------------------------------
# Key schema:
#   Dishes:   PK=DISH#<id>            SK=METADATA         GSI1PK=DISHES  GSI1SK=DISH#<id>
#   Members:  PK=MEMBER#<name>        SK=METADATA         GSI1PK=MEMBERS GSI1SK=MEMBER#<name>
#   Votes:    PK=SLOT#<day>#<meal>    SK=USER#<user_name>  GSI1PK=USER#<user_name> GSI1SK=SLOT#<day>#<meal>
#   Config:   PK=CONFIG               SK=AVAIL#<day>#<meal> | SHORTLIST#<day>#<meal> | MENU#<day>#<meal> | FINALIZED
# ---------------------------------------------------------------------------

BACKEND_PERSISTENCE_MODE = os.getenv("BACKEND_PERSISTENCE_MODE", "inmemory").lower()
_USE_DYNAMODB = BACKEND_PERSISTENCE_MODE == "dynamodb"

_table = None
_persistence_loaded = False

if _USE_DYNAMODB:
    import boto3

    logger.info("Backend persistence mode set to dynamodb")
    try:
        dynamodb_resource = boto3.resource("dynamodb")
        _table = dynamodb_resource.Table(os.environ["TABLE_NAME"])
    except KeyError as exc:
        raise RuntimeError("TABLE_NAME must be configured in environment variables") from exc


def _query_pk(pk: str) -> list[dict]:
    """Query all items sharing a partition key."""
    items: list[dict] = []
    response = _table.query(KeyConditionExpression="PK = :pk", ExpressionAttributeValues={":pk": pk})
    items.extend(response.get("Items", []))
    while response.get("LastEvaluatedKey"):
        response = _table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": pk},
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))
    return items


def _query_gsi1(gsi1pk: str) -> list[dict]:
    """Query all items sharing a GSI1 partition key."""
    items: list[dict] = []
    response = _table.query(
        IndexName="GSI1",
        KeyConditionExpression="GSI1PK = :pk",
        ExpressionAttributeValues={":pk": gsi1pk},
    )
    items.extend(response.get("Items", []))
    while response.get("LastEvaluatedKey"):
        response = _table.query(
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :pk",
            ExpressionAttributeValues={":pk": gsi1pk},
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        items.extend(response.get("Items", []))
    return items


def _put_item(item: dict) -> None:
    _table.put_item(Item=item)


def _delete_item(pk: str, sk: str) -> None:
    _table.delete_item(Key={"PK": pk, "SK": sk})


# ---------------------------------------------------------------------------
# Load from DynamoDB
# ---------------------------------------------------------------------------

def _ensure_store_loaded() -> None:
    global _persistence_loaded
    if not _USE_DYNAMODB or _persistence_loaded:
        return
    logger.info("Loading persistent state from DynamoDB")
    reset_store()
    _load_dishes_from_db()
    _load_members_from_db()
    _load_votes_from_db()
    _load_config_from_db()
    _persistence_loaded = True


def _load_dishes_from_db() -> None:
    for item in _query_gsi1("DISHES"):
        dish = Dish(
            id=item["PK"].removeprefix("DISH#"),
            name=item["name"],
            tags=item.get("tags", []),
            category=item["category"],
        )
        _dishes[dish.id] = dish


def _load_members_from_db() -> None:
    for item in _query_gsi1("MEMBERS"):
        _members.append(item["PK"].removeprefix("MEMBER#"))


def _load_votes_from_db() -> None:
    # Query by GSI1PK would require knowing all users. Instead, query each slot.
    seen: set[tuple[str, str, str]] = set()
    for day in WEEK_DAYS:
        for meal in MEALS:
            for item in _query_pk(f"SLOT#{day}#{meal}"):
                user_name = item["SK"].removeprefix("USER#")
                key = (user_name, day, meal)
                if key not in seen:
                    seen.add(key)
                    vote = Vote(
                        user_name=user_name,
                        dish_id=item["dish_id"],
                        day=day,
                        meal=meal,
                    )
                    _votes.append(vote)


def _load_config_from_db() -> None:
    global _finalized
    for item in _query_pk("CONFIG"):
        sk: str = item["SK"]
        if sk.startswith("AVAIL#"):
            parts = sk.removeprefix("AVAIL#").split("#")
            day, meal = parts[0], parts[1]
            _vote_availability[day][meal] = item["available"]
        elif sk.startswith("SHORTLIST#"):
            parts = sk.removeprefix("SHORTLIST#").split("#")
            day, meal = parts[0], parts[1]
            _shortlists[day][meal] = set(item.get("dish_ids", []))
        elif sk.startswith("MENU#"):
            parts = sk.removeprefix("MENU#").split("#")
            day, meal = parts[0], parts[1]
            _manual_menu[day][meal] = item.get("dish_id")
        elif sk == "FINALIZED":
            _finalized = item.get("finalized", False)


# ---------------------------------------------------------------------------
# Persist helpers
# ---------------------------------------------------------------------------

def _persist_dish(dish: Dish) -> None:
    if not _USE_DYNAMODB:
        return
    _put_item({
        "PK": f"DISH#{dish.id}",
        "SK": "METADATA",
        "GSI1PK": "DISHES",
        "GSI1SK": f"DISH#{dish.id}",
        "name": dish.name,
        "tags": dish.tags,
        "category": dish.category,
    })


def _delete_dish_from_db(dish_id: str) -> None:
    if not _USE_DYNAMODB:
        return
    _delete_item(f"DISH#{dish_id}", "METADATA")


def _persist_member(name: str) -> None:
    if not _USE_DYNAMODB:
        return
    _put_item({
        "PK": f"MEMBER#{name}",
        "SK": "METADATA",
        "GSI1PK": "MEMBERS",
        "GSI1SK": f"MEMBER#{name}",
    })


def _delete_member_from_db(name: str) -> None:
    if not _USE_DYNAMODB:
        return
    _delete_item(f"MEMBER#{name}", "METADATA")


def _persist_vote(vote: Vote) -> None:
    if not _USE_DYNAMODB:
        return
    _put_item({
        "PK": f"SLOT#{vote.day}#{vote.meal}",
        "SK": f"USER#{vote.user_name}",
        "GSI1PK": f"USER#{vote.user_name}",
        "GSI1SK": f"SLOT#{vote.day}#{vote.meal}",
        "dish_id": vote.dish_id,
    })


def _delete_vote_from_db(user_name: str, day: str, meal: str) -> None:
    if not _USE_DYNAMODB:
        return
    _delete_item(f"SLOT#{day}#{meal}", f"USER#{user_name}")


def _delete_votes_for_member(name: str) -> None:
    if not _USE_DYNAMODB:
        return
    for vote in _votes:
        if vote.user_name == name:
            _delete_vote_from_db(name, vote.day, vote.meal)


def _update_votes_member_name(current_name: str, new_name: str) -> None:
    for vote in _votes:
        if vote.user_name == current_name:
            if _USE_DYNAMODB:
                _delete_vote_from_db(current_name, vote.day, vote.meal)
            vote.user_name = new_name
            if _USE_DYNAMODB:
                _persist_vote(vote)


def _persist_config_availability(day: str, meal: str, available: bool) -> None:
    if not _USE_DYNAMODB:
        return
    _put_item({
        "PK": "CONFIG",
        "SK": f"AVAIL#{day}#{meal}",
        "available": available,
    })


def _persist_config_shortlist(day: str, meal: str, dish_ids: list[str]) -> None:
    if not _USE_DYNAMODB:
        return
    _put_item({
        "PK": "CONFIG",
        "SK": f"SHORTLIST#{day}#{meal}",
        "dish_ids": dish_ids,
    })


def _persist_config_menu(day: str, meal: str, dish_id: str | None) -> None:
    if not _USE_DYNAMODB:
        return
    item: dict = {
        "PK": "CONFIG",
        "SK": f"MENU#{day}#{meal}",
    }
    if dish_id is not None:
        item["dish_id"] = dish_id
    _put_item(item)


def _persist_config_finalized(finalized: bool) -> None:
    if not _USE_DYNAMODB:
        return
    _put_item({
        "PK": "CONFIG",
        "SK": "FINALIZED",
        "finalized": finalized,
    })


def reset_store() -> None:
    global _dishes, _votes, _members, _vote_availability, _finalized, _final_weekly_menu, _shortlists, _manual_menu, _persistence_loaded

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
        _persist_config_availability(slot.day, slot.meal, slot.available)
    return list_vote_availability()


def list_dish_categories() -> list[DishCategory]:
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


def set_shortlist(day: Weekday, meal: Meal, dish_ids: list[str]) -> None:
    _ensure_store_loaded()
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if day not in WEEK_DAYS or meal not in MEALS:
        raise ValueError("Invalid vote slot")

    for dish_id in dish_ids:
        if dish_id not in _dishes:
            raise KeyError(f"Dish not found: {dish_id}")

    _shortlists[day][meal] = set(dish_ids)
    _persist_config_shortlist(day, meal, dish_ids)


def set_shortlists(slots: list[SetShortlistRequest]) -> None:
    _ensure_store_loaded()
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    for slot in slots:
        set_shortlist(slot.day, slot.meal, slot.dish_ids)


def set_menu_item(day: Weekday, meal: Meal, dish_id: str | None) -> WeeklyMenuResponse:
    _ensure_store_loaded()
    if _finalized:
        raise ValueError("Le menu est validé et ne peut plus être modifié")
    if day not in WEEK_DAYS or meal not in MEALS:
        raise ValueError("Invalid vote slot")
    if dish_id is not None and dish_id not in _dishes:
        raise KeyError("Dish not found")
    _manual_menu[day][meal] = dish_id
    _persist_config_menu(day, meal, dish_id)
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
    _persist_config_finalized(True)
    return _final_weekly_menu


def unvalidate_menu() -> WeeklyMenuResponse:
    _ensure_store_loaded()
    global _finalized, _final_weekly_menu

    _finalized = False
    _final_weekly_menu = None
    _persist_config_finalized(False)
    return generate_weekly_menu()


def get_slot_category(day: Weekday, meal: Meal) -> DishCategory:
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
    if _USE_DYNAMODB:
        return

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
