from app.schemas.common import CreateDishRequest, CreateVoteRequest
from app.services import store
import pytest


def test_store_update_member_and_vote_consistency() -> None:
    store.reset_store()
    store.seed_data()

    store.add_member("Daniel")
    dish = store.list_dishes()[0]
    store.add_vote(CreateVoteRequest(user_name="Daniel", dish_id=dish.id, day="monday", meal="lunch"))

    store.update_member("Daniel", "Dan")

    assert "Dan" in store.list_members()
    assert "Daniel" not in store.list_members()
    assert store.list_votes()[0].user_name == "Dan"


def test_delete_member_removes_votes() -> None:
    store.reset_store()
    store.seed_data()

    store.add_member("Daniel")
    dish = store.list_dishes()[0]
    store.add_vote(CreateVoteRequest(user_name="Daniel", dish_id=dish.id, day="monday", meal="lunch"))
    store.delete_member("Daniel")

    assert "Daniel" not in store.list_members()
    assert all(vote.user_name != "Daniel" for vote in store.list_votes())


def test_store_shortlist_and_validate_menu_flow() -> None:
    store.reset_store()
    store.seed_data()

    dishes = store.list_dishes()
    first = dishes[0]
    store.set_shortlist("monday", "lunch", [first.id])

    menu = store.generate_weekly_menu()
    assert first.id in menu.shortlists["monday"]["lunch"]

    store.add_vote(CreateVoteRequest(user_name="Alice", dish_id=first.id, day="monday", meal="lunch"))
    validated = store.validate_menu()
    assert validated.finalized is True
    assert store.unvalidate_menu().finalized is False


def test_lambda_handler_importable() -> None:
    import app.lambda_handler as lambda_handler_module

    assert lambda_handler_module.handler is not None


def test_factory_requires_table_name_for_dynamodb_mode(monkeypatch) -> None:
    """Test that factory raises RuntimeError when TABLE_NAME is missing in dynamodb mode."""
    import os
    from app.services.store import get_store, reset_store
    
    # Clear any existing store
    reset_store()
    
    # Set mode to dynamodb but don't set TABLE_NAME
    monkeypatch.setenv("BACKEND_PERSISTENCE_MODE", "dynamodb")
    monkeypatch.delenv("TABLE_NAME", raising=False)
    
    with pytest.raises(RuntimeError) as exc_info:
        get_store()
    
    assert "TABLE_NAME environment variable is required" in str(exc_info.value)
    
    # Clean up
    reset_store()


def test_factory_creates_inmemory_by_default(monkeypatch) -> None:
    """Test that factory creates InMemoryStore when no env vars are set."""
    from app.services.store import get_store, reset_store
    from app.services.store_inmemory import InMemoryStore
    
    # Clear any existing store and env vars
    reset_store()
    monkeypatch.delenv("BACKEND_PERSISTENCE_MODE", raising=False)
    monkeypatch.delenv("TABLE_NAME", raising=False)
    
    store_instance = get_store()
    
    assert isinstance(store_instance, InMemoryStore)
    
    # Clean up
    reset_store()


def test_dynamodb_store_loading_and_query(monkeypatch) -> None:
    from app.schemas.common import Dish, Vote
    from app.services.store_dynamodb import DynamoDBStore

    class FakeTable:
        def __init__(self):
            self.items_by_pk: dict[str, list[dict]] = {}
            self.items_by_gsi1pk: dict[str, list[dict]] = {}
            self.put_calls: list[dict] = []
            self.delete_calls: list[dict] = []

        def add_item(self, item: dict) -> None:
            pk = item["PK"]
            self.items_by_pk.setdefault(pk, []).append(item)
            if "GSI1PK" in item:
                self.items_by_gsi1pk.setdefault(item["GSI1PK"], []).append(item)

        def query(self, KeyConditionExpression=None, ExpressionAttributeValues=None,
                  ExclusiveStartKey=None, IndexName=None):
            if IndexName == "GSI1":
                pk = ExpressionAttributeValues[":pk"]
                return {"Items": self.items_by_gsi1pk.get(pk, [])}
            pk = ExpressionAttributeValues[":pk"]
            return {"Items": self.items_by_pk.get(pk, [])}

        def put_item(self, Item=None):
            self.put_calls.append(Item)

        def delete_item(self, Key=None):
            self.delete_calls.append(Key)

    table = FakeTable()
    table.add_item({
        "PK": "DISH#d1", "SK": "METADATA",
        "GSI1PK": "DISHES", "GSI1SK": "DISH#d1",
        "name": "Test Dish", "tags": ["tag"], "category": "lunch",
    })
    table.add_item({
        "PK": "MEMBER#Alice", "SK": "METADATA",
        "GSI1PK": "MEMBERS", "GSI1SK": "MEMBER#Alice",
    })
    table.add_item({
        "PK": "SLOT#monday#lunch", "SK": "USER#Alice",
        "GSI1PK": "USER#Alice", "GSI1SK": "SLOT#monday#lunch",
        "dish_id": "d1",
    })

    # Create DynamoDBStore without connecting to real DynamoDB
    store_instance = object.__new__(DynamoDBStore)
    store_instance._table = table
    store_instance._persistence_loaded = False
    # Initialize in-memory state
    from app.services.store_inmemory import MEALS, WEEK_DAYS
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
    
    store_instance._ensure_store_loaded()

    assert store_instance.list_dishes()[0].name == "Test Dish"
    assert store_instance.list_members() == ["Alice"]
    assert store_instance.list_votes()[0].user_name == "Alice"


