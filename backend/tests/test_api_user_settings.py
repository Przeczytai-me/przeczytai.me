from fastapi.testclient import TestClient

from app.main import app
from app.models import DEFAULT_USER_SETTINGS
from app.routes.user_settings import get_user_settings_repository
from test_api import client

EXPECTED_DEFAULTS = {
    "tts_vendor": "edge-tts",
    "tts_voice": "Zofia",
    "pronunciation_style": None,
    "playback_speed": 1.0,
    "sentence_highlighting": True,
    "export_format": "mp3",
    "abbreviation_readings": [],
}


class FakeUserSettingsRepository:
    def __init__(self, items: dict[str, dict] | None = None) -> None:
        self.items = items or {}
        self.requested_user_ids: list[str] = []

    def get(self, owner_user_id: str) -> dict | None:
        self.requested_user_ids.append(owner_user_id)
        return self.items.get(owner_user_id)

    def put(self, owner_user_id: str, overrides: dict) -> None:
        self.items[owner_user_id] = overrides


def settings_client(
    repo: FakeUserSettingsRepository | None = None,
    auth: bool = True,
) -> tuple[TestClient, FakeUserSettingsRepository]:
    test_client, _ = client(auth=auth)
    repo = repo or FakeUserSettingsRepository()
    app.dependency_overrides[get_user_settings_repository] = lambda: repo
    return test_client, repo


def test_settings_returns_defaults_for_new_user() -> None:
    """Return the exact backend defaults when the user has no saved overrides."""
    test_client, _ = settings_client()

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 200
    assert DEFAULT_USER_SETTINGS == EXPECTED_DEFAULTS
    assert response.json() == {
        "settings": EXPECTED_DEFAULTS,
        "defaults": EXPECTED_DEFAULTS,
    }


def test_settings_merges_persisted_overrides_with_defaults() -> None:
    """Overlay persisted user values while retaining every backend default."""
    repo = FakeUserSettingsRepository(
        {"user_1": {"tts_voice": "Marek", "playback_speed": 1.5}}
    )
    test_client, _ = settings_client(repo)

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json() == {
        "settings": EXPECTED_DEFAULTS | {"tts_voice": "Marek", "playback_speed": 1.5},
        "defaults": EXPECTED_DEFAULTS,
    }


def test_settings_falls_back_to_new_default_missing_from_stored_overrides() -> None:
    """Use a newly introduced default when an older override dict omits its key."""
    repo = FakeUserSettingsRepository({"user_1": {"tts_vendor": "openai"}})
    test_client, _ = settings_client(repo)

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json()["settings"]["sentence_highlighting"] is True


def test_settings_ignores_unknown_stored_keys() -> None:
    """Exclude unknown persisted keys from the effective settings response."""
    repo = FakeUserSettingsRepository(
        {"user_1": {"tts_voice": "Marek", "unknown_setting": "ignored"}}
    )
    test_client, _ = settings_client(repo)

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 200
    body = response.json()
    assert body["settings"] == EXPECTED_DEFAULTS | {"tts_voice": "Marek"}
    assert "unknown_setting" not in body["settings"]
    assert "unknown_setting" not in body["defaults"]


def test_settings_preserves_abbreviation_readings_order() -> None:
    """Return abbreviation readings in their persisted order."""
    abbreviation_readings = [
        {"abbreviation": "AI", "read_as": "sztuczna inteligencja"},
        {"abbreviation": "dr", "read_as": "doktor"},
    ]
    repo = FakeUserSettingsRepository(
        {"user_1": {"abbreviation_readings": abbreviation_readings}}
    )
    test_client, _ = settings_client(repo)

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json()["settings"]["abbreviation_readings"] == abbreviation_readings


def test_settings_queries_only_authenticated_user() -> None:
    """Load settings only for the authenticated user's id."""
    repo = FakeUserSettingsRepository(
        {
            "user_1": {"tts_voice": "Marek"},
            "user_2": {"tts_voice": "Ava"},
        }
    )
    test_client, _ = settings_client(repo)

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 200
    assert response.json()["settings"]["tts_voice"] == "Marek"
    assert repo.requested_user_ids == ["user_1"]


def test_settings_requires_authentication() -> None:
    """Reject settings requests without JWT claims."""
    test_client, repo = settings_client(auth=False)

    response = test_client.get("/api/v1/settings")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert repo.requested_user_ids == []


def test_settings_appears_in_openapi() -> None:
    """Publish the user settings endpoint in the OpenAPI schema."""
    test_client, _ = settings_client()

    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/settings" in response.json()["paths"]
