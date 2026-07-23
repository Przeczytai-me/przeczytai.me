from copy import deepcopy

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.routes.user_settings import get_user_settings_repository
from test_api import client

EPOCH_UPDATED_AT = "1970-01-01T00:00:00Z"
SAVED_UPDATED_AT = "2026-07-22T12:34:56Z"
DEFAULT_SETTINGS = {
    "reading_model": "edge-tts",
    "fallback_model": None,
    "voice": "Zofia",
    "pronunciation_style": "natural",
    "playback_speed": 1.0,
    "sentence_highlighting": True,
    "custom_abbreviation_readings": [],
    "exports": {
        "filename_pattern": "{reading_id}",
        "mp3_quality": "standard",
        "text_format": "md",
    },
    "updated_at": EPOCH_UPDATED_AT,
}
DEFAULT_PUT_SETTINGS = {
    key: deepcopy(value) for key, value in DEFAULT_SETTINGS.items() if key != "updated_at"
}


class FakeUserSettingsRepository:
    def __init__(self, items: dict[str, dict] | None = None) -> None:
        self.items = deepcopy(items or {})
        self.requested_user_ids: list[str] = []
        self.put_calls: list[tuple[str, dict]] = []

    def get(self, owner_user_id: str) -> dict | None:
        self.requested_user_ids.append(owner_user_id)
        item = self.items.get(owner_user_id)
        return deepcopy(item) if item is not None else None

    def put(self, owner_user_id: str, settings: dict) -> str:
        recorded = deepcopy(settings)
        self.put_calls.append((owner_user_id, recorded))
        self.items[owner_user_id] = recorded | {"updated_at": SAVED_UPDATED_AT}
        return SAVED_UPDATED_AT


def settings_client(
    repo: FakeUserSettingsRepository | None = None,
    *,
    auth: bool = True,
    openai_enabled: bool = False,
    reading_repo: object | None = None,
) -> tuple[TestClient, FakeUserSettingsRepository]:
    test_client, _ = client(
        repo=reading_repo,
        auth=auth,
        settings=Settings(max_text_chars=10, openai_tts_enabled=openai_enabled),
    )
    repo = repo or FakeUserSettingsRepository()
    app.dependency_overrides[get_user_settings_repository] = lambda: repo
    return test_client, repo


def test_settings_returns_bare_defaults_for_new_user() -> None:
    """Return frontend defaults and the epoch timestamp for an unsaved user."""
    test_client, _ = settings_client()

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json() == DEFAULT_SETTINGS


def test_settings_overlays_known_stored_values_on_defaults() -> None:
    """Overlay known stored fields and default fields absent from an older record."""
    repo = FakeUserSettingsRepository(
        {
            "user_1": {
                "voice": "Marek",
                "playback_speed": 1.5,
                "updated_at": SAVED_UPDATED_AT,
            }
        }
    )
    test_client, _ = settings_client(repo)

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json() == DEFAULT_SETTINGS | {
        "voice": "Marek",
        "playback_speed": 1.5,
        "updated_at": SAVED_UPDATED_AT,
    }


def test_settings_ignores_unknown_stored_keys() -> None:
    """Ignore unknown persisted fields during schema evolution."""
    repo = FakeUserSettingsRepository(
        {
            "user_1": {
                "voice": "Marek",
                "unknown_setting": "ignored",
                "updated_at": SAVED_UPDATED_AT,
            }
        }
    )
    test_client, _ = settings_client(repo)

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json() == DEFAULT_SETTINGS | {
        "voice": "Marek",
        "updated_at": SAVED_UPDATED_AT,
    }
    assert "unknown_setting" not in response.json()


def test_settings_preserves_custom_abbreviation_order() -> None:
    """Return custom abbreviation readings in their stored order."""
    readings = [
        {"abbreviation": "AI", "read_as": "sztuczna inteligencja"},
        {"abbreviation": "dr", "read_as": "doktor"},
    ]
    repo = FakeUserSettingsRepository(
        {
            "user_1": {
                "custom_abbreviation_readings": readings,
                "updated_at": SAVED_UPDATED_AT,
            }
        }
    )
    test_client, _ = settings_client(repo)

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json()["custom_abbreviation_readings"] == readings


def test_settings_queries_only_authenticated_user() -> None:
    """Load settings with only the authenticated user's id."""
    repo = FakeUserSettingsRepository(
        {
            "user_1": {"voice": "Marek", "updated_at": SAVED_UPDATED_AT},
            "user_2": {"voice": "Ava", "updated_at": SAVED_UPDATED_AT},
        }
    )
    test_client, _ = settings_client(repo)

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json()["voice"] == "Marek"
    assert repo.requested_user_ids == ["user_1"]


def test_settings_requires_authentication() -> None:
    """Reject settings requests without JWT claims before repository access."""
    test_client, repo = settings_client(auth=False)

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert repo.requested_user_ids == []


def test_settings_get_and_put_appear_in_openapi() -> None:
    """Publish both settings methods in the OpenAPI schema."""
    test_client, _ = settings_client()

    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    assert {"get", "put"} <= set(response.json()["paths"]["/api/v1/settings"])
