"""Tests for periods router.

Covers menu period listing and retrieval endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.services import store


class TestListMenuPeriods:
    """Test GET /weekly-menu/periods endpoint."""

    def test_list_periods_returns_periods(self, client: TestClient):
        """Should return list of periods."""
        # First login as admin
        login_response = client.post("/admin/login", json={
            "username": "admin",
            "password": "password"
        })
        assert login_response.status_code == 200

        # Create some periods
        period1 = store.create_period("2026-04-09")
        period2 = store.create_period("2026-04-16")

        # List periods
        response = client.get("/weekly-menu/periods")
        assert response.status_code == 200
        periods = response.json()
        assert isinstance(periods, list)
        assert len(periods) >= 2

    def test_list_periods_respects_limit(self, client: TestClient):
        """Should respect limit parameter."""
        login_response = client.post("/admin/login", json={
            "username": "admin",
            "password": "password"
        })
        assert login_response.status_code == 200

        # Create multiple periods
        store.create_period("2026-04-02")
        store.create_period("2026-04-09")
        store.create_period("2026-04-16")

        # List with limit
        response = client.get("/weekly-menu/periods?limit=2")
        assert response.status_code == 200
        periods = response.json()
        assert len(periods) <= 2

    def test_list_periods_public_access(self, client: TestClient):
        """Should be accessible without authentication."""
        response = client.get("/weekly-menu/periods")
        assert response.status_code == 200


class TestGetMenuPeriod:
    """Test GET /weekly-menu/periods/{period_id} endpoint."""

    def test_get_existing_period(self, client: TestClient):
        """Should return specific period."""
        login_response = client.post("/admin/login", json={
            "username": "admin",
            "password": "password"
        })
        assert login_response.status_code == 200

        # Create a period
        period = store.create_period("2026-04-16")

        # Get the period
        response = client.get("/weekly-menu/periods/2026-04-16")
        assert response.status_code == 200
        period_data = response.json()
        assert period_data["period_id"] == "2026-04-16"
        assert period_data["start_date"] == "2026-04-16"

    def test_get_nonexistent_period(self, client: TestClient):
        """Should return 404 for nonexistent period."""
        response = client.get("/weekly-menu/periods/2099-01-01")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_period_public_access(self, client: TestClient):
        """Should be accessible without authentication."""
        login_response = client.post("/admin/login", json={
            "username": "admin",
            "password": "password"
        })
        assert login_response.status_code == 200

        store.create_period("2026-04-16")

        response = client.get("/weekly-menu/periods/2026-04-16")
        assert response.status_code == 200


class TestGetCurrentPeriod:
    """Test GET /weekly-menu/current-period endpoint."""

    def test_get_current_period(self, client: TestClient):
        """Should return current active period."""
        login_response = client.post("/admin/login", json={
            "username": "admin",
            "password": "password"
        })
        assert login_response.status_code == 200

        response = client.get("/weekly-menu/current-period")
        assert response.status_code == 200
        period = response.json()
        assert "period_id" in period
        assert "start_date" in period
        assert "end_date" in period

    def test_get_current_period_public_access(self, client: TestClient):
        """Should be accessible without authentication."""
        response = client.get("/weekly-menu/current-period")
        assert response.status_code == 200
        period = response.json()
        assert "period_id" in period

    def test_current_period_has_valid_dates(self, client: TestClient):
        """Should return period with valid date format."""
        response = client.get("/weekly-menu/current-period")
        assert response.status_code == 200
        period = response.json()

        # Check date format (YYYY-MM-DD)
        import re
        date_pattern = r"\d{4}-\d{2}-\d{2}"
        assert re.match(date_pattern, period["start_date"])
        assert re.match(date_pattern, period["end_date"])
