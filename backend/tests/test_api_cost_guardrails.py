import pytest
from fastapi.testclient import TestClient
from test_api import FakeRepo, FakeStorage, add_reading

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.costs import USD_MICROS, estimate_cost, usage_from_text
from app.main import app
from app.normalization import apply_abbreviation_readings, normalize
from app.pricing import get_prices
from app.routes.readings import get_file_storage, get_reading_repository


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def client(
    settings: Settings, repo: FakeRepo | None = None, storage: FakeStorage | None = None
) -> tuple[TestClient, FakeRepo, FakeStorage]:
    repo = repo or FakeRepo()
    storage = storage or FakeStorage()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_reading_repository] = lambda: repo
    app.dependency_overrides[get_file_storage] = lambda: storage
    app.dependency_overrides[get_current_user] = lambda: CurrentUser("user-1")
    return TestClient(app), repo, storage


def test_empty_text_remains_a_validation_error() -> None:
    test_client, _, _ = client(Settings(max_text_chars=10))

    response = test_client.post("/api/v1/readings", json={"original_text": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_text_over_character_limit_remains_payload_too_large() -> None:
    test_client, _, _ = client(Settings(max_text_chars=10))

    response = test_client.post("/api/v1/readings", json={"original_text": "x" * 11})

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_text_at_character_limit_is_accepted() -> None:
    test_client, _, _ = client(Settings(max_text_chars=10))

    response = test_client.post("/api/v1/readings", json={"original_text": "x" * 10})

    assert response.status_code == 202


def test_cost_limit_rejection_happens_before_any_write_or_processing() -> None:
    settings = Settings(max_text_chars=100).model_copy(update={"max_run_cost_usd": 0.000001})
    test_client, repo, storage = client(settings)

    response = test_client.post("/api/v1/readings", json={"original_text": "ordinary text"})

    assert response.status_code == 413
    error = response.json()["error"]
    assert error["code"] == "cost_limit_exceeded"
    assert isinstance(error["message"], str) and error["message"].strip()
    assert storage.texts == {}
    assert repo.items == {}
    assert repo.jobs == {}
    assert repo.started == []


def test_default_cost_limit_accepts_an_ordinary_reading() -> None:
    test_client, _, _ = client(Settings(max_text_chars=100))

    response = test_client.post("/api/v1/readings", json={"original_text": "ordinary text"})

    assert response.status_code == 202


def estimated_cost_micros(text: str, settings: Settings) -> int:
    usage = usage_from_text(
        text,
        "edge-tts",
        max_chunk_chars=settings.max_chunk_chars,
        lambda_memory_mb=settings.lambda_memory_mb,
        lambda_timeout_ms=settings.lambda_timeout_ms,
    )
    return estimate_cost(usage, get_prices(settings.cost_price_overrides)).total_usd_micros


def test_abbreviation_expansion_cannot_bypass_the_cost_limit() -> None:
    original_text = "API " * 100
    abbreviation_readings = [{"abbreviation": "API", "read_as": "x" * 200}]
    expanded_text = normalize(
        apply_abbreviation_readings(original_text.strip(), abbreviation_readings)
    )
    base_settings = Settings(max_text_chars=len(original_text))
    raw_cost = estimated_cost_micros(original_text.strip(), base_settings)
    expanded_cost = estimated_cost_micros(expanded_text, base_settings)
    limit_micros = (raw_cost + expanded_cost) // 2
    guarded_settings = base_settings.model_copy(
        update={"max_run_cost_usd": limit_micros / USD_MICROS}
    )

    assert len(expanded_text) > len(original_text) * 10
    assert raw_cost < limit_micros < expanded_cost

    harmless_client, _, _ = client(guarded_settings)
    harmless = harmless_client.post(
        "/api/v1/readings",
        json={
            "original_text": "API documentation",
            "abbreviation_readings": [
                {"abbreviation": "API", "read_as": "application programming interface"}
            ],
        },
    )
    assert harmless.status_code == 202

    test_client, _, _ = client(guarded_settings)
    response = test_client.post(
        "/api/v1/readings",
        json={
            "original_text": original_text,
            "abbreviation_readings": abbreviation_readings,
        },
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "cost_limit_exceeded"


def test_retry_cost_guardrail_blocks_expensive_runs_without_breaking_normal_retries() -> None:
    ordinary_settings = Settings(max_text_chars=100)
    ordinary_repo = FakeRepo()
    ordinary_storage = FakeStorage()
    ordinary = add_reading(
        ordinary_repo,
        "user-1",
        "ordinary text",
        vendor="edge-tts",
        voice="pl-PL-ZofiaNeural",
    )
    ordinary["status"] = "completed"
    ordinary_storage.texts[ordinary["original_text_key"]] = "ordinary text"
    ordinary_client, _, _ = client(ordinary_settings, ordinary_repo, ordinary_storage)

    ordinary_response = ordinary_client.post(
        f"/api/v1/readings/{ordinary['reading_id']}/retry"
    )

    assert ordinary_response.status_code == 202

    expensive_text = "expensive " * 1_000
    expensive_cost = estimated_cost_micros(expensive_text, ordinary_settings)
    guarded_settings = ordinary_settings.model_copy(
        update={"max_run_cost_usd": (expensive_cost - 1) / USD_MICROS}
    )
    expensive_repo = FakeRepo()
    expensive_storage = FakeStorage()
    expensive = add_reading(
        expensive_repo,
        "user-1",
        expensive_text,
        vendor="edge-tts",
        voice="pl-PL-ZofiaNeural",
    )
    expensive["status"] = "completed"
    expensive_storage.texts[expensive["original_text_key"]] = expensive_text
    test_client, _, _ = client(guarded_settings, expensive_repo, expensive_storage)

    response = test_client.post(f"/api/v1/readings/{expensive['reading_id']}/retry")

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "cost_limit_exceeded"
    assert expensive_repo.started == []
    assert expensive_repo.jobs == {}
