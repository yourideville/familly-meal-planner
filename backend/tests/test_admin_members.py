from fastapi.testclient import TestClient


def login_admin(client: TestClient) -> None:
    response = client.post("/admin/login", json={"username": "admin", "password": "password"})
    assert response.status_code == 200
    assert response.json() == {"authenticated": True}


def test_admin_routes_require_authentication(client: TestClient) -> None:
    response = client.get("/admin/members")
    assert response.status_code == 401
    assert response.json()["detail"] == "Accès administrateur requis"


def test_public_member_list_is_available_without_authentication(client: TestClient) -> None:
    response = client.get("/members")
    assert response.status_code == 200
    assert "Alice" in response.json()


def test_admin_login_session_and_logout(client: TestClient) -> None:
    session_response = client.get("/admin/session")
    assert session_response.status_code == 200
    assert session_response.json() == {"authenticated": False}

    login_admin(client)

    session_response = client.get("/admin/session")
    assert session_response.status_code == 200
    assert session_response.json() == {"authenticated": True}

    logout_response = client.post("/admin/logout")
    assert logout_response.status_code == 200
    assert logout_response.json() == {"authenticated": False}

    members_response = client.get("/admin/members")
    assert members_response.status_code == 401


def test_admin_member_crud(client: TestClient) -> None:
    login_admin(client)

    members_response = client.get("/admin/members")
    assert members_response.status_code == 200
    assert "Alice" in members_response.json()

    create_response = client.post("/admin/members", json={"name": "Daniel"})
    assert create_response.status_code == 200
    assert create_response.json() == "Daniel"

    rename_response = client.put("/admin/members/Daniel", json={"name": "Daniela"})
    assert rename_response.status_code == 200
    assert rename_response.json() == "Daniela"

    delete_response = client.delete("/admin/members/Daniela")
    assert delete_response.status_code == 204

    members_after = client.get("/admin/members").json()
    assert "Daniela" not in members_after


def test_admin_vote_availability(client: TestClient) -> None:
    login_admin(client)

    response = client.get("/admin/vote-availability")
    assert response.status_code == 200
    slots = response.json()

    assert any(slot["day"] == "monday" and slot["meal"] == "lunch" and slot["available"] is True for slot in slots)

    updated_slots = [
        {**slot, "available": False} if slot["day"] == "monday" and slot["meal"] == "lunch" else slot
        for slot in slots
    ]
    set_response = client.put("/admin/vote-availability", json=updated_slots)
    assert set_response.status_code == 200
    assert any(slot["day"] == "monday" and slot["meal"] == "lunch" and slot["available"] is False for slot in set_response.json())
