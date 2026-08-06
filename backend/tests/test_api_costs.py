from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.main import app
from app.routes.readings import get_file_storage, get_reading_repository
from app.tts import OPENAI_TTS_INPUT_MAX_CHARS, TTS_PROVIDERS
from test_api import FakeRepo, FakeStorage, add_reading

TOP_LEVEL_KEYS = {
    "currency",
    "price_book_version",
    "budget",
    "totals",
    "months",
    "days",
    "components",
    "vendors",
    "users",
    "runs",
    "limits",
}
TOTAL_KEYS = {
    "all_time_usd",
    "month_usd",
    "previous_month_usd",
    "runs_all_time",
    "runs_month",
    "chars_month",
    "audio_ms_month",
    "avg_run_usd",
    "usd_per_1k_chars",
    "usd_per_audio_minute",
    "retained_storage_usd_per_month",
    "active_users_month",
}
COMPONENT_KEYS = {"tts", "llm", "compute", "storage", "platform"}


class FakeCostRepo(FakeRepo):
    def __init__(self) -> None:
        super().__init__()
        self.system_costs: list[dict] = []
        self.user_costs: list[dict] = []
        self.run_costs: list[dict] = []

    def list_run_costs(self, limit: int) -> list[dict]:
        return self.run_costs[:limit]

    def get_system_month_costs(self, months: int) -> list[dict]:
        return self.system_costs[:months]

    def get_user_month_cost(self, owner_user_id: str, month: str) -> dict:
        suffix = f"COSTUSER#{month}#{owner_user_id}"
        return next((item for item in self.user_costs if item["sk"] == suffix), {})

    def list_user_month_costs(self, month: str) -> list[dict]:
        return [item for item in self.user_costs if f"COSTUSER#{month}#" in item["sk"]]


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def settings(admin_user_ids: str) -> Settings:
    return Settings(max_text_chars=100_000, openai_tts_enabled=True).model_copy(
        update={
            "admin_user_ids": admin_user_ids,
            "max_run_cost_usd": 0.25,
            "monthly_budget_usd": None,
        }
    )


def client(
    *,
    user_id: str = "admin-1",
    admin_user_ids: str = "admin-1",
    repo: FakeCostRepo | None = None,
    storage: FakeStorage | None = None,
) -> tuple[TestClient, FakeCostRepo, FakeStorage]:
    repo = repo or FakeCostRepo()
    storage = storage or FakeStorage()
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(user_id)
    app.dependency_overrides[get_settings] = lambda: settings(admin_user_ids)
    app.dependency_overrides[get_reading_repository] = lambda: repo
    app.dependency_overrides[get_file_storage] = lambda: storage
    return TestClient(app), repo, storage


def nested_keys(value: object):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key).casefold()
            yield from nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_keys(child)


def test_get_costs_as_admin_has_the_complete_top_level_shape() -> None:
    test_client, _, _ = client()

    response = test_client.get("/api/v1/costs?months=6")

    assert response.status_code == 200
    body = response.json()
    assert TOP_LEVEL_KEYS <= body.keys()
    assert body["currency"] == "USD"
    assert body["price_book_version"] == "2026-08-05"


def test_get_costs_with_no_data_is_fully_zeroed() -> None:
    test_client, _, _ = client()

    response = test_client.get("/api/v1/costs")

    assert response.status_code == 200
    body = response.json()
    assert all(body["totals"][key] == 0 for key in TOTAL_KEYS)
    assert body["budget"]["month_spent_usd"] == 0
    assert body["budget"]["projected_month_usd"] == 0
    assert body["budget"]["monthly_limit_usd"] is None
    assert body["budget"]["utilization"] is None
    assert body["budget"]["thresholds"] == [50, 80, 95]
    assert body["months"] == []
    assert body["days"] == []
    assert body["vendors"] == []
    assert body["users"] == []
    assert body["runs"] == []
    assert all(body["components"][key] == 0 for key in COMPONENT_KEYS)
    assert body["limits"]["max_text_chars"] == 100_000
    assert body["limits"]["max_run_cost_usd"] == 0.25
    assert body["limits"]["monthly_budget_usd"] is None


