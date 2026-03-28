from fastapi.testclient import TestClient


def login_admin(client: TestClient) -> None:
    response = client.post("/admin/login", json={"username": "admin", "password": "password"})
    assert response.status_code == 200
    assert response.json() == {"authenticated": True}


def _first_dish_id(client: TestClient) -> str:
    response = client.get("/dishes")
    assert response.status_code == 200
    dishes = response.json()
    assert dishes
    return dishes[0]["id"]


def _set_slot_availability(client: TestClient, day: str, meal: str, available: bool) -> list[dict[str, object]]:
    login_admin(client)
    response = client.get("/admin/vote-availability")
    assert response.status_code == 200
    slots = response.json()
    for slot in slots:
        if slot["day"] == day and slot["meal"] == meal:
            slot["available"] = available
    update = client.put("/admin/vote-availability", json=slots)
    assert update.status_code == 200
    return update.json()


def test_post_vote_rejects_unknown_dish(client: TestClient) -> None:
    payload = {"user_name": "Alice", "dish_id": "unknown", "day": "monday", "meal": "lunch"}

    response = client.post("/votes", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Dish not found"


def test_post_vote_rejects_unknown_member(client: TestClient) -> None:
    dish_id = _first_dish_id(client)
    payload = {"user_name": "Unknown", "dish_id": dish_id, "day": "monday", "meal": "lunch"}

    response = client.post("/votes", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"


def test_post_vote_rejects_unavailable_slot(client: TestClient) -> None:
    dish_id = _first_dish_id(client)
    _set_slot_availability(client, "monday", "lunch", False)

    payload = {"user_name": "Alice", "dish_id": dish_id, "day": "monday", "meal": "lunch"}
    response = client.post("/votes", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Slot not available"


def test_post_vote_and_list_votes(client: TestClient) -> None:
    dish_id = _first_dish_id(client)
    payload = {"user_name": "Alice", "dish_id": dish_id, "day": "tuesday", "meal": "dinner"}

    vote_response = client.post("/votes", json=payload)
    assert vote_response.status_code == 200
    assert vote_response.json() == payload

    list_response = client.get("/votes")
    assert list_response.status_code == 200
    assert list_response.json() == [payload]


def test_post_vote_updates_existing_vote_for_same_slot(client: TestClient) -> None:
    dishes = client.get("/dishes").json()
    first = dishes[0]["id"]
    second = dishes[1]["id"]

    client.post("/votes", json={"user_name": "Alice", "dish_id": first, "day": "wednesday", "meal": "lunch"})
    updated = client.post("/votes", json={"user_name": "Alice", "dish_id": second, "day": "wednesday", "meal": "lunch"})

    assert updated.status_code == 200
    assert updated.json()["dish_id"] == second

    votes = client.get("/votes").json()
    assert len(votes) == 1
    assert votes[0]["dish_id"] == second


def test_generate_weekly_menu_returns_winner_for_each_slot(client: TestClient) -> None:
    dishes = client.get("/dishes").json()
    first = dishes[0]["id"]
    second = dishes[1]["id"]

    client.post("/votes", json={"user_name": "Alice", "dish_id": first, "day": "monday", "meal": "lunch"})
    client.post("/votes", json={"user_name": "Bob", "dish_id": first, "day": "monday", "meal": "lunch"})
    client.post("/votes", json={"user_name": "Cara", "dish_id": second, "day": "monday", "meal": "lunch"})
    client.post("/votes", json={"user_name": "Alice", "dish_id": second, "day": "monday", "meal": "dinner"})
    client.post("/votes", json={"user_name": "Bob", "dish_id": second, "day": "monday", "meal": "dinner"})

    menu_response = client.get("/weekly-menu")
    assert menu_response.status_code == 200
    menu = menu_response.json()["items"]

    monday_lunch = next(item for item in menu if item["day"] == "monday" and item["meal"] == "lunch")
    monday_dinner = next(item for item in menu if item["day"] == "monday" and item["meal"] == "dinner")
    tuesday_lunch = next(item for item in menu if item["day"] == "tuesday" and item["meal"] == "lunch")

    assert monday_lunch["dish"]["id"] == first
    assert monday_dinner["dish"]["id"] == second
    assert tuesday_lunch["dish"] is None


def test_admin_shortlist_and_validate_menu(client: TestClient) -> None:
    login_admin(client)
    dishes = client.get("/dishes").json()
    first = dishes[0]["id"]
    second = dishes[1]["id"]

    shortlist_response = client.put(
        "/admin/menu/shortlist",
        json=[{"day": "monday", "meal": "lunch", "dish_ids": [first]}],
    )
    assert shortlist_response.status_code == 200
    assert shortlist_response.json()["shortlists"]["monday"]["lunch"] == [first]

    client.post("/votes", json={"user_name": "Alice", "dish_id": second, "day": "monday", "meal": "lunch"})
    client.post("/votes", json={"user_name": "Bob", "dish_id": second, "day": "monday", "meal": "lunch"})
    client.post("/votes", json={"user_name": "Cara", "dish_id": first, "day": "monday", "meal": "lunch"})

    menu_response = client.get("/weekly-menu")
    monday_lunch = next(item for item in menu_response.json()["items"] if item["day"] == "monday" and item["meal"] == "lunch")
    assert monday_lunch["dish"]["id"] == first

    validated = client.post("/admin/menu/validate")
    assert validated.status_code == 200
    assert validated.json()["finalized"] is True

    forbidden = client.post("/votes", json={"user_name": "Dave", "dish_id": first, "day": "tuesday", "meal": "lunch"})
    assert forbidden.status_code == 409


def test_admin_crud_dish(client: TestClient) -> None:
    login_admin(client)
    payload = {"name": "Nouvelle salade", "tags": ["healthy"], "category": "lunch"}
    create_response = client.post("/admin/dishes", json=payload)
    assert create_response.status_code == 200
    building = create_response.json()

    update_response = client.put(
        f"/admin/dishes/{building['id']}",
        json={"name": "Salade super", "tags": ["fresh"], "category": "dinner"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Salade super"
    assert update_response.json()["category"] == "dinner"

    delete_response = client.delete(f"/admin/dishes/{building['id']}")
    assert delete_response.status_code == 204

    missing = client.get("/dishes").json()
    assert all(d["id"] != building["id"] for d in missing)


def test_admin_manual_menu_item_and_unvalidate(client: TestClient) -> None:
    dishes = client.get("/dishes").json()
    first = dishes[0]["id"]
    second = dishes[1]["id"]

    client.post("/votes", json={"user_name": "Alice", "dish_id": first, "day": "monday", "meal": "lunch"})
    client.post("/votes", json={"user_name": "Bob", "dish_id": first, "day": "monday", "meal": "lunch"})
    client.post("/votes", json={"user_name": "Cara", "dish_id": second, "day": "monday", "meal": "lunch"})

    menu_response = client.get("/weekly-menu")
    login_admin(client)
    monday_lunch = next(item for item in menu_response.json()["items"] if item["day"] == "monday" and item["meal"] == "lunch")
    assert monday_lunch["dish"]["id"] == first

    override_response = client.put(
        "/admin/menu/item",
        json={"day": "monday", "meal": "lunch", "dish_id": second},
    )
    assert override_response.status_code == 200
    monday_override = next(item for item in override_response.json()["items"] if item["day"] == "monday" and item["meal"] == "lunch")
    assert monday_override["dish"]["id"] == second

    client.post("/admin/menu/validate")
    assert client.get("/weekly-menu").json()["finalized"] is True

    unvalidate_response = client.delete("/admin/menu/validate")
    assert unvalidate_response.status_code == 200
    assert unvalidate_response.json()["finalized"] is False

    new_vote = client.post("/votes", json={"user_name": "Alice", "dish_id": first, "day": "tuesday", "meal": "lunch"})
    assert new_vote.status_code == 200