def test_dynamodb_store_persist_and_delete_helpers(monkeypatch) -> None:
    from app.schemas.common import Dish, Vote
    from app.services.store_dynamodb import DynamoDBStore
    from app.services.store_inmemory import MEALS, WEEK_DAYS

    class FakeTable:
        def __init__(self):
            self.put_calls: list[dict] = []
            self.delete_calls: list[dict] = []

        def query(self, KeyConditionExpression=None, ExpressionAttributeValues=None,
                  ExclusiveStartKey=None, IndexName=None):
            return {"Items": []}

        def put_item(self, Item=None):
            self.put_calls.append(Item)

        def delete_item(self, Key=None):
            self.delete_calls.append(Key)

    table = FakeTable()

    store_instance = object.__new__(DynamoDBStore)
    store_instance._table = table
    # Initialize in-memory state
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
    store_instance._persistence_loaded = True

    dish = Dish(id="d1", name="Test Dish", tags=["tag"], category="lunch")
    store_instance._persist_dish(dish)
    assert table.put_calls[0]["PK"] == "DISH#d1"
    assert table.put_calls[0]["SK"] == "METADATA"
    assert table.put_calls[0]["name"] == "Test Dish"

    store_instance._persist_member("Bob")
    assert table.put_calls[1]["PK"] == "MEMBER#Bob"
    assert table.put_calls[1]["SK"] == "METADATA"

    vote = Vote(user_name="Bob", dish_id="d1", day="tuesday", meal="dinner")
    store_instance._persist_vote(vote)
    assert table.put_calls[2]["PK"] == "SLOT#tuesday#dinner"
    assert table.put_calls[2]["SK"] == "USER#Bob"
    assert table.put_calls[2]["dish_id"] == "d1"

    store_instance._delete_dish_from_db("d1")
    assert table.delete_calls[0] == {"PK": "DISH#d1", "SK": "METADATA"}

    store_instance._delete_member_from_db("Bob")
    assert table.delete_calls[1] == {"PK": "MEMBER#Bob", "SK": "METADATA"}

    store_instance._delete_vote_from_db("Bob", "tuesday", "dinner")
    assert table.delete_calls[2] == {"PK": "SLOT#tuesday#dinner", "SK": "USER#Bob"}


def test_dynamodb_config_persistence(monkeypatch) -> None:
    from app.services.store_dynamodb import DynamoDBStore
    from app.services.store_inmemory import MEALS, WEEK_DAYS

    class FakeTable:
        def __init__(self):
            self.put_calls: list[dict] = []
            self.items_by_pk: dict[str, list[dict]] = {}

        def query(self, KeyConditionExpression=None, ExpressionAttributeValues=None,
                  ExclusiveStartKey=None, IndexName=None):
            if IndexName == "GSI1":
                return {"Items": []}
            pk = ExpressionAttributeValues[":pk"]
            return {"Items": self.items_by_pk.get(pk, [])}

        def put_item(self, Item=None):
            self.put_calls.append(Item)
            pk = Item["PK"]
            self.items_by_pk.setdefault(pk, []).append(Item)

        def delete_item(self, Key=None):
            pass

    table = FakeTable()

    store_instance = object.__new__(DynamoDBStore)
    store_instance._table = table
    # Initialize in-memory state
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
    store_instance._persistence_loaded = False

    store_instance._persist_config_availability("monday", "lunch", False)
    assert table.put_calls[-1]["PK"] == "CONFIG"
    assert table.put_calls[-1]["SK"] == "AVAIL#monday#lunch"
    assert table.put_calls[-1]["available"] is False

    store_instance._persist_config_shortlist("monday", "lunch", ["d1", "d2"])
    assert table.put_calls[-1]["SK"] == "SHORTLIST#monday#lunch"
    assert table.put_calls[-1]["dish_ids"] == ["d1", "d2"]

    store_instance._persist_config_menu("monday", "lunch", "d1")
    assert table.put_calls[-1]["SK"] == "MENU#monday#lunch"
    assert table.put_calls[-1]["dish_id"] == "d1"

    store_instance._persist_config_finalized(True)
    assert table.put_calls[-1]["SK"] == "FINALIZED"
    assert table.put_calls[-1]["finalized"] is True

    # Test loading config back
    store_instance.reset_store()
    store_instance._load_config_from_db()
    assert store_instance._vote_availability["monday"]["lunch"] is False
    assert "d1" in store_instance._shortlists["monday"]["lunch"]
    assert store_instance._manual_menu["monday"]["lunch"] == "d1"
    assert store_instance._finalized is True
