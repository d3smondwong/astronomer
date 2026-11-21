"""Bearer-token enforcement on /v1/chart/* (apps/backend/security.py)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.backend import security
from apps.backend.routers import chart

TOKEN = "test-token-123"

BIRTH = {
    "year": 1985, "month": 11, "day": 25, "hour": 17, "minute": 7,
    "gender": 1, "latitude": 1.35, "longitude": 103.8,
    "use_solar_time_correction": True,
}

# Every route the router exposes, with a body that would otherwise be valid enough to
# reach the handler. Auth must reject before any of them run (no calc, no LLM call).
ROUTES = [
    ("/v1/chart/natal", BIRTH),
    ("/v1/chart/cycles", BIRTH),
    ("/v1/chart/insights", {"data": {}, "section": "personality"}),
    ("/v1/chart/insights/stream", {"data": {}, "section": "personality"}),
]


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(chart.router)
    return TestClient(app)


@pytest.fixture
def token_set(monkeypatch):
    monkeypatch.setenv(security.TOKEN_ENV_VAR, TOKEN)
    monkeypatch.delenv(security.CLOUD_RUN_ENV_VAR, raising=False)


@pytest.fixture
def token_unset(monkeypatch):
    monkeypatch.delenv(security.TOKEN_ENV_VAR, raising=False)
    monkeypatch.delenv(security.CLOUD_RUN_ENV_VAR, raising=False)


class TestTokenConfigured:
    @pytest.mark.parametrize("path,body", ROUTES)
    def test_missing_header_is_401(self, client, token_set, path, body):
        res = client.post(path, json=body)
        assert res.status_code == 401
        assert res.headers["www-authenticate"] == "Bearer"

    @pytest.mark.parametrize("path,body", ROUTES)
    def test_wrong_token_is_401(self, client, token_set, path, body):
        res = client.post(path, json=body, headers={"Authorization": "Bearer nope"})
        assert res.status_code == 401

    @pytest.mark.parametrize(
        "header", [TOKEN, f"Basic {TOKEN}", "Bearer", "Bearer ", f"Bearer {TOKEN}x"]
    )
    def test_malformed_or_near_miss_is_401(self, client, token_set, header):
        res = client.post("/v1/chart/natal", json=BIRTH, headers={"Authorization": header})
        assert res.status_code == 401

    def test_auth_runs_before_body_validation(self, client, token_set):
        # An unauthenticated caller learns nothing about the request schema.
        res = client.post("/v1/chart/natal", json={"bogus": True})
        assert res.status_code == 401

    def test_correct_token_reaches_handler(self, client, token_set):
        res = client.post(
            "/v1/chart/natal", json=BIRTH, headers={"Authorization": f"Bearer {TOKEN}"}
        )
        assert res.status_code == 200
        assert res.json()["chart_key"] == "bBdLeEgIM"

    def test_scheme_is_case_insensitive(self, client, token_set):
        res = client.post(
            "/v1/chart/natal", json=BIRTH, headers={"Authorization": f"bearer {TOKEN}"}
        )
        assert res.status_code == 200


class TestTokenUnset:
    @pytest.mark.parametrize("path,body", ROUTES)
    def test_cloud_run_fails_closed(self, client, token_unset, monkeypatch, path, body):
        monkeypatch.setenv(security.CLOUD_RUN_ENV_VAR, "astronomer-api")
        res = client.post(path, json=body)
        assert res.status_code == 503

    def test_local_dev_allows_requests(self, client, token_unset):
        res = client.post("/v1/chart/natal", json=BIRTH)
        assert res.status_code == 200
