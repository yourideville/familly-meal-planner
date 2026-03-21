from fastapi.testclient import TestClient


def test_{endpoint_name}_success(client: TestClient) -> None:
    # Arrange
    # payload = {{...}}

    # Act
    response = client.{method}("/{endpoint}")

    # Assert
    assert response.status_code == 200
    # assert response.json() == expected


def test_{endpoint_name}_validation_error(client: TestClient) -> None:
    # Arrange
    # invalid_payload = {{...}}

    # Act
    response = client.{method}("/{endpoint}", json=invalid_payload)

    # Assert
    assert response.status_code == 422  # or appropriate error code
    # assert "error" in response.json()


def test_{endpoint_name}_not_found(client: TestClient) -> None:
    # Arrange
    # invalid_id = "nonexistent"

    # Act
    response = client.{method}("/{endpoint}/{{invalid_id}}")

    # Assert
    assert response.status_code == 404
    # assert response.json()["detail"] == "Not found"