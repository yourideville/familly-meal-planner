"""DynamoDB implementation of the meal planner store.

This implementation uses a single-table DynamoDB design for persistence.
All state is loaded once at initialization and persisted on every change.
"""

import logging
import os
from collections import Counter
from uuid import uuid4

import boto3

from app.schemas.common import (
    CreateDishRequest,
    CreateVoteRequest,
    Dish,
    DishCategory,
    Meal,
    MenuItem,
    MenuPeriod,
    SetShortlistRequest,
    Vote,
    VoteSlot,
    Weekday,
    WeeklyMenuResponse,
)
from app.services.store_interface import StoreInterface
from app.services import period_utils

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


class DynamoDBStore(StoreInterface):
    """DynamoDB-backed store implementation with in-memory cache."""

    def __init__(self) -> None:
        """Initialize DynamoDB connection and load state."""
        self._table = None
        self._persistence_loaded = False

        # In-memory cache (same structure as InMemoryStore)
        self._dishes: dict[str, Dish] = {}
        self._votes: list[Vote] = []
        self._members: list[str] = []
        self._vote_availability: dict[str, dict[Meal, bool]] = {
            day: {meal: True for meal in MEALS} for day in WEEK_DAYS
        }
        self._finalized: bool = False
        self._final_weekly_menu: WeeklyMenuResponse | None = None
        self._shortlists: dict[str, dict[Meal, set[str]]] = {
            day: {meal: set() for meal in MEALS} for day in WEEK_DAYS
        }
        self._manual_menu: dict[str, dict[Meal, str | None]] = {
            day: {meal: None for meal in MEALS} for day in WEEK_DAYS
        }
        
        # Period management
        self._periods: dict[str, MenuPeriod] = {}
        self._active_period_id: str | None = None

        # Initialize DynamoDB
        try:
            dynamodb_resource = boto3.resource("dynamodb")
            self._table = dynamodb_resource.Table(os.environ["TABLE_NAME"])
            logger.info("DynamoDB connection established")
        except KeyError as exc:
            raise RuntimeError(
                "TABLE_NAME must be configured in environment variables"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Failed to connect to DynamoDB: {exc}") from exc

    # -------------------------------------------------------------------------
    # Public interface methods
    # -------------------------------------------------------------------------

    def list_dishes(self) -> list[Dish]:
        self._ensure_store_loaded()
        return list(self._dishes.values())

    def create_dish(self, payload: CreateDishRequest) -> Dish:
        self._ensure_store_loaded()
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        dish = Dish(
            id=str(uuid4()),
            name=payload.name,
            tags=payload.tags,
            category=payload.category,
        )
        self._dishes[dish.id] = dish
        self._persist_dish(dish)
        return dish

    def update_dish(self, dish_id: str, payload: CreateDishRequest) -> Dish:
        self._ensure_store_loaded()
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        if dish_id not in self._dishes:
            raise KeyError("Dish not found")

        dish = self._dishes[dish_id]
        dish.name = payload.name
        dish.tags = payload.tags
        dish.category = payload.category
        self._dishes[dish_id] = dish
        self._persist_dish(dish)
        return dish

    def delete_dish(self, dish_id: str) -> None:
        self._ensure_store_loaded()
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        if dish_id not in self._dishes:
            raise KeyError("Dish not found")

        self._dishes.pop(dish_id)
        self._delete_dish_from_db(dish_id)

    def list_members(self) -> list[str]:
        self._ensure_store_loaded()
        return list(self._members)

    def add_member(self, name: str) -> str:
        self._ensure_store_loaded()
        if not name.strip():
            raise ValueError("Member name cannot be empty")
        if name in self._members:
            raise ValueError("Member already exists")
        self._members.append(name)
        self._persist_member(name)
        return name

    def update_member(self, current_name: str, new_name: str) -> str:
        self._ensure_store_loaded()
        if current_name not in self._members:
            raise KeyError("Member not found")
        if not new_name.strip():
            raise ValueError("Member name cannot be empty")
        if new_name != current_name and new_name in self._members:
            raise ValueError("Member already exists")
        index = self._members.index(current_name)
        self._members[index] = new_name
        self._delete_member_from_db(current_name)
        self._persist_member(new_name)
        self._update_votes_member_name(current_name, new_name)
        return new_name

    def delete_member(self, name: str) -> None:
        self._ensure_store_loaded()
        if name not in self._members:
            raise KeyError("Member not found")
        self._delete_votes_for_member(name)
        self._members.remove(name)
        self._votes[:] = [vote for vote in self._votes if vote.user_name != name]
        self._delete_member_from_db(name)

    def list_votes(self) -> list[Vote]:
        self._ensure_store_loaded()
        return self._votes

    def add_vote(self, payload: CreateVoteRequest) -> Vote:
        self._ensure_store_loaded()
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus recevoir de votes")
        
        # Check if voting window is open (Friday-Sunday)
        if not self.is_voting_window_open():
            raise ValueError("Le vote n'est ouvert que du vendredi au dimanche")
        
        if payload.dish_id not in self._dishes:
            raise KeyError("Dish not found")
        if payload.user_name not in self._members:
            raise ValueError("Member not found")
        if not self._vote_availability[payload.day][payload.meal]:
            raise ValueError("Slot not available")

        existing_vote = next(
            (
                vote
                for vote in self._votes
                if vote.user_name == payload.user_name
                and vote.day == payload.day
                and vote.meal == payload.meal
            ),
            None,
        )
        if existing_vote is not None:
            existing_vote.dish_id = payload.dish_id
            self._persist_vote(existing_vote)
            return existing_vote

        vote = Vote(
            user_name=payload.user_name,
            dish_id=payload.dish_id,
            day=payload.day,
            meal=payload.meal,
        )
        self._votes.append(vote)
        self._persist_vote(vote)
        return vote

    def list_vote_availability(self) -> list[VoteSlot]:
        self._ensure_store_loaded()
        slots: list[VoteSlot] = []
        for day in WEEK_DAYS:
            for meal in MEALS:
                slots.append(
                    VoteSlot(
                        day=day,
                        meal=meal,
                        available=self._vote_availability[day][meal],
                    )
                )
        return slots

    def set_vote_availability(self, slots: list[VoteSlot]) -> list[VoteSlot]:
        self._ensure_store_loaded()
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        for slot in slots:
            if slot.day not in WEEK_DAYS or slot.meal not in MEALS:
                raise ValueError("Invalid vote slot")
            self._vote_availability[slot.day][slot.meal] = slot.available
            self._persist_config_availability(slot.day, slot.meal, slot.available)
        return self.list_vote_availability()

    def set_shortlist(self, day: Weekday, meal: Meal, dish_ids: list[str]) -> None:
        self._ensure_store_loaded()
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        if day not in WEEK_DAYS or meal not in MEALS:
            raise ValueError("Invalid vote slot")

        for dish_id in dish_ids:
            if dish_id not in self._dishes:
                raise KeyError(f"Dish not found: {dish_id}")

        self._shortlists[day][meal] = set(dish_ids)
        self._persist_config_shortlist(day, meal, dish_ids)

    def set_shortlists(self, slots: list[SetShortlistRequest]) -> None:
        self._ensure_store_loaded()
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        for slot in slots:
            self.set_shortlist(slot.day, slot.meal, slot.dish_ids)

    def set_menu_item(
        self, day: Weekday, meal: Meal, dish_id: str | None
    ) -> WeeklyMenuResponse:
        self._ensure_store_loaded()
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        if day not in WEEK_DAYS or meal not in MEALS:
            raise ValueError("Invalid vote slot")
        if dish_id is not None and dish_id not in self._dishes:
            raise KeyError("Dish not found")
        self._manual_menu[day][meal] = dish_id
        self._persist_config_menu(day, meal, dish_id)
        return self.generate_weekly_menu()

    def generate_weekly_menu(
        self, allow_generate_final: bool = False
    ) -> WeeklyMenuResponse:
        self._ensure_store_loaded()
        if (
            self._finalized
            and self._final_weekly_menu is not None
            and not allow_generate_final
        ):
            return self._final_weekly_menu

        items: list[MenuItem] = []
        for day in WEEK_DAYS:
            for meal in MEALS:
                manual_dish_id = self._manual_menu[day][meal]
                if manual_dish_id is not None:
                    items.append(
                        MenuItem(
                            day=day, meal=meal, dish=self._dishes.get(manual_dish_id)
                        )
                    )
                    continue

                day_meal_votes = [
                    v for v in self._votes if v.day == day and v.meal == meal
                ]
                whitelist = self._shortlists[day][meal]

                if whitelist:
                    day_meal_votes = [
                        v for v in day_meal_votes if v.dish_id in whitelist
                    ]

                if not day_meal_votes:
                    items.append(MenuItem(day=day, meal=meal, dish=None))
                    continue

                slot_category = self.get_slot_category(day, meal)
                eligible_dish_ids = [
                    dish.id
                    for dish in self._dishes.values()
                    if dish.category == slot_category
                ]
                if eligible_dish_ids:
                    day_meal_votes = [
                        v for v in day_meal_votes if v.dish_id in eligible_dish_ids
                    ]

                if not day_meal_votes:
                    items.append(MenuItem(day=day, meal=meal, dish=None))
                    continue

                ranking = Counter(v.dish_id for v in day_meal_votes)
                winner_id = ranking.most_common(1)[0][0]
                items.append(
                    MenuItem(day=day, meal=meal, dish=self._dishes.get(winner_id))
                )

        # Get current period info
        period = self.get_active_period()
        if period:
            period_id = period.period_id
            period_label = period.display_label
            start_date = period.start_date
            end_date = period.end_date
        else:
            # Fallback for backward compatibility
            period_info = period_utils.get_current_period()
            period_id = period_info["period_id"]
            period_label = period_info["display_label"]
            start_date = period_info["start_date"]
            end_date = period_info["end_date"]

        response = WeeklyMenuResponse(
            period_id=period_id,
            period_label=period_label,
            start_date=start_date,
            end_date=end_date,
            items=items,
            finalized=self._finalized,
            shortlists={
                day: {meal: list(self._shortlists[day][meal]) for meal in MEALS}
                for day in WEEK_DAYS
            },
        )
        return response

    def validate_menu(self) -> WeeklyMenuResponse:
        self._ensure_store_loaded()
        if self._finalized and self._final_weekly_menu is not None:
            return self._final_weekly_menu

        # Archive current period with menu
        if self._active_period_id:
            self.archive_period(self._active_period_id)
        
        # Delete all votes
        self.delete_all_votes()

        self._final_weekly_menu = self.generate_weekly_menu(allow_generate_final=True)
        self._finalized = True
        self._final_weekly_menu = WeeklyMenuResponse(
            period_id=self._final_weekly_menu.period_id,
            period_label=self._final_weekly_menu.period_label,
            start_date=self._final_weekly_menu.start_date,
            end_date=self._final_weekly_menu.end_date,
            items=self._final_weekly_menu.items,
            finalized=True,
            shortlists=self._final_weekly_menu.shortlists,
        )
        self._persist_config_finalized(True)
        return self._final_weekly_menu

    def unvalidate_menu(self) -> WeeklyMenuResponse:
        self._ensure_store_loaded()
        
        self._finalized = False
        self._final_weekly_menu = None
        self._persist_config_finalized(False)
        return self.generate_weekly_menu()

    def list_dish_categories(self) -> list[DishCategory]:
        return ["lunch", "dinner", "weekends_lunch", "saturday_dinner"]

    def get_slot_category(self, day: Weekday, meal: Meal) -> DishCategory:
        if meal == "lunch":
            return "weekends_lunch" if day in ["saturday", "sunday"] else "lunch"
        if meal == "dinner":
            return "saturday_dinner" if day == "saturday" else "dinner"
        return "dinner"

    def reset_store(self) -> None:
        """Reset in-memory cache and mark as unloaded."""
        self._dishes.clear()
        self._votes.clear()
        self._members.clear()
        self._finalized = False
        self._final_weekly_menu = None
        self._vote_availability = {
            day: {meal: True for meal in MEALS} for day in WEEK_DAYS
        }
        self._shortlists = {
            day: {meal: set() for meal in MEALS} for day in WEEK_DAYS
        }
        self._manual_menu = {
            day: {meal: None for meal in MEALS} for day in WEEK_DAYS
        }
        self._periods.clear()
        self._active_period_id = None
        self._persistence_loaded = False

    def seed_data(self) -> None:
        """No-op for DynamoDB mode (data should be loaded from DynamoDB)."""
        pass

    # -------------------------------------------------------------------------
    # Session operations
    # -------------------------------------------------------------------------

    def save_session(self, token: str) -> None:
        """Persist an admin session token."""
        self._put_item({"PK": f"SESSION#{token}", "SK": "METADATA"})

    def delete_session(self, token: str) -> None:
        """Remove an admin session token."""
        self._delete_item(f"SESSION#{token}", "METADATA")

    def session_exists(self, token: str) -> bool:
        """Check whether a session token is valid."""
        resp = self._table.get_item(
            Key={"PK": f"SESSION#{token}", "SK": "METADATA"}
        )
        return "Item" in resp

    def invalidate_store_cache(self) -> None:
        """Mark the in-memory cache as stale so the next operation reloads."""
        self._persistence_loaded = False

    # -------------------------------------------------------------------------
    # Data loading from DynamoDB
    # -------------------------------------------------------------------------

    def _ensure_store_loaded(self) -> None:
        """Load state from DynamoDB if not already loaded."""
        if self._persistence_loaded:
            return
        logger.info("Loading persistent state from DynamoDB")
        self._load_dishes_from_db()
        self._load_members_from_db()
        self._load_votes_from_db()
        self._load_config_from_db()
        self._persistence_loaded = True

    def _load_dishes_from_db(self) -> None:
        """Load all dishes from DynamoDB."""
        for item in self._query_gsi1("DISHES"):
            dish = Dish(
                id=item["PK"].removeprefix("DISH#"),
                name=item["name"],
                tags=item.get("tags", []),
                category=item["category"],
            )
            self._dishes[dish.id] = dish

    def _load_members_from_db(self) -> None:
        """Load all members from DynamoDB."""
        for item in self._query_gsi1("MEMBERS"):
            self._members.append(item["PK"].removeprefix("MEMBER#"))

    def _load_votes_from_db(self) -> None:
        """Load all votes from DynamoDB."""
        seen: set[tuple[str, str, str]] = set()
        for day in WEEK_DAYS:
            for meal in MEALS:
                for item in self._query_pk(f"SLOT#{day}#{meal}"):
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
                        self._votes.append(vote)

    def _load_config_from_db(self) -> None:
        """Load configuration (availability, shortlists, menu, finalized) from DynamoDB."""
        for item in self._query_pk("CONFIG"):
            sk: str = item["SK"]
            if sk.startswith("AVAIL#"):
                parts = sk.removeprefix("AVAIL#").split("#")
                day, meal = parts[0], parts[1]
                self._vote_availability[day][meal] = item["available"]
            elif sk.startswith("SHORTLIST#"):
                parts = sk.removeprefix("SHORTLIST#").split("#")
                day, meal = parts[0], parts[1]
                self._shortlists[day][meal] = set(item.get("dish_ids", []))
            elif sk.startswith("MENU#"):
                parts = sk.removeprefix("MENU#").split("#")
                day, meal = parts[0], parts[1]
                self._manual_menu[day][meal] = item.get("dish_id")
            elif sk == "FINALIZED":
                self._finalized = item.get("finalized", False)

    # -------------------------------------------------------------------------
    # Period management operations
    # -------------------------------------------------------------------------

    def get_active_period(self) -> MenuPeriod | None:
        """Get the currently active menu period."""
        if not self._active_period_id:
            # Load from DynamoDB
            self._load_periods_from_db()
            
            # If still no active period, create one
            if not self._active_period_id:
                period_info = period_utils.get_current_period()
                self._create_period(period_info["period_id"])
        
        return self._periods.get(self._active_period_id)

    def create_period(self, period_id: str) -> MenuPeriod:
        """Create a new menu period."""
        return self._create_period(period_id)

    def _create_period(self, period_id: str) -> MenuPeriod:
        """Internal method to create a period."""
        from datetime import datetime
        
        # Get period info
        if period_id == period_utils.get_current_period()["period_id"]:
            period_info = period_utils.get_current_period()
        else:
            period_info = period_utils.get_period_from_date(period_id)
        
        period = MenuPeriod(
            period_id=period_id,
            start_date=period_info["start_date"],
            end_date=period_info["end_date"],
            display_label=period_info["display_label"],
            created_at=datetime.now().isoformat(),
            finalized_at=None,
            menu=None,
        )
        
        self._periods[period_id] = period
        self._active_period_id = period_id
        
        # Persist to DynamoDB
        self._persist_period(period)
        
        return period

    def get_period(self, period_id: str) -> MenuPeriod | None:
        """Get a specific menu period by ID."""
        if period_id not in self._periods:
            self._load_periods_from_db()
        return self._periods.get(period_id)

    def list_periods(self, limit: int = 12) -> list[MenuPeriod]:
        """List menu periods, most recent first."""
        if not self._periods:
            self._load_periods_from_db()
        
        periods = sorted(
            self._periods.values(),
            key=lambda p: p.created_at,
            reverse=True,
        )
        return periods[:limit]

    def archive_period(self, period_id: str) -> MenuPeriod:
        """Archive a period with its menu content for historical access."""
        period = self._periods.get(period_id)
        if not period:
            raise KeyError(f"Period not found: {period_id}")
        
        # Generate and store the menu for this period
        menu = self.generate_weekly_menu()
        period.menu = menu
        
        from datetime import datetime
        period.finalized_at = datetime.now().isoformat()
        
        # Persist archived period
        self._persist_period(period)
        
        return period

    def delete_all_votes(self) -> None:
        """Delete all votes from DynamoDB and in-memory cache."""
        # Delete from DynamoDB
        self._delete_all_votes_from_db()
        
        # Clear in-memory cache
        self._votes.clear()

    # -------------------------------------------------------------------------
    # Automated lifecycle operations
    # -------------------------------------------------------------------------

    def auto_finalize_if_needed(self) -> bool:
        """Check if it's Monday 23:59 and auto-finalize if needed."""
        if self._finalized:
            return False  # Already finalized
        
        if period_utils.is_finalization_time():
            try:
                self.validate_menu()
                logger.info("Auto-finalized menu on Monday 23:59")
                return True
            except Exception as e:
                logger.error(f"Auto-finalization failed: {e}")
                return False
        
        return False

    def is_voting_window_open(self) -> bool:
        """Check if voting is currently allowed (Friday-Sunday)."""
        return period_utils.is_voting_open()

    def _load_periods_from_db(self) -> None:
        """Load all menu periods from DynamoDB."""
        for item in self._query_gsi1("PERIODS"):
            period_id = item["PK"].removeprefix("PERIOD#")
            period = MenuPeriod(
                period_id=period_id,
                start_date=item["start_date"],
                end_date=item["end_date"],
                display_label=item["display_label"],
                created_at=item["created_at"],
                finalized_at=item.get("finalized_at"),
                menu=None,  # Don't load full menu in list view
            )
            self._periods[period_id] = period
            
            # Set active period if marked
            if item.get("is_active"):
                self._active_period_id = period_id

    def _persist_period(self, period: MenuPeriod) -> None:
        """Persist a menu period to DynamoDB."""
        item: dict = {
            "PK": f"PERIOD#{period.period_id}",
            "SK": "METADATA",
            "GSI1PK": "PERIODS",
            "GSI1SK": f"PERIOD#{period.period_id}",
            "start_date": period.start_date,
            "end_date": period.end_date,
            "display_label": period.display_label,
            "created_at": period.created_at,
        }
        if period.finalized_at:
            item["finalized_at"] = period.finalized_at
        if period.period_id == self._active_period_id:
            item["is_active"] = True
        
        self._put_item(item)

    def _delete_all_votes_from_db(self) -> None:
        """Delete all votes from DynamoDB."""
        for day in WEEK_DAYS:
            for meal in MEALS:
                # Query all votes for this slot
                for item in self._query_pk(f"SLOT#{day}#{meal}"):
                    user_name = item["SK"].removeprefix("USER#")
                    self._delete_vote_from_db(user_name, day, meal)

    # -------------------------------------------------------------------------
    # DynamoDB operations
    # -------------------------------------------------------------------------

    def _query_pk(self, pk: str) -> list[dict]:
        """Query all items sharing a partition key."""
        items: list[dict] = []
        response = self._table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={":pk": pk},
        )
        items.extend(response.get("Items", []))
        while response.get("LastEvaluatedKey"):
            response = self._table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={":pk": pk},
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        return items

    def _query_gsi1(self, gsi1pk: str) -> list[dict]:
        """Query all items sharing a GSI1 partition key."""
        items: list[dict] = []
        response = self._table.query(
            IndexName="GSI1",
            KeyConditionExpression="GSI1PK = :pk",
            ExpressionAttributeValues={":pk": gsi1pk},
        )
        items.extend(response.get("Items", []))
        while response.get("LastEvaluatedKey"):
            response = self._table.query(
                IndexName="GSI1",
                KeyConditionExpression="GSI1PK = :pk",
                ExpressionAttributeValues={":pk": gsi1pk},
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))
        return items

    def _put_item(self, item: dict) -> None:
        """Put an item into DynamoDB."""
        self._table.put_item(Item=item)

    def _delete_item(self, pk: str, sk: str) -> None:
        """Delete an item from DynamoDB."""
        self._table.delete_item(Key={"PK": pk, "SK": sk})

    def _persist_dish(self, dish: Dish) -> None:
        self._put_item(
            {
                "PK": f"DISH#{dish.id}",
                "SK": "METADATA",
                "GSI1PK": "DISHES",
                "GSI1SK": f"DISH#{dish.id}",
                "name": dish.name,
                "tags": dish.tags,
                "category": dish.category,
            }
        )

    def _delete_dish_from_db(self, dish_id: str) -> None:
        self._delete_item(f"DISH#{dish_id}", "METADATA")

    def _persist_member(self, name: str) -> None:
        self._put_item(
            {
                "PK": f"MEMBER#{name}",
                "SK": "METADATA",
                "GSI1PK": "MEMBERS",
                "GSI1SK": f"MEMBER#{name}",
            }
        )

    def _delete_member_from_db(self, name: str) -> None:
        self._delete_item(f"MEMBER#{name}", "METADATA")

    def _persist_vote(self, vote: Vote) -> None:
        self._put_item(
            {
                "PK": f"SLOT#{vote.day}#{vote.meal}",
                "SK": f"USER#{vote.user_name}",
                "GSI1PK": f"USER#{vote.user_name}",
                "GSI1SK": f"SLOT#{vote.day}#{vote.meal}",
                "dish_id": vote.dish_id,
            }
        )

    def _delete_vote_from_db(self, user_name: str, day: str, meal: str) -> None:
        self._delete_item(f"SLOT#{day}#{meal}", f"USER#{user_name}")

    def _delete_votes_for_member(self, name: str) -> None:
        for vote in self._votes:
            if vote.user_name == name:
                self._delete_vote_from_db(name, vote.day, vote.meal)

    def _update_votes_member_name(self, current_name: str, new_name: str) -> None:
        for vote in self._votes:
            if vote.user_name == current_name:
                self._delete_vote_from_db(current_name, vote.day, vote.meal)
                vote.user_name = new_name
                self._persist_vote(vote)

    def _persist_config_availability(
        self, day: str, meal: str, available: bool
    ) -> None:
        self._put_item(
            {
                "PK": "CONFIG",
                "SK": f"AVAIL#{day}#{meal}",
                "available": available,
            }
        )

    def _persist_config_shortlist(
        self, day: str, meal: str, dish_ids: list[str]
    ) -> None:
        self._put_item(
            {
                "PK": "CONFIG",
                "SK": f"SHORTLIST#{day}#{meal}",
                "dish_ids": dish_ids,
            }
        )

    def _persist_config_menu(self, day: str, meal: str, dish_id: str | None) -> None:
        item: dict = {
            "PK": "CONFIG",
            "SK": f"MENU#{day}#{meal}",
        }
        if dish_id is not None:
            item["dish_id"] = dish_id
        self._put_item(item)

    def _persist_config_finalized(self, finalized: bool) -> None:
        self._put_item(
            {
                "PK": "CONFIG",
                "SK": "FINALIZED",
                "finalized": finalized,
            }
        )
