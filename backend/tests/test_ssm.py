import pytest

import app.core.ssm as ssm_module


class DummySSMClient:
    def get_parameter(self, Name: str, WithDecryption: bool = False):
        assert Name == "/family-meal-planner/dev/admin-password"
        assert WithDecryption is True
        return {"Parameter": {"Value": "secret"}}


def test_get_admin_password_from_ssm(monkeypatch):
    monkeypatch.setattr(ssm_module.boto3, "client", lambda service_name: DummySSMClient())

    value = ssm_module.get_admin_password("/family-meal-planner/dev/admin-password")

    assert value == "secret"


def test_get_admin_password_requires_parameter() -> None:
    with pytest.raises(ValueError):
        ssm_module.get_admin_password("")
