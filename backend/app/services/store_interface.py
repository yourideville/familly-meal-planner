"""Abstract interface for the meal planner store.

This module defines the contract that all store implementations must follow.
Both InMemoryStore and DynamoDBStore implement this interface.
"""

from abc import ABC, abstractmethod

from app.schemas.common import (
    CreateDishRequest,
    CreateVoteRequest,
    Dish,
    DishCategory,
    Meal,
    MenuPeriod,
    SetShortlistRequest,
    Vote,
    VoteSlot,
    Weekday,
    WeeklyMenuResponse,
)


class StoreInterface(ABC):
    """Abstract interface for the meal planner store."""

    # -------------------------------------------------------------------------
    # Dish operations
    # -------------------------------------------------------------------------

    @abstractmethod
    def list_dishes(self) -> list[Dish]:
        """Return all dishes."""
        ...

    @abstractmethod
    def create_dish(self, payload: CreateDishRequest) -> Dish:
        """Create a new dish."""
        ...

    @abstractmethod
    def update_dish(self, dish_id: str, payload: CreateDishRequest) -> Dish:
        """Update an existing dish."""
        ...

    @abstractmethod
    def delete_dish(self, dish_id: str) -> None:
        """Delete a dish."""
        ...

    # -------------------------------------------------------------------------
    # Member operations
    # -------------------------------------------------------------------------

    @abstractmethod
    def list_members(self) -> list[str]:
        """Return all member names."""
        ...

    @abstractmethod
    def add_member(self, name: str) -> str:
        """Add a new member. Returns the member name."""
        ...

    @abstractmethod
    def update_member(self, current_name: str, new_name: str) -> str:
        """Update a member's name."""
        ...

    @abstractmethod
    def delete_member(self, name: str) -> None:
        """Delete a member."""
        ...

    # -------------------------------------------------------------------------
    # Vote operations
    # -------------------------------------------------------------------------

    @abstractmethod
    def list_votes(self) -> list[Vote]:
        """Return all votes."""
        ...

    @abstractmethod
    def add_vote(self, payload: CreateVoteRequest) -> Vote:
        """Add or update a vote for a user/day/meal slot."""
        ...

    # -------------------------------------------------------------------------
    # Vote availability
    # -------------------------------------------------------------------------

    @abstractmethod
    def list_vote_availability(self) -> list[VoteSlot]:
        """Return availability status for all day/meal slots."""
        ...

    @abstractmethod
    def set_vote_availability(self, slots: list[VoteSlot]) -> list[VoteSlot]:
        """Update availability for specified day/meal slots."""
        ...

    # -------------------------------------------------------------------------
    # Shortlist operations
    # -------------------------------------------------------------------------

    @abstractmethod
    def set_shortlist(self, day: Weekday, meal: Meal, dish_ids: list[str]) -> None:
        """Set the shortlist (candidate dishes) for a day/meal slot."""
        ...

    @abstractmethod
    def set_shortlists(self, slots: list[SetShortlistRequest]) -> None:
        """Set shortlists for multiple day/meal slots."""
        ...

    # -------------------------------------------------------------------------
    # Manual menu operations
    # -------------------------------------------------------------------------

    @abstractmethod
    def set_menu_item(self, day: Weekday, meal: Meal, dish_id: str | None) -> WeeklyMenuResponse:
        """Manually set a dish for a day/meal slot, or clear manual assignment."""
        ...

    # -------------------------------------------------------------------------
    # Menu generation and validation
    # -------------------------------------------------------------------------

    @abstractmethod
    def generate_weekly_menu(self, allow_generate_final: bool = False) -> WeeklyMenuResponse:
        """Generate the weekly menu based on votes and manual assignments."""
        ...

    @abstractmethod
    def validate_menu(self) -> WeeklyMenuResponse:
        """Finalize and lock the weekly menu."""
        ...

    @abstractmethod
    def unvalidate_menu(self) -> WeeklyMenuResponse:
        """Unvalidate and reopen the weekly menu."""
        ...

    # -------------------------------------------------------------------------
    # Utility operations
    # -------------------------------------------------------------------------

    @abstractmethod
    def list_dish_categories(self) -> list[DishCategory]:
        """Return all available dish categories."""
        ...

    @abstractmethod
    def get_slot_category(self, day: Weekday, meal: Meal) -> DishCategory:
        """Determine the dish category for a day/meal slot."""
        ...

    @abstractmethod
    def reset_store(self) -> None:
        """Reset all in-memory state (useful for testing)."""
        ...

    @abstractmethod
    def seed_data(self) -> None:
        """Create sample data for development (in-memory mode only)."""
        ...

    # -------------------------------------------------------------------------
    # Period management operations
    # -------------------------------------------------------------------------

    @abstractmethod
    def get_active_period(self) -> MenuPeriod | None:
        """Get the currently active menu period."""
        ...

    @abstractmethod
    def create_period(self, period_id: str) -> MenuPeriod:
        """Create a new menu period."""
        ...

    @abstractmethod
    def get_period(self, period_id: str) -> MenuPeriod | None:
        """Get a specific menu period by ID."""
        ...

    @abstractmethod
    def list_periods(self, limit: int = 12) -> list[MenuPeriod]:
        """List menu periods, most recent first."""
        ...

    @abstractmethod
    def archive_period(self, period_id: str) -> MenuPeriod:
        """Archive a period with its menu content for historical access."""
        ...

    @abstractmethod
    def delete_all_votes(self) -> None:
        """Delete all votes (called when menu is finalized)."""
        ...

    # -------------------------------------------------------------------------
    # Automated lifecycle operations
    # -------------------------------------------------------------------------

    def auto_finalize_if_needed(self) -> bool:
        """Check if it's time to auto-finalize and do so if needed.
        
        Returns:
            True if auto-finalization was performed, False otherwise
        """
        return False  # Default: no auto-finalization

    def ensure_active_period(self) -> MenuPeriod:
        """Ensure the current period exists and is active.
        
        Creates a new period if needed (e.g., on Tuesday after finalization).
        """
        period = self.get_active_period()
        if not period:
            from app.services import period_utils
            period_info = period_utils.get_current_period()
            period = self.create_period(period_info["period_id"])
        return period

    def is_voting_window_open(self) -> bool:
        """Check if voting is currently allowed (Friday-Sunday)."""
        from app.services import period_utils
        return period_utils.is_voting_open()

    # -------------------------------------------------------------------------
    # Session operations (DynamoDB only, no-op for in-memory)
    # -------------------------------------------------------------------------

    def save_session(self, token: str) -> None:
        """Persist an admin session token."""
        pass  # Optional: only needed for DynamoDB mode

    def delete_session(self, token: str) -> None:
        """Remove an admin session token."""
        pass  # Optional: only needed for DynamoDB mode

    def session_exists(self, token: str) -> bool:
        """Check whether a session token is valid."""
        return False  # Default: no session support in in-memory mode

    def invalidate_store_cache(self) -> None:
        """Mark the in-memory cache as stale."""
        pass  # Optional: only needed for DynamoDB mode
