"""Tests for schemas module.

Covers Pydantic model validation and serialization.
"""

import pytest
from pydantic import ValidationError

from app.schemas.common import (
    CreateDishRequest,
    CreateVoteRequest,
    Dish,
    FamilyMember,
    AdminLoginRequest,
    AdminSessionResponse,
    MenuItem,
    MenuPeriod,
    SetMenuItemRequest,
    SetMenuSlotItemRequest,
    SetShortlistRequest,
    Vote,
    VoteSlot,
    WeeklyMenuResponse,
)


class TestDish:
    """Test Dish model."""

    def test_create_dish_with_minimal_fields(self):
        """Should create dish with only required fields."""
        dish = Dish(id="1", name="Pasta")
        assert dish.id == "1"
        assert dish.name == "Pasta"
        assert dish.tags == []
        assert dish.category == "lunch"

    def test_create_dish_with_all_fields(self):
        """Should create dish with all fields."""
        dish = Dish(
            id="2",
            name="Salad",
            tags=["vegetarian", "healthy"],
            category="dinner"
        )
        assert dish.id == "2"
        assert dish.name == "Salad"
        assert dish.tags == ["vegetarian", "healthy"]
        assert dish.category == "dinner"

    def test_dish_rejects_invalid_category(self):
        """Should reject invalid category."""
        with pytest.raises(ValidationError):
            Dish(id="1", name="Test", category="invalid")


class TestCreateDishRequest:
    """Test CreateDishRequest model."""

    def test_create_request_with_minimal_fields(self):
        """Should create request with only name."""
        request = CreateDishRequest(name="Soup")
        assert request.name == "Soup"
        assert request.tags == []
        assert request.category == "lunch"

    def test_create_request_with_all_fields(self):
        """Should create request with all fields."""
        request = CreateDishRequest(
            name="Pizza",
            tags=["italian"],
            category="weekends_lunch"
        )
        assert request.name == "Pizza"
        assert request.tags == ["italian"]
        assert request.category == "weekends_lunch"

    def test_create_request_requires_name(self):
        """Should require name field."""
        with pytest.raises(ValidationError):
            CreateDishRequest()


class TestFamilyMember:
    """Test FamilyMember model."""

    def test_create_member(self):
        """Should create family member."""
        member = FamilyMember(name="John")
        assert member.name == "John"

    def test_member_requires_name(self):
        """Should require name field."""
        with pytest.raises(ValidationError):
            FamilyMember()


class TestAdminLoginRequest:
    """Test AdminLoginRequest model."""

    def test_create_login_request(self):
        """Should create login request."""
        request = AdminLoginRequest(username="admin", password="secret")
        assert request.username == "admin"
        assert request.password == "secret"

    def test_login_request_requires_fields(self):
        """Should require username and password."""
        with pytest.raises(ValidationError):
            AdminLoginRequest()


class TestAdminSessionResponse:
    """Test AdminSessionResponse model."""

    def test_create_session_response(self):
        """Should create session response."""
        response = AdminSessionResponse(authenticated=True)
        assert response.authenticated is True


class TestVoteSlot:
    """Test VoteSlot model."""

    def test_create_vote_slot(self):
        """Should create vote slot."""
        slot = VoteSlot(day="monday", meal="lunch", available=True)
        assert slot.day == "monday"
        assert slot.meal == "lunch"
        assert slot.available is True

    def test_vote_slot_requires_fields(self):
        """Should require all fields."""
        with pytest.raises(ValidationError):
            VoteSlot()


class TestVote:
    """Test Vote model."""

    def test_create_vote(self):
        """Should create vote."""
        vote = Vote(
            user_name="John",
            dish_id="1",
            day="monday",
            meal="lunch"
        )
        assert vote.user_name == "John"
        assert vote.dish_id == "1"
        assert vote.day == "monday"
        assert vote.meal == "lunch"


class TestCreateVoteRequest:
    """Test CreateVoteRequest model."""

    def test_create_vote_request(self):
        """Should create vote request."""
        request = CreateVoteRequest(
            user_name="Jane",
            dish_id="2",
            day="tuesday",
            meal="dinner"
        )
        assert request.user_name == "Jane"
        assert request.dish_id == "2"
        assert request.day == "tuesday"
        assert request.meal == "dinner"


