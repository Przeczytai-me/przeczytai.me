import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes.user_settings import get_user_settings_repository
from app.tts import EDGE_TTS_VOICES, OPENAI_TTS_VOICES
from test_api import client
from test_api_user_settings import EXPECTED_DEFAULTS, FakeUserSettingsRepository


class RecordingFakeUserSettingsRepository(FakeUserSettingsRepository):
    def __init__(self, items: dict[str, dict] | None = None) -> None:
        super().__init__(items)
        self.put_calls: list[tuple[str, dict]] = []

    def put(self, owner_user_id: str, overrides: dict) -> None:
        self.put_calls.append((owner_user_id, dict(overrides)))
        super().put(owner_user_id, overrides)


class FailOnReadingRepositoryAccess:
    def __getattribute__(self, name: str) -> object:
        if name.startswith("__"):
            return object.__getattribute__(self, name)
        raise AssertionError(f"Reading repository was accessed via {name}")


def settings_client(
    repo: RecordingFakeUserSettingsRepository | None = None,
    auth: bool = True,
    reading_repo: object | None = None,
) -> tuple[TestClient, RecordingFakeUserSettingsRepository]:
    test_client, _ = client(repo=reading_repo, auth=auth)
    repo = repo or RecordingFakeUserSettingsRepository()
    app.dependency_overrides[get_user_settings_repository] = lambda: repo
    return test_client, repo


def assert_validation_error(
    response: object,
    repo: RecordingFakeUserSettingsRepository,
) -> None:
    assert getattr(response, "status_code") == 422
    assert getattr(response, "json")()["error"]["code"] == "validation_error"
    assert repo.put_calls == []


def test_put_settings_full_replaces_overrides_and_returns_effective_settings() -> None:
    """Replace the stored record once and return the resulting effective settings."""
    repo = RecordingFakeUserSettingsRepository(
        {
            "user_1": {
                "tts_voice": "Marek",
                "playback_speed": 0.75,
                "unknown_setting": "stale",
            }
        }
    )
    test_client, _ = settings_client(repo)
    payload = {
        "tts_vendor": "openai",
        "tts_voice": "alloy",
        "pronunciation_style": "Czytaj spokojnie",
        "playback_speed": 1.5,
        "sentence_highlighting": False,
        "export_format": "mp3",
        "abbreviation_readings": [
            {"abbreviation": " AI ", "read_as": " sztuczna inteligencja "},
            {"abbreviation": " dr ", "read_as": " doktor "},
        ],
    }
    stored = payload | {
        "abbreviation_readings": [
            {"abbreviation": "AI", "read_as": "sztuczna inteligencja"},
            {"abbreviation": "dr", "read_as": "doktor"},
        ]
    }

    response = test_client.put("/api/v1/settings", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "settings": EXPECTED_DEFAULTS | stored,
        "defaults": EXPECTED_DEFAULTS,
    }
    assert repo.items["user_1"] == stored
    assert repo.put_calls == [("user_1", stored)]


def test_put_settings_partial_body_removes_unmentioned_overrides() -> None:
    """Treat omitted fields as resets during a full replacement."""
    repo = RecordingFakeUserSettingsRepository(
        {"user_1": {"tts_voice": "Marek", "sentence_highlighting": False}}
    )
    test_client, _ = settings_client(repo)

    response = test_client.put("/api/v1/settings", json={"playback_speed": 1.25})

    assert response.status_code == 200
    assert response.json() == {
        "settings": EXPECTED_DEFAULTS | {"playback_speed": 1.25},
        "defaults": EXPECTED_DEFAULTS,
    }
    assert repo.items["user_1"] == {"playback_speed": 1.25}
    assert repo.put_calls == [("user_1", {"playback_speed": 1.25})]


def test_put_settings_accepts_empty_object_and_stores_no_overrides() -> None:
    """Allow every request field to be omitted."""
    repo = RecordingFakeUserSettingsRepository({"user_1": {"tts_voice": "Marek"}})
    test_client, _ = settings_client(repo)

    response = test_client.put("/api/v1/settings", json={})

    assert response.status_code == 200
    assert response.json() == {"settings": EXPECTED_DEFAULTS, "defaults": EXPECTED_DEFAULTS}
    assert repo.items["user_1"] == {}
    assert repo.put_calls == [("user_1", {})]


