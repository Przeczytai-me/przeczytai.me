import pytest
from fastapi.testclient import TestClient

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.main import app
from app.routes.readings import get_file_storage, get_reading_repository
from test_api import FakeRepo, FakeStorage


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
