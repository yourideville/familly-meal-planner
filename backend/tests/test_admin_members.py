from fastapi.testclient import TestClient


def test_admin_member_crud(client: TestClient) -> None:
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