def test_legacy_readings_without_costs_do_not_break_aggregates() -> None:
    repo = FakeCostRepo()
    add_reading(repo, "admin-1", "legacy")
    costed = add_reading(repo, "admin-1", "costed")
    current_time = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    for item in repo.items.values():
        item["created_at"] = current_time
        item["updated_at"] = current_time
    costed.update(
        {
            "cost_usd_micros": 2500,
            "cost_components": {"tts_usd_micros": 2500},
            "cost_usage": {"audio_ms": 1000},
            "price_book_version": "2026-08-05",
        }
    )
    month = datetime.now(UTC).strftime("%Y-%m")
    repo.system_costs = [
        {
            "pk": "SYSTEM",
            "sk": f"COST#{month}",
            "total_usd_micros": 2500,
            "tts_usd_micros": 2500,
            "llm_usd_micros": 0,
            "compute_usd_micros": 0,
            "storage_usd_micros": 0,
            "platform_usd_micros": 0,
            "runs": 1,
            "chars": costed["char_count"],
            "audio_ms": 1000,
        }
    ]
    test_client, _, _ = client(repo=repo)

    response = test_client.get("/api/v1/costs")

    assert response.status_code == 200
    assert response.json()["totals"]["month_usd"] == 0.0025
    assert response.json()["totals"]["runs_month"] == 1


def test_get_costs_rejects_non_admin() -> None:
    test_client, _, _ = client(user_id="user-1")

    response = test_client.get("/api/v1/costs")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_get_costs_fails_closed_when_admin_list_is_empty() -> None:
    test_client, _, _ = client(admin_user_ids="")

    response = test_client.get("/api/v1/costs")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_estimate_rejects_non_admin() -> None:
    test_client, _, _ = client(user_id="user-1")

    response = test_client.post("/api/v1/costs/estimate", json={"original_text": "hello"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_estimate_reports_each_vendor_limit_without_writing() -> None:
    test_client, repo, storage = client()
    original_text = "x" * (OPENAI_TTS_INPUT_MAX_CHARS + 1)

    response = test_client.post(
        "/api/v1/costs/estimate", json={"original_text": original_text}
    )

    assert response.status_code == 200
    body = response.json()
    assert {"char_count", "chunk_count", "vendors", "limits", "price_book_version"} <= body.keys()
    vendors = {item["vendor"]: item for item in body["vendors"]}
    assert set(vendors) == {str(vendor) for vendor in TTS_PROVIDERS}
    assert vendors["openai"]["allowed"] is False
    assert vendors["openai"]["rejection"]["code"]
    assert vendors["edge-tts"]["allowed"] is True
    assert vendors["edge-tts"]["rejection"] is None
    assert repo.items == {}
    assert repo.jobs == {}
    assert repo.started == []
    assert storage.texts == {}


def test_reading_endpoints_never_leak_cost_fields() -> None:
    repo = FakeCostRepo()
    item = add_reading(repo, "user-1", "private costs")
    item.update(
        {
            "cost_usd_micros": 123,
            "cost_components": {"tts_usd_micros": 100},
            "cost_usage": {"audio_ms": 1000},
            "price_book_version": "2026-08-05",
            # metadata IS returned to users, so a cost key hiding in there is the
            # likeliest way this feature leaks. Seed one and prove it is stripped.
            "metadata": {"voice": "Zofia", "cost_usage": {"audio_ms": 1000}},
        }
    )
    test_client, _, _ = client(user_id="user-1", repo=repo)

    responses = [
        test_client.get(f"/api/v1/readings/{item['reading_id']}"),
        test_client.get("/api/v1/readings"),
    ]

    assert all(response.status_code == 200 for response in responses)
    for response in responses:
        keys = list(nested_keys(response.json()))
        assert all("cost" not in key for key in keys)
        assert all("price_book" not in key for key in keys)


def test_user_references_are_stable_and_pseudonymous() -> None:
    repo = FakeCostRepo()
    month = datetime.now(UTC).strftime("%Y-%m")
    raw_user_id = "user-sensitive-id"
    repo.user_costs = [
        {
            "pk": "SYSTEM",
            "sk": f"COSTUSER#{month}#{raw_user_id}",
            "total_usd_micros": 1200,
            "tts_usd_micros": 1200,
            "llm_usd_micros": 0,
            "compute_usd_micros": 0,
            "storage_usd_micros": 0,
            "platform_usd_micros": 0,
            "runs": 2,
            "chars": 200,
            "audio_ms": 1000,
        }
    ]
    test_client, _, _ = client(repo=repo)

    first = test_client.get("/api/v1/costs").json()["users"]
    second = test_client.get("/api/v1/costs").json()["users"]

    assert first
    assert first[0]["user_ref"] == second[0]["user_ref"]
    assert first[0]["user_ref"] != raw_user_id
    assert raw_user_id not in first[0]["user_ref"]
