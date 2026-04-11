from typing import Literal

from pydantic import BaseModel, Field


Weekday = Literal[
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

Meal = Literal["lunch", "dinner"]
DishCategory = Literal["lunch", "dinner", "weekends_lunch", "saturday_dinner"]


class Dish(BaseModel):
    id: str
    name: str
    tags: list[str] = Field(default_factory=list)
    category: DishCategory = "lunch"


class CreateDishRequest(BaseModel):
    name: str
    tags: list[str] = Field(default_factory=list)
    category: DishCategory = "lunch"


class FamilyMember(BaseModel):
    name: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminSessionResponse(BaseModel):
    authenticated: bool


class VoteSlot(BaseModel):
    day: Weekday
    meal: Meal
    available: bool


class Vote(BaseModel):
    user_name: str
    dish_id: str
    day: Weekday
    meal: Meal


class CreateVoteRequest(BaseModel):
    user_name: str
    dish_id: str
    day: Weekday
    meal: Meal


class MenuItem(BaseModel):
    day: Weekday
    meal: Meal
    dish: Dish | None


class SetMenuItemRequest(BaseModel):
    dish_id: str | None


class SetMenuSlotItemRequest(BaseModel):
    day: Weekday
    meal: Meal
    dish_id: str | None


class SetShortlistRequest(BaseModel):
    day: Weekday
    meal: Meal
    dish_ids: list[str] = Field(default_factory=list)


class MenuPeriod(BaseModel):
    """Represents a menu period (Thursday to Wednesday cycle)."""
    period_id: str  # e.g., "2026-04-16" (start date)
    start_date: str  # ISO date string (Thursday)
    end_date: str  # ISO date string (following Wednesday)
    display_label: str  # e.g., "16/04 - 23/04"
    created_at: str  # ISO timestamp when period was created
    finalized_at: str | None = None  # ISO timestamp when menu was finalized
    menu: "WeeklyMenuResponse | None" = None  # The actual menu content (None for historical periods)


class WeeklyMenuResponse(BaseModel):
    period_id: str  # e.g., "2026-04-16"
    period_label: str  # e.g., "16/04 - 23/04"
    start_date: str  # ISO date string (Thursday)
    end_date: str  # ISO date string (following Wednesday)
    items: list[MenuItem]
    finalized: bool = False
    shortlists: dict[Weekday, dict[Meal, list[str]]] = Field(default_factory=dict)