def test_put_settings_accepts_null_for_every_field_and_stores_no_overrides() -> None:
    """Allow null for all seven fields and reset each one to its default."""
    repo = RecordingFakeUserSettingsRepository(
        {"user_1": EXPECTED_DEFAULTS | {"tts_voice": "Marek"}}
    )
    test_client, _ = settings_client(repo)
    payload = {key: None for key in EXPECTED_DEFAULTS}

    response = test_client.put("/api/v1/settings", json=payload)

    assert response.status_code == 200
    assert response.json() == {"settings": EXPECTED_DEFAULTS, "defaults": EXPECTED_DEFAULTS}
    assert repo.items["user_1"] == {}
    assert repo.put_calls == [("user_1", {})]


def test_put_settings_uses_authenticated_owner_and_never_touches_readings() -> None:
    """Persist only for the authenticated owner without reading or writing readings."""
    repo = RecordingFakeUserSettingsRepository()
    test_client, _ = settings_client(repo, reading_repo=FailOnReadingRepositoryAccess())

    response = test_client.put("/api/v1/settings", json={"tts_voice": "Marek"})

    assert response.status_code == 200
    assert repo.put_calls == [("user_1", {"tts_voice": "Marek"})]


@pytest.mark.parametrize(
    ("vendor", "voice"),
    [
        *[(None, voice) for voice in EDGE_TTS_VOICES],
        *[(None, voice) for voice in EDGE_TTS_VOICES.values()],
        *[("openai", voice) for voice in OPENAI_TTS_VOICES],
        *[("openai", voice) for voice in OPENAI_TTS_VOICES.values()],
    ],
)
def test_put_settings_accepts_catalog_voice_keys_and_provider_values(
    vendor: str | None,
    voice: str,
) -> None:
    """Accept every friendly voice key and provider value for the effective vendor."""
    test_client, repo = settings_client()
    payload = {"tts_voice": voice}
    if vendor is not None:
        payload["tts_vendor"] = vendor

    response = test_client.put("/api/v1/settings", json=payload)

    assert response.status_code == 200
    assert repo.put_calls == [("user_1", payload)]


@pytest.mark.parametrize("tts_vendor", ["azure", "EDGE-TTS", "", "open-ai"])
def test_put_settings_rejects_unsupported_vendor(tts_vendor: str) -> None:
    """Reject every vendor outside the two supported identifiers before persistence."""
    test_client, repo = settings_client()

    response = test_client.put("/api/v1/settings", json={"tts_vendor": tts_vendor})

    assert_validation_error(response, repo)


@pytest.mark.parametrize(
    "payload",
    [
        {"tts_voice": "alloy"},
        {"tts_vendor": "openai", "tts_voice": "Zofia"},
        {"tts_voice": "not-a-real-voice"},
        {"tts_vendor": "openai", "tts_voice": "not-a-real-voice"},
    ],
)
def test_put_settings_rejects_voice_outside_effective_vendor_catalog(payload: dict) -> None:
    """Reject voices not found in the effective vendor's catalog before persistence."""
    test_client, repo = settings_client()

    response = test_client.put("/api/v1/settings", json=payload)

    assert_validation_error(response, repo)


def test_put_settings_uses_default_vendor_when_vendor_is_omitted() -> None:
    """Validate an omitted-vendor voice against edge-tts even after an OpenAI override."""
    repo = RecordingFakeUserSettingsRepository({"user_1": {"tts_vendor": "openai"}})
    test_client, _ = settings_client(repo)

    response = test_client.put("/api/v1/settings", json={"tts_voice": "alloy"})

    assert_validation_error(response, repo)
    assert repo.items["user_1"] == {"tts_vendor": "openai"}


