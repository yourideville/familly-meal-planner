from fastapi.testclient import TestClient

from conftest import login_admin


def _first_dish_id(client: TestClient) -> str:
    response = client.get("/dishes")
    assert response.status_code == 200
    dishes = response.json()
    assert dishes
    return dishes[0]["id"]


def test_admin_update_dish_not_found(client: TestClient) -> None:
    login_admin(client)
    response = client.put(
        "/admin/dishes/nonexistent",
        json={"name": "Updated", "tags": [], "category": "lunch"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Dish not found"


def test_admin_delete_dish_not_found(client: TestClient) -> None:
    login_admin(client)
    response = client.delete("/admin/dishes/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Dish not found"


def test_admin_update_dish_when_menu_finalized(client: TestClient) -> None:
    login_admin(client)
    dish_id = _first_dish_id(client)
    client.post("/admin/menu/validate")
    response = client.put(
        f"/admin/dishes/{dish_id}",
        json={"name": "Updated", "tags": [], "category": "lunch"},
    )
    assert response.status_code == 409


def test_admin_delete_dish_when_menu_finalized(client: TestClient) -> None:
    login_admin(client)
    dish_id = _first_dish_id(client)
    client.post("/admin/menu/validate")
    response = client.delete(f"/admin/dishes/{dish_id}")
    assert response.status_code == 409


def test_admin_create_dish_when_menu_finalized(client: TestClient) -> None:
    login_admin(client)
    client.post("/admin/menu/validate")
    response = client.post(
        "/admin/dishes",
        json={"name": "New Dish", "tags": [], "category": "lunch"},
    )
    assert response.status_code == 409


def test_admin_get_dish_categories(client: TestClient) -> None:
    login_admin(client)
    response = client.get("/admin/dishes/categories")
    assert response.status_code == 200
    categories = response.json()
    assert "lunch" in categories
    assert "dinner" in categories
    assert "weekends_lunch" in categories
    assert "saturday_dinner" in categories


def test_admin_get_dishes(client: TestClient) -> None:
    login_admin(client)
    response = client.get("/admin/dishes")
    assert response.status_code == 200
    assert len(response.json()) == 4


def test_admin_shortlist_with_unknown_dish(client: TestClient) -> None:
    login_admin(client)
    response = client.put(
        "/admin/menu/shortlist",
        json=[{"day": "monday", "meal": "lunch", "dish_ids": ["nonexistent"]}],
    )
    assert response.status_code == 404


def test_admin_shortlist_legacy_endpoint(client: TestClient) -> None:
    login_admin(client)
    dish_id = _first_dish_id(client)
    response = client.put(
        "/admin/menu/shortlist/monday",
        json=[dish_id],
    )
    assert response.status_code == 200
    assert dish_id in response.json()["shortlists"]["monday"]["lunch"]


def test_admin_shortlist_legacy_unknown_dish(client: TestClient) -> None:
    login_admin(client)
    response = client.put(
        "/admin/menu/shortlist/monday",
        json=["nonexistent"],
    )
    assert response.status_code == 404


def test_admin_menu_item_unknown_dish(client: TestClient) -> None:
    login_admin(client)
    response = client.put(
        "/admin/menu/item",
        json={"day": "monday", "meal": "lunch", "dish_id": "nonexistent"},
    )
    assert response.status_code == 404


def test_admin_menu_item_legacy_endpoint(client: TestClient) -> None:
    login_admin(client)
    dish_id = _first_dish_id(client)
    response = client.put(
        f"/admin/menu/item/monday",
        json={"dish_id": dish_id},
    )
    assert response.status_code == 200
    monday_lunch = next(
        item for item in response.json()["items"]
        if item["day"] == "monday" and item["meal"] == "lunch"
    )
    assert monday_lunch["dish"]["id"] == dish_id


def test_admin_menu_item_legacy_unknown_dish(client: TestClient) -> None:
    login_admin(client)
    response = client.put(
        "/admin/menu/item/monday",
        json={"dish_id": "nonexistent"},
    )
    assert response.status_code == 404


def test_admin_validate_menu_returns_finalized(client: TestClient) -> None:
    login_admin(client)
    response = client.post("/admin/menu/validate")
    assert response.status_code == 200
    assert response.json()["finalized"] is True


def test_admin_unvalidate_menu(client: TestClient) -> None:
    login_admin(client)
    client.post("/admin/menu/validate")
    response = client.delete("/admin/menu/validate")
    assert response.status_code == 200
    assert response.json()["finalized"] is False


def test_admin_validate_already_finalized_returns_menu(client: TestClient) -> None:
    login_admin(client)
    client.post("/admin/menu/validate")
    response = client.post("/admin/menu/validate")
    assert response.status_code == 200
    assert response.json()["finalized"] is True


def test_admin_member_error_paths(client: TestClient) -> None:
    login_admin(client)

    response = client.post("/admin/members", json={"name": ""})
    assert response.status_code == 400

    response = client.post("/admin/members", json={"name": "Alice"})
    assert response.status_code == 400

    response = client.put("/admin/members/Nonexistent", json={"name": "NewName"})
    assert response.status_code == 404

    response = client.delete("/admin/members/Nonexistent")
    assert response.status_code == 404


def test_admin_invalid_login(client: TestClient) -> None:
    response = client.post("/admin/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
