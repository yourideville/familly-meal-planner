from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_dishes_returns_seed_data(client: TestClient) -> None:
    response = client.get("/dishes")

    assert response.status_code == 200
    dishes = response.json()
    assert len(dishes) == 4
    assert {dish["name"] for dish in dishes} == {
        "Spaghetti Bolognese",
        "Chicken Curry",
        "Vegetable Stir Fry",
        "Grilled Salmon",
    }


def test_create_dish_persists_and_returns_payload(client: TestClient) -> None:
    payload = {"name": "Fish Tacos", "tags": ["seafood", "quick"]}

    create_response = client.post("/dishes", json=payload)
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["name"] == payload["name"]
    assert created["tags"] == payload["tags"]
    assert created["id"]

    list_response = client.get("/dishes")
    assert list_response.status_code == 200
    names = [dish["name"] for dish in list_response.json()]
    assert "Fish Tacos" in names
