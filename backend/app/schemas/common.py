from typing import Literal

from pydantic import BaseModel, Field


Weekday = Literal[
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]


class Dish(BaseModel):
    id: str
    name: str
    tags: list[str] = Field(default_factory=list)


class CreateDishRequest(BaseModel):
    name: str
    tags: list[str] = Field(default_factory=list)


class Vote(BaseModel):
    user_name: str
    dish_id: str
    day: Weekday


class CreateVoteRequest(BaseModel):
    user_name: str
    dish_id: str
    day: Weekday


class MenuItem(BaseModel):
    day: Weekday
    dish: Dish | None


class SetMenuItemRequest(BaseModel):
    dish_id: str | None


class WeeklyMenuResponse(BaseModel):
    items: list[MenuItem]
    finalized: bool = False
    shortlists: dict[Weekday, list[str]] = Field(default_factory=dict)
