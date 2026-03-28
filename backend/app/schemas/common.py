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


class WeeklyMenuResponse(BaseModel):
    items: list[MenuItem]
    finalized: bool = False
    shortlists: dict[Weekday, dict[Meal, list[str]]] = Field(default_factory=dict)
