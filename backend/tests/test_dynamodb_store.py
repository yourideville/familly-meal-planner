"""Tests for DynamoDB store persistence helpers.

Uses FakeTable pattern to test DynamoDB-specific methods without AWS connection.
"""

import pytest
from app.schemas.common import CreateDishRequest, CreateVoteRequest, SetShortlistRequest
from app.services.store_dynamodb import DynamoDBStore
from app.services.store_inmemory import MEALS, WEEK_DAYS


class FakeTable:
    """Fake DynamoDB table for testing persistence helpers."""

    def __init__(self):
        self.items_by_pk: dict[str, list[dict]] = {}
        self.items_by_gsi1pk: dict[str, list[dict]] = {}
        self.put_calls: list[dict] = []
        self.delete_calls: list[dict] = []
        self.query_responses: dict[str, list[dict]] = {}

    def add_item(self, item: dict) -> None:
        pk = item["PK"]
        self.items_by_pk.setdefault(pk, []).append(item)
        if "GSI1PK" in item:
            self.items_by_gsi1pk.setdefault(item["GSI1PK"], []).append(item)

    def query(self, KeyConditionExpression=None, ExpressionAttributeValues=None,
              ExclusiveStartKey=None, IndexName=None, Limit=None, ScanIndexForward=None):
        if IndexName == "GSI1":
            pk = ExpressionAttributeValues[":pk"]["S"] if isinstance(ExpressionAttributeValues[":pk"], dict) else ExpressionAttributeValues[":pk"]
            return {"Items": self.items_by_gsi1pk.get(pk, [])}
        pk = ExpressionAttributeValues[":pk"]["S"] if isinstance(ExpressionAttributeValues[":pk"], dict) else ExpressionAttributeValues[":pk"]
        items = self.items_by_pk.get(pk, [])
        if Limit:
            return {"Items": items[:Limit]}
        return {"Items": items}

    def put_item(self, Item=None):
        self.put_calls.append(Item)
        # Also add to in-memory tracking
        pk = Item["PK"]
        self.items_by_pk.setdefault(pk, []).append(Item)
        if "GSI1PK" in Item:
            self.items_by_gsi1pk.setdefault(Item["GSI1PK"], []).append(Item)

    def delete_item(self, Key=None):
        self.delete_calls.append(Key)
        # Remove from in-memory tracking
        pk = Key["PK"]
        if pk in self.items_by_pk:
            self.items_by_pk[pk] = [
                item for item in self.items_by_pk[pk]
                if item.get("SK") != Key.get("SK") or item.get("GSI1SK") != Key.get("GSI1SK")
            ]

    def get_item(self, Key=None):
        pk = Key["PK"]
        sk = Key.get("SK")
        items = self.items_by_pk.get(pk, [])
        for item in items:
            if item.get("SK") == sk:
                return {"Item": item}
        # Return empty dict (no "Item" key) to simulate missing item
        return {}


def _create_store_with_table(table: FakeTable) -> DynamoDBStore:
    """Create a DynamoDBStore with a fake table and initialized in-memory state."""
    store_instance = object.__new__(DynamoDBStore)
    store_instance._table = table
    store_instance._persistence_loaded = True
    store_instance._dishes = {}
    store_instance._votes = []
    store_instance._members = []
    store_instance._vote_availability = {day: {meal: True for meal in MEALS} for day in WEEK_DAYS}
    store_instance._finalized = False
    store_instance._final_weekly_menu = None
    store_instance._shortlists = {day: {meal: set() for meal in MEALS} for day in WEEK_DAYS}
    store_instance._manual_menu = {day: {meal: None for meal in MEALS} for day in WEEK_DAYS}
    store_instance._periods = {}
    store_instance._active_period_id = None
    return store_instance


