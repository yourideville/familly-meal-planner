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
