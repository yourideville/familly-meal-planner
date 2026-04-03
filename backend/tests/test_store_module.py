from app.schemas.common import CreateDishRequest, CreateVoteRequest
from app.services import store


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


def test_dynamodb_store_loading_and_scan(monkeypatch) -> None:
    from app.schemas.common import Dish, Vote

    class FakeTable:
        def __init__(self, items=None):
            self.items = items or []
            self.scan_calls = 0
            self.put_calls = []
            self.delete_calls = []

        def scan(self, ExclusiveStartKey=None):
            self.scan_calls += 1
            if self.scan_calls == 1:
                return {"Items": self.items}
            return {"Items": []}

        def put_item(self, Item=None):
            self.put_calls.append(Item)

        def delete_item(self, Key=None):
            self.delete_calls.append(Key)

    dishes_table = FakeTable([{"dish_id": "d1", "name": "Test Dish", "tags": ["tag"], "category": "lunch"}])
    members_table = FakeTable([{"member_id": "Alice"}])
    votes_table = FakeTable([{"vote_id": "v1", "user_name": "Alice", "dish_id": "d1", "day": "monday", "meal": "lunch"}])

    monkeypatch.setattr(store, "_USE_DYNAMODB", True)
    monkeypatch.setattr(store, "_persistence_loaded", False)
    monkeypatch.setattr(store, "_dishes_table", dishes_table)
    monkeypatch.setattr(store, "_members_table", members_table)
    monkeypatch.setattr(store, "_votes_table", votes_table)

    store.reset_store()
    store._ensure_store_loaded()

    assert store.list_dishes()[0].name == "Test Dish"
    assert store.list_members() == ["Alice"]
    assert store.list_votes()[0].user_name == "Alice"


def test_dynamodb_store_persist_and_delete_helpers(monkeypatch) -> None:
    from app.schemas.common import Dish, Vote

    class FakeTable:
        def __init__(self):
            self.put_calls = []
            self.delete_calls = []

        def put_item(self, Item=None):
            self.put_calls.append(Item)

        def delete_item(self, Key=None):
            self.delete_calls.append(Key)

        def scan(self, ExclusiveStartKey=None):
            return {"Items": []}

    dishes_table = FakeTable()
    members_table = FakeTable()
    votes_table = FakeTable()

    monkeypatch.setattr(store, "_USE_DYNAMODB", True)
    monkeypatch.setattr(store, "_dishes_table", dishes_table)
    monkeypatch.setattr(store, "_members_table", members_table)
    monkeypatch.setattr(store, "_votes_table", votes_table)
    monkeypatch.setattr(store, "_persistence_loaded", False)

    dish = Dish(id="d1", name="Test Dish", tags=["tag"], category="lunch")
    store._persist_dish(dish)
    assert dishes_table.put_calls[0]["dish_id"] == "d1"

    store._persist_member("Bob")
    assert members_table.put_calls[0]["member_id"] == "Bob"

    vote = Vote(user_name="Bob", dish_id="d1", day="tuesday", meal="dinner")
    store._persist_vote(vote, "v2")
    assert votes_table.put_calls[0]["vote_id"] == "v2"
    assert vote.user_name == "Bob"
    assert store._vote_ids[("Bob", "tuesday", "dinner")] == "v2"

    store._delete_dish_from_db("d1")
    assert dishes_table.delete_calls[0]["dish_id"] == "d1"

    store._delete_member_from_db("Bob")
    assert members_table.delete_calls[0]["member_id"] == "Bob"

    store._delete_vote_from_db("v2")
    assert votes_table.delete_calls[0]["vote_id"] == "v2"
