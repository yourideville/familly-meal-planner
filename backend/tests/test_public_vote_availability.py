"""Tests for public vote availability route and admin session persistence."""
from fastapi.testclient import TestClient

from conftest import login_admin


# ---------------------------------------------------------------------------
# Public vote availability (no admin session required)
# ---------------------------------------------------------------------------

def test_public_vote_availability_without_auth(client: TestClient) -> None:
    """Family members can read vote availability without admin login."""
    response = client.get("/votes/availability")
    assert response.status_code == 200
    slots = response.json()
    assert len(slots) > 0
    assert all("day" in s and "meal" in s and "available" in s for s in slots)


def test_public_vote_availability_reflects_admin_changes(client: TestClient) -> None:
    """Changes made by admin are visible through the public endpoint."""
    login_admin(client)

    admin_slots = client.get("/admin/vote-availability").json()
    updated = [
        {**s, "available": False} if s["day"] == "monday" and s["meal"] == "lunch" else s
        for s in admin_slots
    ]
    client.put("/admin/vote-availability", json=updated)

    public_response = client.get("/votes/availability")
    assert public_response.status_code == 200
    monday_lunch = next(
        s for s in public_response.json()
        if s["day"] == "monday" and s["meal"] == "lunch"
    )
    assert monday_lunch["available"] is False


def test_admin_vote_availability_still_requires_auth(client: TestClient) -> None:
    """PUT (modify) vote availability still requires admin session."""
    response = client.put("/admin/vote-availability", json=[])
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Admin session persistence across requests
# ---------------------------------------------------------------------------

def test_admin_session_survives_across_requests(client: TestClient) -> None:
    """After login, multiple admin requests succeed without re-login."""
    login_admin(client)

    for _ in range(3):
        response = client.get("/admin/members")
        assert response.status_code == 200


def test_admin_session_invalidated_after_logout(client: TestClient) -> None:
    """After logout, admin routes return 401."""
    login_admin(client)
    assert client.get("/admin/members").status_code == 200

    client.post("/admin/logout")

    assert client.get("/admin/members").status_code == 401


def test_admin_login_with_wrong_password(client: TestClient) -> None:
    """Login with wrong credentials returns 401."""
    response = client.post("/admin/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Nom d'utilisateur ou mot de passe invalide"


def test_admin_login_with_wrong_username(client: TestClient) -> None:
    """Login with wrong username returns 401."""
    response = client.post("/admin/login", json={"username": "hacker", "password": "password"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# All admin protected routes require authentication
# ---------------------------------------------------------------------------

def test_admin_protected_routes_require_auth(client: TestClient) -> None:
    """All admin-protected endpoints return 401 without a session."""
    protected_gets = [
        "/admin/members",
        "/admin/vote-availability",
        "/admin/dishes",
        "/admin/dishes/categories",
    ]
    for route in protected_gets:
        response = client.get(route)
        assert response.status_code == 401, f"GET {route} should require auth"

    protected_writes = [
        ("POST", "/admin/members", {"name": "Hacker"}),
        ("PUT", "/admin/vote-availability", []),
        ("POST", "/admin/dishes", {"name": "Evil", "tags": [], "category": "lunch"}),
        ("POST", "/admin/menu/validate", None),
    ]
    for method, route, body in protected_writes:
        kwargs = {"json": body} if body is not None else {}
        response = client.request(method, route, **kwargs)
        assert response.status_code == 401, f"{method} {route} should require auth"