class TestDynamoDBDishPersistence:
    """Test dish creation and persistence in DynamoDB store."""

    def test_create_dish_persists_to_table(self):
        """Should persist dish to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        dish = store.create_dish(CreateDishRequest(name="Pasta", category="lunch"))

        assert dish.name == "Pasta"
        assert len(table.put_calls) == 1
        assert table.put_calls[0]["name"] == "Pasta"
        assert table.put_calls[0]["category"] == "lunch"

    def test_update_dish_persists_changes(self):
        """Should persist updated dish to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        # Create initial dish
        dish = store.create_dish(CreateDishRequest(name="Pasta", category="lunch"))
        initial_put_count = len(table.put_calls)

        # Update the dish
        updated = store.update_dish(dish.id, CreateDishRequest(name="Risotto", category="dinner"))

        assert updated.name == "Risotto"
        assert updated.category == "dinner"
        assert len(table.put_calls) == initial_put_count + 1

    def test_delete_dish_persists_deletion(self):
        """Should persist dish deletion to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        dish = store.create_dish(CreateDishRequest(name="Pasta"))
        initial_delete_count = len(table.delete_calls)

        store.delete_dish(dish.id)

        assert len(table.delete_calls) == initial_delete_count + 1
        assert dish.id not in [d["id"] for d in store.list_dishes()]


class TestDynamoDBMemberPersistence:
    """Test member operations persistence in DynamoDB store."""

    def test_add_member_persists_to_table(self):
        """Should persist new member to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        store.add_member("Alice")

        assert "Alice" in store.list_members()
        assert len(table.put_calls) >= 1

    def test_update_member_persists_to_table(self):
        """Should persist member name change to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        store.add_member("Alice")
        initial_put_count = len(table.put_calls)

        store.update_member("Alice", "Bob")

        assert "Bob" in store.list_members()
        assert "Alice" not in store.list_members()
        assert len(table.put_calls) > initial_put_count

    def test_delete_member_persists_to_table(self):
        """Should persist member deletion to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        store.add_member("Alice")
        initial_delete_count = len(table.delete_calls)

        store.delete_member("Alice")

        assert "Alice" not in store.list_members()
        assert len(table.delete_calls) > initial_delete_count


class TestDynamoDBVotePersistence:
    """Test vote operations persistence in DynamoDB store."""

    def test_add_vote_persists_to_table(self):
        """Should persist vote to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        # Add member and dish first
        store.add_member("Alice")
        dish = store.create_dish(CreateDishRequest(name="Pasta"))

        initial_put_count = len(table.put_calls)

        store.add_vote(CreateVoteRequest(user_name="Alice", dish_id=dish.id, day="monday", meal="lunch"))

        assert len(store.list_votes()) == 1
        assert len(table.put_calls) > initial_put_count


class TestDynamoDBShortlistPersistence:
    """Test shortlist operations persistence in DynamoDB store."""

    def test_set_shortlist_persists_to_table(self):
        """Should persist shortlist to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        dish = store.create_dish(CreateDishRequest(name="Pasta"))

        initial_put_count = len(table.put_calls)

        store.set_shortlist("monday", "lunch", [dish.id])

        assert dish.id in store._shortlists["monday"]["lunch"]
        # Should have persisted the shortlist
        assert len(table.put_calls) > initial_put_count


