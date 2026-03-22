from fastapi.testclient import TestClient


def _first_dish_id(client: TestClient) -> str:
    response = client.get("/dishes")
    assert response.status_code == 200
    dishes = response.json()
    assert dishes
    return dishes[0]["id"]


def test_post_vote_rejects_unknown_dish(client: TestClient) -> None:
    payload = {"user_name": "Alice", "dish_id": "unknown", "day": "monday"}

    response = client.post("/votes", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "Dish not found"


def test_post_vote_and_list_votes(client: TestClient) -> None:
    dish_id = _first_dish_id(client)
    payload = {"user_name": "Alice", "dish_id": dish_id, "day": "tuesday"}

    vote_response = client.post("/votes", json=payload)
    assert vote_response.status_code == 200
    assert vote_response.json() == payload

    list_response = client.get("/votes")
    assert list_response.status_code == 200
    assert list_response.json() == [payload]


def test_generate_weekly_menu_returns_winner_for_voted_day(client: TestClient) -> None:
    dishes_response = client.get("/dishes")
    dishes = dishes_response.json()
    first = dishes[0]["id"]
    second = dishes[1]["id"]

    # Monday winner should be "first" (2 votes vs 1).
    client.post("/votes", json={"user_name": "Alice", "dish_id": first, "day": "monday"})
    client.post("/votes", json={"user_name": "Bob", "dish_id": first, "day": "monday"})
    client.post("/votes", json={"user_name": "Cara", "dish_id": second, "day": "monday"})

    menu_response = client.get("/weekly-menu")
    assert menu_response.status_code == 200
    menu = menu_response.json()["items"]

    monday = next(item for item in menu if item["day"] == "monday")
    tuesday = next(item for item in menu if item["day"] == "tuesday")
    assert monday["dish"]["id"] == first
    assert tuesday["dish"] is None


def test_admin_shortlist_and_validate_menu(client: TestClient) -> None:
    dishes_response = client.get("/dishes")
    dishes = dishes_response.json()
    first = dishes[0]["id"]
    second = dishes[1]["id"]

    # shortlist only first dish for monday
    shortlist_response = client.put("/admin/menu/shortlist/monday", json=[first])
    assert shortlist_response.status_code == 200
    assert shortlist_response.json()["shortlists"]["monday"] == [first]

    # vote for both dishes, shortlist should prefer first even with most votes for second
    client.post("/votes", json={"user_name": "Alice", "dish_id": second, "day": "monday"})
    client.post("/votes", json={"user_name": "Bob", "dish_id": second, "day": "monday"})
    client.post("/votes", json={"user_name": "Cara", "dish_id": first, "day": "monday"})

    menu_response = client.get("/weekly-menu")
    assert menu_response.status_code == 200
    monday = next(item for item in menu_response.json()["items"] if item["day"] == "monday")
    assert monday["dish"]["id"] == first

    validated = client.post("/admin/menu/validate")
    assert validated.status_code == 200
    assert validated.json()["finalized"] is True

    # no more votes allowed after validation
    forbidden = client.post("/votes", json={"user_name": "Dave", "dish_id": first, "day": "tuesday"})
    assert forbidden.status_code == 409


def test_admin_crud_dish(client: TestClient) -> None:
    payload = {"name": "Nouvelle salade", "tags": ["healthy"]}
    create_response = client.post("/admin/dishes", json=payload)
    assert create_response.status_code == 200
    building = create_response.json()

    update_response = client.put(f"/admin/dishes/{building['id']}", json={"name": "Salade super", "tags": ["fresh"]})
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Salade super"

    delete_response = client.delete(f"/admin/dishes/{building['id']}")
    assert delete_response.status_code == 204

    missing = client.get("/dishes").json()
    assert all(d["id"] != building['id'] for d in missing)


def test_admin_manual_menu_item_and_unvalidate(client: TestClient) -> None:
    dishes_response = client.get("/dishes")
    dishes = dishes_response.json()
    first = dishes[0]["id"]
    second = dishes[1]["id"]

    # Add votes for monday so default winner is first
    client.post("/votes", json={"user_name": "Alice", "dish_id": first, "day": "monday"})
    client.post("/votes", json={"user_name": "Bob", "dish_id": first, "day": "monday"})
    client.post("/votes", json={"user_name": "Cara", "dish_id": second, "day": "monday"})

    menu_response = client.get("/weekly-menu")
    monday = next(item for item in menu_response.json()["items"] if item["day"] == "monday")
    assert monday["dish"]["id"] == first

    # Override monday to second explicitly
    override_response = client.put("/admin/menu/item/monday", json={"dish_id": second})
    assert override_response.status_code == 200
    monday_override = next(item for item in override_response.json()["items"] if item["day"] == "monday")
    assert monday_override["dish"]["id"] == second

    # Validate menu then unvalidate
    client.post("/admin/menu/validate")
    assert client.get("/weekly-menu").json()["finalized"] is True

    unvalidate_response = client.delete("/admin/menu/validate")
    assert unvalidate_response.status_code == 200
    assert unvalidate_response.json()["finalized"] is False

    # After unvalidate, can still vote again
    new_vote = client.post("/votes", json={"user_name": "Dave", "dish_id": first, "day": "tuesday"})
    assert new_vote.status_code == 200

