"""Pure in-memory implementation of the meal planner store.

This implementation keeps all state in memory with no persistence.
Ideal for local development and testing.
"""

from collections import Counter
from uuid import uuid4

from app.schemas.common import (
    CreateDishRequest,
    CreateVoteRequest,
    Dish,
    DishCategory,
    FamilyMember,
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

logger = __import__("logging").getLogger(__name__)

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


class InMemoryStore(StoreInterface):
    """In-memory store implementation."""

    def __init__(self) -> None:
        """Initialize empty in-memory state."""
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
        self._periods: dict[str, MenuPeriod] = {}  # period_id -> MenuPeriod
        self._active_period_id: str | None = None

    # -------------------------------------------------------------------------
    # Dish operations
    # -------------------------------------------------------------------------

    def list_dishes(self) -> list[Dish]:
        return list(self._dishes.values())

    def create_dish(self, payload: CreateDishRequest) -> Dish:
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        dish = Dish(
            id=str(uuid4()),
            name=payload.name,
            tags=payload.tags,
            category=payload.category,
        )
        self._dishes[dish.id] = dish
        return dish

    def update_dish(self, dish_id: str, payload: CreateDishRequest) -> Dish:
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        if dish_id not in self._dishes:
            raise KeyError("Dish not found")

        dish = self._dishes[dish_id]
        dish.name = payload.name
        dish.tags = payload.tags
        dish.category = payload.category
        self._dishes[dish_id] = dish
        return dish

    def delete_dish(self, dish_id: str) -> None:
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        if dish_id not in self._dishes:
            raise KeyError("Dish not found")

        self._dishes.pop(dish_id)

    # -------------------------------------------------------------------------
    # Member operations
    # -------------------------------------------------------------------------

    def list_members(self) -> list[str]:
        return list(self._members)

    def add_member(self, name: str) -> str:
        if not name.strip():
            raise ValueError("Member name cannot be empty")
        if name in self._members:
            raise ValueError("Member already exists")
        self._members.append(name)
        return name

    def update_member(self, current_name: str, new_name: str) -> str:
        if current_name not in self._members:
            raise KeyError("Member not found")
        if not new_name.strip():
            raise ValueError("Member name cannot be empty")
        if new_name != current_name and new_name in self._members:
            raise ValueError("Member already exists")
        index = self._members.index(current_name)
        self._members[index] = new_name
        self._update_votes_member_name(current_name, new_name)
        return new_name

    def delete_member(self, name: str) -> None:
        if name not in self._members:
            raise KeyError("Member not found")
        self._members.remove(name)
        self._votes[:] = [vote for vote in self._votes if vote.user_name != name]

    # -------------------------------------------------------------------------
    # Vote operations
    # -------------------------------------------------------------------------

    def list_votes(self) -> list[Vote]:
        return self._votes

    def add_vote(self, payload: CreateVoteRequest) -> Vote:
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
            return existing_vote

        vote = Vote(
            user_name=payload.user_name,
            dish_id=payload.dish_id,
            day=payload.day,
            meal=payload.meal,
        )
        self._votes.append(vote)
        return vote

    # -------------------------------------------------------------------------
    # Vote availability
    # -------------------------------------------------------------------------

    def list_vote_availability(self) -> list[VoteSlot]:
        slots: list[VoteSlot] = []
        for day in WEEK_DAYS:
            for meal in MEALS:
                slots.append(
                    VoteSlot(
                        day=day, meal=meal, available=self._vote_availability[day][meal]
                    )
                )
        return slots

    def set_vote_availability(self, slots: list[VoteSlot]) -> list[VoteSlot]:
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        for slot in slots:
            if slot.day not in WEEK_DAYS or slot.meal not in MEALS:
                raise ValueError("Invalid vote slot")
            self._vote_availability[slot.day][slot.meal] = slot.available
        return self.list_vote_availability()

    # -------------------------------------------------------------------------
    # Shortlist operations
    # -------------------------------------------------------------------------

    def set_shortlist(self, day: Weekday, meal: Meal, dish_ids: list[str]) -> None:
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        if day not in WEEK_DAYS or meal not in MEALS:
            raise ValueError("Invalid vote slot")

        for dish_id in dish_ids:
            if dish_id not in self._dishes:
                raise KeyError(f"Dish not found: {dish_id}")

        self._shortlists[day][meal] = set(dish_ids)

    def set_shortlists(self, slots: list[SetShortlistRequest]) -> None:
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        for slot in slots:
            self.set_shortlist(slot.day, slot.meal, slot.dish_ids)

    # -------------------------------------------------------------------------
    # Manual menu operations
    # -------------------------------------------------------------------------

    def set_menu_item(self, day: Weekday, meal: Meal, dish_id: str | None) -> WeeklyMenuResponse:
        if self._finalized:
            raise ValueError("Le menu est validé et ne peut plus être modifié")
        if day not in WEEK_DAYS or meal not in MEALS:
            raise ValueError("Invalid vote slot")
        if dish_id is not None and dish_id not in self._dishes:
            raise KeyError("Dish not found")
        self._manual_menu[day][meal] = dish_id
        return self.generate_weekly_menu()

    # -------------------------------------------------------------------------
    # Menu generation and validation
    # -------------------------------------------------------------------------

    def generate_weekly_menu(self, allow_generate_final: bool = False) -> WeeklyMenuResponse:
        if self._finalized and self._final_weekly_menu is not None and not allow_generate_final:
            return self._final_weekly_menu

        items: list[MenuItem] = []
        for day in WEEK_DAYS:
            for meal in MEALS:
                manual_dish_id = self._manual_menu[day][meal]
                if manual_dish_id is not None:
                    items.append(
                        MenuItem(day=day, meal=meal, dish=self._dishes.get(manual_dish_id))
                    )
                    continue

                day_meal_votes = [
                    v for v in self._votes if v.day == day and v.meal == meal
                ]
                whitelist = self._shortlists[day][meal]

                if whitelist:
                    day_meal_votes = [v for v in day_meal_votes if v.dish_id in whitelist]

                if not day_meal_votes:
                    items.append(MenuItem(day=day, meal=meal, dish=None))
                    continue

                slot_category = self.get_slot_category(day, meal)
                eligible_dish_ids = [
                    dish.id for dish in self._dishes.values() if dish.category == slot_category
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
        return self._final_weekly_menu

    def unvalidate_menu(self) -> WeeklyMenuResponse:
        self._finalized = False
        self._final_weekly_menu = None
        return self.generate_weekly_menu()

    # -------------------------------------------------------------------------
    # Utility operations
    # -------------------------------------------------------------------------

    def list_dish_categories(self) -> list[DishCategory]:
        return ["lunch", "dinner", "weekends_lunch", "saturday_dinner"]

    def get_slot_category(self, day: Weekday, meal: Meal) -> DishCategory:
        if meal == "lunch":
            return "weekends_lunch" if day in ["saturday", "sunday"] else "lunch"
        if meal == "dinner":
            return "saturday_dinner" if day == "saturday" else "dinner"
        return "dinner"

    def reset_store(self) -> None:
        """Reset all in-memory state."""
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

    def seed_data(self) -> None:
        """Create sample data for development."""
        if self._dishes:
            return

        self.reset_store()

        for name, tags, category in [
            ("Spaghetti Bolognese", ["pasta", "beef"], "lunch"),
            ("Chicken Curry", ["spicy", "rice"], "dinner"),
            ("Vegetable Stir Fry", ["veggie", "quick"], "weekends_lunch"),
            ("Grilled Salmon", ["fish", "healthy"], "saturday_dinner"),
        ]:
            self.create_dish(CreateDishRequest(name=name, tags=tags, category=category))

        for member in ["Alice", "Bob", "Cara"]:
            self.add_member(member)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _update_votes_member_name(self, current_name: str, new_name: str) -> None:
        """Update member name in all votes."""
        for vote in self._votes:
            if vote.user_name == current_name:
                vote.user_name = new_name

    # -------------------------------------------------------------------------
    # Period management operations
    # -------------------------------------------------------------------------

    def get_active_period(self) -> MenuPeriod | None:
        """Get the currently active menu period."""
        if not self._active_period_id:
            # Auto-create current period if it doesn't exist
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
            # Calculate period info from the period_id (which is the start date)
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
        
        return period

    def get_period(self, period_id: str) -> MenuPeriod | None:
        """Get a specific menu period by ID."""
        return self._periods.get(period_id)

    def list_periods(self, limit: int = 12) -> list[MenuPeriod]:
        """List menu periods, most recent first."""
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
        period.finalized_at = __import__("datetime").datetime.now().isoformat()
        
        return period

    def delete_all_votes(self) -> None:
        """Delete all votes."""
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