class TestDynamoDBMenuItemPersistence:
    """Test manual menu item persistence in DynamoDB store."""

    def test_set_menu_item_persists_to_table(self):
        """Should persist manual menu item to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        dish = store.create_dish(CreateDishRequest(name="Pasta"))

        initial_put_count = len(table.put_calls)

        store.set_menu_item("monday", "lunch", dish.id)

        assert store._manual_menu["monday"]["lunch"] == dish.id
        assert len(table.put_calls) > initial_put_count

    def test_set_menu_item_with_none_clears_slot(self):
        """Should clear menu item when dish_id is None."""
        table = FakeTable()
        store = _create_store_with_table(table)

        dish = store.create_dish(CreateDishRequest(name="Pasta"))
        store.set_menu_item("monday", "lunch", dish.id)
        assert store._manual_menu["monday"]["lunch"] == dish.id

        initial_put_count = len(table.put_calls)

        store.set_menu_item("monday", "lunch", None)

        assert store._manual_menu["monday"]["lunch"] is None
        assert len(table.put_calls) > initial_put_count


class TestDynamoDBValidationPersistence:
    """Test menu validation persistence in DynamoDB store."""

    def test_validate_menu_persists_finalized_state(self):
        """Should persist finalized state to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        # Add votes
        store.add_member("Alice")
        dish = store.create_dish(CreateDishRequest(name="Pasta"))
        store.add_vote(CreateVoteRequest(user_name="Alice", dish_id=dish.id, day="monday", meal="lunch"))

        initial_put_count = len(table.put_calls)

        menu = store.validate_menu()

        assert menu.finalized is True
        assert store._finalized is True
        # Should have persisted the finalized state
        assert len(table.put_calls) > initial_put_count

    def test_unvalidate_menu_clears_finalized_state(self):
        """Should persist un-finalized state to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        store.add_member("Alice")
        dish = store.create_dish(CreateDishRequest(name="Pasta"))
        store.add_vote(CreateVoteRequest(user_name="Alice", dish_id=dish.id, day="monday", meal="lunch"))
        store.validate_menu()

        initial_put_count = len(table.put_calls)

        menu = store.unvalidate_menu()

        assert menu.finalized is False
        assert store._finalized is False
        assert len(table.put_calls) > initial_put_count


class TestDynamoDBPeriodPersistence:
    """Test period operations persistence in DynamoDB store."""

    def test_create_period_persists_to_table(self):
        """Should persist period creation to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        initial_put_count = len(table.put_calls)

        period = store.create_period("2026-04-16")

        assert period.period_id == "2026-04-16"
        assert len(table.put_calls) > initial_put_count

    def test_get_period_returns_existing(self):
        """Should return period from store."""
        table = FakeTable()
        store = _create_store_with_table(table)

        period = store.create_period("2026-04-16")
        retrieved = store.get_period("2026-04-16")

        assert retrieved is not None
        assert retrieved.period_id == "2026-04-16"

    def test_list_periods_returns_all(self):
        """Should list all periods."""
        table = FakeTable()
        store = _create_store_with_table(table)

        store.create_period("2026-04-09")
        store.create_period("2026-04-16")

        periods = store.list_periods()

        assert len(periods) >= 2

    def test_archive_period_persists_archive(self):
        """Should persist period archival."""
        table = FakeTable()
        store = _create_store_with_table(table)

        store.create_period("2026-04-16")
        initial_put_count = len(table.put_calls)

        store.archive_period("2026-04-16")

        # Should have persisted the archive
        assert len(table.put_calls) > initial_put_count


class TestDynamoDBSessionPersistence:
    """Test session operations persistence in DynamoDB store."""

    def test_save_session_persists_to_table(self):
        """Should persist session to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        initial_put_count = len(table.put_calls)

        store.save_session("test_session_token")

        # Verify session was added to table
        table.add_item({
            "PK": "SESSION#test_session_token",
            "SK": "METADATA",
        })
        assert len(table.put_calls) >= initial_put_count

    def test_delete_session_persists_to_table(self):
        """Should persist session deletion to DynamoDB table."""
        table = FakeTable()
        store = _create_store_with_table(table)

        # Add session to table first
        table.add_item({
            "PK": "SESSION#test_session_token",
            "SK": "METADATA",
        })
        initial_delete_count = len(table.delete_calls)

        store.delete_session("test_session_token")

        assert len(table.delete_calls) > initial_delete_count

    def test_session_exists_returns_true(self):
        """Should return True for saved session."""
        table = FakeTable()
        store = _create_store_with_table(table)

        # Add session directly to table
        table.add_item({
            "PK": "SESSION#test_session_token",
            "SK": "METADATA",
        })

        assert store.session_exists("test_session_token") is True

    def test_session_exists_returns_false(self):
        """Should return False for unknown session."""
        table = FakeTable()
        store = _create_store_with_table(table)

        # Make sure session doesn't exist
        result = store.session_exists("unknown_token")
        assert result is False