class TestMenuItem:
    """Test MenuItem model."""

    def test_create_menu_item_with_dish(self):
        """Should create menu item with dish."""
        dish = Dish(id="1", name="Pasta")
        item = MenuItem(day="monday", meal="lunch", dish=dish)
        assert item.day == "monday"
        assert item.meal == "lunch"
        assert item.dish == dish

    def test_create_menu_item_without_dish(self):
        """Should create menu item without dish."""
        item = MenuItem(day="tuesday", meal="dinner", dish=None)
        assert item.day == "tuesday"
        assert item.meal == "dinner"
        assert item.dish is None


class TestSetMenuItemRequest:
    """Test SetMenuItemRequest model."""

    def test_create_with_dish(self):
        """Should create request with dish."""
        request = SetMenuItemRequest(dish_id="1")
        assert request.dish_id == "1"

    def test_create_without_dish(self):
        """Should create request without dish (None)."""
        request = SetMenuItemRequest(dish_id=None)
        assert request.dish_id is None


class TestSetMenuSlotItemRequest:
    """Test SetMenuSlotItemRequest model."""

    def test_create_slot_item_request(self):
        """Should create slot item request."""
        request = SetMenuSlotItemRequest(
            day="wednesday",
            meal="lunch",
            dish_id="3"
        )
        assert request.day == "wednesday"
        assert request.meal == "lunch"
        assert request.dish_id == "3"


class TestSetShortlistRequest:
    """Test SetShortlistRequest model."""

    def test_create_shortlist_with_dishes(self):
        """Should create shortlist with dish IDs."""
        request = SetShortlistRequest(
            day="monday",
            meal="lunch",
            dish_ids=["1", "2", "3"]
        )
        assert request.day == "monday"
        assert request.meal == "lunch"
        assert request.dish_ids == ["1", "2", "3"]

    def test_create_shortlist_without_dishes(self):
        """Should create shortlist without dish IDs."""
        request = SetShortlistRequest(day="tuesday", meal="dinner")
        assert request.day == "tuesday"
        assert request.meal == "dinner"
        assert request.dish_ids == []


class TestMenuPeriod:
    """Test MenuPeriod model."""

    def test_create_period_minimal(self):
        """Should create period with minimal fields."""
        period = MenuPeriod(
            period_id="2026-04-16",
            start_date="2026-04-16",
            end_date="2026-04-23",
            display_label="16/04 - 23/04",
            created_at="2026-04-16T00:00:00"
        )
        assert period.period_id == "2026-04-16"
        assert period.finalized_at is None
        assert period.menu is None

    def test_create_period_with_menu(self):
        """Should create period with menu."""
        menu = WeeklyMenuResponse(
            period_id="2026-04-16",
            period_label="16/04 - 23/04",
            start_date="2026-04-16",
            end_date="2026-04-23",
            items=[]
        )
        period = MenuPeriod(
            period_id="2026-04-16",
            start_date="2026-04-16",
            end_date="2026-04-23",
            display_label="16/04 - 23/04",
            created_at="2026-04-16T00:00:00",
            finalized_at="2026-04-20T23:59:00",
            menu=menu
        )
        assert period.finalized_at == "2026-04-20T23:59:00"
        assert period.menu == menu


class TestWeeklyMenuResponse:
    """Test WeeklyMenuResponse model."""

    def test_create_menu_response(self):
        """Should create menu response."""
        menu = WeeklyMenuResponse(
            period_id="2026-04-16",
            period_label="16/04 - 23/04",
            start_date="2026-04-16",
            end_date="2026-04-23",
            items=[],
            finalized=False,
            shortlists={}
        )
        assert menu.period_id == "2026-04-16"
        assert menu.finalized is False
        assert menu.shortlists == {}

    def test_create_menu_with_items(self):
        """Should create menu with items."""
        dish = Dish(id="1", name="Pasta")
        item = MenuItem(day="monday", meal="lunch", dish=dish)
        menu = WeeklyMenuResponse(
            period_id="2026-04-16",
            period_label="16/04 - 23/04",
            start_date="2026-04-16",
            end_date="2026-04-23",
            items=[item]
        )
        assert len(menu.items) == 1
        assert menu.items[0].dish.name == "Pasta"