@pytest.mark.parametrize("playback_speed", [0.5, 2.0])
def test_put_settings_accepts_playback_speed_boundaries(playback_speed: float) -> None:
    """Accept playback speeds at both inclusive limits."""
    test_client, repo = settings_client()

    response = test_client.put(
        "/api/v1/settings",
        json={"playback_speed": playback_speed},
    )

    assert response.status_code == 200
    assert repo.put_calls == [("user_1", {"playback_speed": playback_speed})]


@pytest.mark.parametrize("playback_speed", [0.49, 2.01])
def test_put_settings_rejects_playback_speed_outside_range(playback_speed: float) -> None:
    """Reject playback speeds outside the inclusive range before persistence."""
    test_client, repo = settings_client()

    response = test_client.put(
        "/api/v1/settings",
        json={"playback_speed": playback_speed},
    )

    assert_validation_error(response, repo)


def test_put_settings_rejects_wrong_playback_speed_type() -> None:
    """Return the standard validation error for a nonnumeric playback speed."""
    test_client, repo = settings_client()

    response = test_client.put("/api/v1/settings", json={"playback_speed": "fast"})

    assert_validation_error(response, repo)


@pytest.mark.parametrize("export_format", ["wav", "ogg", "MP3"])
def test_put_settings_rejects_export_format_other_than_mp3(export_format: str) -> None:
    """Reject export formats other than the exact v1 mp3 identifier."""
    test_client, repo = settings_client()

    response = test_client.put("/api/v1/settings", json={"export_format": export_format})

    assert_validation_error(response, repo)


def test_put_settings_accepts_pronunciation_style_at_maximum_length() -> None:
    """Accept a pronunciation style containing exactly 120 characters."""
    test_client, repo = settings_client()
    pronunciation_style = "x" * 120

    response = test_client.put(
        "/api/v1/settings",
        json={"pronunciation_style": pronunciation_style},
    )

    assert response.status_code == 200
    assert repo.put_calls == [("user_1", {"pronunciation_style": pronunciation_style})]


def test_put_settings_rejects_pronunciation_style_over_maximum_length() -> None:
    """Reject a pronunciation style longer than 120 characters before persistence."""
    test_client, repo = settings_client()

    response = test_client.put(
        "/api/v1/settings",
        json={"pronunciation_style": "x" * 121},
    )

    assert_validation_error(response, repo)


@pytest.mark.parametrize("sentence_highlighting", ["true", 1, 0])
def test_put_settings_rejects_non_boolean_sentence_highlighting(
    sentence_highlighting: object,
) -> None:
    """Reject values that are not JSON booleans before persistence."""
    test_client, repo = settings_client()

    response = test_client.put(
        "/api/v1/settings",
        json={"sentence_highlighting": sentence_highlighting},
    )

    assert_validation_error(response, repo)


def test_put_settings_trims_abbreviation_entries_and_preserves_order() -> None:
    """Trim valid abbreviation entries while preserving their request order."""
    test_client, repo = settings_client()
    payload = {
        "abbreviation_readings": [
            {"abbreviation": " AI ", "read_as": " sztuczna inteligencja "},
            {"abbreviation": f" {'x' * 50} ", "read_as": f" {'y' * 200} "},
        ]
    }
    stored_entries = [
        {"abbreviation": "AI", "read_as": "sztuczna inteligencja"},
        {"abbreviation": "x" * 50, "read_as": "y" * 200},
    ]

    response = test_client.put("/api/v1/settings", json=payload)

    assert response.status_code == 200
    assert response.json()["settings"]["abbreviation_readings"] == stored_entries
    assert repo.put_calls == [("user_1", {"abbreviation_readings": stored_entries})]


@pytest.mark.parametrize(
    "entry",
    [
        {"abbreviation": "   ", "read_as": "czytaj"},
        {"abbreviation": "AI", "read_as": " \t\n"},
    ],
)
def test_put_settings_rejects_empty_trimmed_abbreviation_fields(entry: dict) -> None:
    """Reject abbreviation entries whose trimmed field is empty before persistence."""
    test_client, repo = settings_client()

    response = test_client.put(
        "/api/v1/settings",
        json={"abbreviation_readings": [entry]},
    )

    assert_validation_error(response, repo)


