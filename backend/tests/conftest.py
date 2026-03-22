from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.services import store


@pytest.fixture(autouse=True)
def reset_store() -> None:
    store.reset_store()
    store.seed_data()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
