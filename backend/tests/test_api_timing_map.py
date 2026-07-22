import json

import pytest
from fastapi.testclient import TestClient

from app.auth import CurrentUser, get_current_user
from app.main import app
from app.routes.readings import get_file_storage, get_reading_repository
from app.storage import StorageError

NOW = "2026-07-22T12:00:00Z"


class TimingRepo:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict[str, object]] = {}

    def get(self, owner_user_id: str, reading_id: str) -> dict[str, object] | None:
        return self.items.get((owner_user_id, reading_id))


class TimingStorage:
    def __init__(self) -> None:
        self.texts: dict[str, str] = {}
        self.get_calls: list[str] = []
        self.fail_load = False

    def get_text(self, key: str) -> str:
        self.get_calls.append(key)
        if self.fail_load:
            raise StorageError("S3 unavailable")
        return self.texts[key]


def add_reading(
    repo: TimingRepo,
    owner_user_id: str,
    *,
    reading_id: str = "reading-1",
    status: str = "completed",
    timing_map_key: str | None = None,
) -> dict[str, object]:
    item: dict[str, object] = {
        "reading_id": reading_id,
        "owner_user_id": owner_user_id,
        "original_text_key": f"users/{owner_user_id}/readings/{reading_id}/original.txt",
        "status": status,
        "char_count": 10,
        "created_at": NOW,
        "updated_at": NOW,
    }
    if timing_map_key is not None:
        item["timing_map_key"] = timing_map_key
    repo.items[(owner_user_id, reading_id)] = item
    return item


def timing_client(
    repo: TimingRepo | None = None,
    storage: TimingStorage | None = None,
    *,
    auth: bool = True,
) -> tuple[TestClient, TimingRepo, TimingStorage]:
    app.dependency_overrides.clear()
    repo = repo or TimingRepo()
    storage = storage or TimingStorage()
    app.dependency_overrides[get_reading_repository] = lambda: repo
    app.dependency_overrides[get_file_storage] = lambda: storage
    if auth:
        app.dependency_overrides[get_current_user] = lambda: CurrentUser("user-1")
    return TestClient(app), repo, storage


@pytest.mark.parametrize(
    "reading_status",
    ["uploaded", "normalizing", "generating_audio", "merging_audio"],
)
def test_timing_map_is_not_ready_for_active_reading(reading_status: str) -> None:
    """Return the pinned conflict while timing generation is still active."""
    test_client, repo, _ = timing_client()
    add_reading(repo, "user-1", status=reading_status)

    response = test_client.get("/api/v1/readings/reading-1/timing-map")

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "timing_map_not_ready",
            "message": "Timing map is not ready",
        }
    }


@pytest.mark.parametrize("reading_status", ["failed", "failed_to_start"])
def test_timing_map_is_unavailable_for_failed_reading(reading_status: str) -> None:
    """Return unavailable for a terminal failed reading without a timing key."""
    test_client, repo, _ = timing_client()
    add_reading(repo, "user-1", status=reading_status)

    response = test_client.get("/api/v1/readings/reading-1/timing-map")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "timing_map_unavailable",
            "message": "Timing map is not available",
        }
    }


def test_timing_map_is_unavailable_for_legacy_completed_reading() -> None:
    """Return unavailable for completed legacy data that has no timing key."""
    test_client, repo, _ = timing_client()
    add_reading(repo, "user-1", status="completed")

    response = test_client.get("/api/v1/readings/reading-1/timing-map")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "timing_map_unavailable",
            "message": "Timing map is not available",
        }
    }


def test_timing_map_returns_persisted_segments_with_exact_public_shape() -> None:
    """Load persisted timing JSON and return only the public timing-map fields."""
    test_client, repo, storage = timing_client()
    key = "users/user-1/readings/reading-1/timing-job-2.json"
    add_reading(repo, "user-1", timing_map_key=key)
    timing = {
        "version": 1,
        "duration_ms": 3750,
        "segments": [
            {
                "id": "segment-1",
                "text": "Ala ma kota.",
                "paragraph_index": 0,
                "start_ms": 0,
                "end_ms": 1250,
            },
            {
                "id": "segment-2",
                "text": "Ola ma psa.",
                "paragraph_index": 1,
                "start_ms": 1250,
                "end_ms": 3750,
            },
        ],
    }
    storage.texts[key] = json.dumps(timing)

    response = test_client.get("/api/v1/readings/reading-1/timing-map")

    assert response.status_code == 200
    assert response.json() == {
        "reading_id": "reading-1",
        "duration_ms": 3750,
        "segments": timing["segments"],
    }
    assert storage.get_calls == [key]


def test_timing_map_returns_not_found_for_missing_reading() -> None:
    """Return the pinned not-found error when the reading does not exist."""
    test_client, _, _ = timing_client()

    response = test_client.get("/api/v1/readings/missing/timing-map")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Reading not found"}
    }


def test_timing_map_hides_a_foreign_reading() -> None:
    """Return not found when the timing map belongs to another user."""
    test_client, repo, _ = timing_client()
    add_reading(repo, "user-2", timing_map_key="users/user-2/timing.json")

    response = test_client.get("/api/v1/readings/reading-1/timing-map")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Reading not found"}
    }


def test_timing_map_requires_authentication() -> None:
    """Reject timing-map requests without API Gateway JWT claims."""
    test_client, _, _ = timing_client(auth=False)

    response = test_client.get("/api/v1/readings/reading-1/timing-map")

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Missing API Gateway JWT claims",
        }
    }


def test_timing_map_returns_storage_error_when_loading_fails() -> None:
    """Translate timing object storage failures into the pinned API error."""
    test_client, repo, storage = timing_client()
    key = "users/user-1/readings/reading-1/timing.json"
    add_reading(repo, "user-1", timing_map_key=key)
    storage.fail_load = True

    response = test_client.get("/api/v1/readings/reading-1/timing-map")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "storage_error",
            "message": "Failed to load timing map",
        }
    }
    assert storage.get_calls == [key]


def test_timing_map_endpoint_is_in_openapi() -> None:
    """Publish the protected timing-map endpoint in the OpenAPI document."""
    test_client, _, _ = timing_client()

    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/readings/{reading_id}/timing-map" in response.json()["paths"]
    assert "get" in response.json()["paths"]["/api/v1/readings/{reading_id}/timing-map"]