@pytest.mark.parametrize(
    "entry",
    [
        {"abbreviation": "x" * 51, "read_as": "czytaj"},
        {"abbreviation": "AI", "read_as": "y" * 201},
    ],
)
def test_put_settings_rejects_overlong_abbreviation_fields(entry: dict) -> None:
    """Reject abbreviation fields over their respective limits before persistence."""
    test_client, repo = settings_client()

    response = test_client.put(
        "/api/v1/settings",
        json={"abbreviation_readings": [entry]},
    )

    assert_validation_error(response, repo)


def test_put_settings_rejects_more_than_100_abbreviation_entries() -> None:
    """Reject an abbreviation list containing more than 100 entries."""
    test_client, repo = settings_client()
    entries = [
        {"abbreviation": f"A{index}", "read_as": f"czytaj {index}"}
        for index in range(101)
    ]

    response = test_client.put(
        "/api/v1/settings",
        json={"abbreviation_readings": entries},
    )

    assert_validation_error(response, repo)


def test_put_settings_rejects_casefolded_duplicate_abbreviations() -> None:
    """Reject duplicate abbreviations after trimming and Unicode casefolding."""
    test_client, repo = settings_client()
    entries = [
        {"abbreviation": " Straße ", "read_as": "ulica"},
        {"abbreviation": "STRASSE", "read_as": "ulica"},
    ]

    response = test_client.put(
        "/api/v1/settings",
        json={"abbreviation_readings": entries},
    )

    assert_validation_error(response, repo)


def test_put_settings_validation_failure_preserves_existing_overrides() -> None:
    """Leave the existing record intact when any request field is invalid."""
    existing = {"tts_voice": "Marek", "playback_speed": 1.25}
    repo = RecordingFakeUserSettingsRepository({"user_1": existing.copy()})
    test_client, _ = settings_client(repo)

    response = test_client.put(
        "/api/v1/settings",
        json={
            "tts_voice": "Zofia",
            "playback_speed": 1.5,
            "export_format": "wav",
        },
    )

    assert_validation_error(response, repo)
    assert repo.items["user_1"] == existing


def test_put_settings_round_trip_matches_followup_get() -> None:
    """Return the same effective settings from PUT and a subsequent GET."""
    test_client, repo = settings_client()
    payload = {
        "tts_voice": "Marek",
        "playback_speed": 1.75,
        "sentence_highlighting": False,
    }

    put_response = test_client.put("/api/v1/settings", json=payload)
    get_response = test_client.get("/api/v1/settings")

    assert put_response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json() == put_response.json()
    assert repo.put_calls == [("user_1", payload)]


def test_put_settings_null_voice_resets_to_default_on_followup_get() -> None:
    """Remove a null voice override and expose the default voice on the next GET."""
    repo = RecordingFakeUserSettingsRepository({"user_1": {"tts_voice": "Marek"}})
    test_client, _ = settings_client(repo)

    put_response = test_client.put("/api/v1/settings", json={"tts_voice": None})
    get_response = test_client.get("/api/v1/settings")

    assert put_response.status_code == 200
    assert repo.items["user_1"] == {}
    assert "tts_voice" not in repo.items["user_1"]
    assert repo.put_calls == [("user_1", {})]
    assert get_response.status_code == 200
    assert get_response.json()["settings"]["tts_voice"] == EXPECTED_DEFAULTS["tts_voice"]
    assert get_response.json() == put_response.json()


def test_put_settings_requires_authentication() -> None:
    """Reject PUT requests without JWT claims before persistence."""
    test_client, repo = settings_client(auth=False)

    response = test_client.put("/api/v1/settings", json={"tts_voice": "Marek"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert repo.requested_user_ids == []
    assert repo.put_calls == []


def test_put_settings_appears_in_openapi() -> None:
    """Publish the PUT method for user settings in the OpenAPI schema."""
    test_client, _ = settings_client()

    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    assert "put" in response.json()["paths"]["/api/v1/settings"]
