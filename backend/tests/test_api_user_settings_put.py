from copy import deepcopy
from datetime import datetime

import pytest

from app.tts import EDGE_TTS_VOICES, OPENAI_TTS_VOICES
from test_api_user_settings import (
    DEFAULT_PUT_SETTINGS,
    DEFAULT_SETTINGS,
    EPOCH_UPDATED_AT,
    FakeUserSettingsRepository,
    SAVED_UPDATED_AT,
    settings_client,
)


class FailOnReadingRepositoryAccess:
    def __getattribute__(self, name: str) -> object:
        if name.startswith("__"):
            return object.__getattribute__(self, name)
        raise AssertionError(f"Reading repository was accessed via {name}")


def payload(**changes: object) -> dict:
    return deepcopy(DEFAULT_PUT_SETTINGS) | changes


def assert_iso_timestamp(value: str) -> None:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None


def assert_validation_error(response: object, repo: FakeUserSettingsRepository) -> None:
    assert getattr(response, "status_code") == 422
    assert getattr(response, "json")()["error"]["code"] == "validation_error"
    assert repo.put_calls == []


def test_put_settings_full_replaces_record_and_returns_bare_settings() -> None:
    """Replace the stored record with the complete validated settings object."""
    repo = FakeUserSettingsRepository(
        {
            "user_1": {
                "voice": "Ava",
                "unknown_setting": "stale",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        }
    )
    test_client, _ = settings_client(repo)
    request_body = payload(
        voice="Marek",
        pronunciation_style="clear",
        playback_speed=1.5,
        sentence_highlighting=False,
        custom_abbreviation_readings=[
            {"abbreviation": " AI ", "read_as": " sztuczna inteligencja "},
            {"abbreviation": " dr ", "read_as": " doktor "},
        ],
        exports={
            "filename_pattern": "czytanie-{reading_id}",
            "mp3_quality": "standard",
            "text_format": "txt",
        },
    )
    normalized = request_body | {
        "custom_abbreviation_readings": [
            {"abbreviation": "AI", "read_as": "sztuczna inteligencja"},
            {"abbreviation": "dr", "read_as": "doktor"},
        ]
    }

    response = test_client.put("/api/v1/settings", json=request_body)

    assert response.status_code == 200
    assert response.json() == normalized | {"updated_at": SAVED_UPDATED_AT}
    assert repo.put_calls == [("user_1", normalized)]
    assert "updated_at" not in repo.put_calls[0][1]
    assert_iso_timestamp(response.json()["updated_at"])
    assert response.json()["updated_at"] != EPOCH_UPDATED_AT


def test_put_settings_round_trip_exactly_matches_followup_get() -> None:
    """Return exactly the replaced values from a subsequent GET."""
    test_client, repo = settings_client()
    request_body = payload(
        voice="Marek",
        playback_speed=1.75,
        sentence_highlighting=False,
    )

    put_response = test_client.put("/api/v1/settings", json=request_body)
    get_response = test_client.get("/api/v1/settings")

    assert put_response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json() == put_response.json()
    assert repo.put_calls == [("user_1", request_body)]


def test_put_settings_can_reset_every_value_to_defaults() -> None:
    """Reset saved settings by replacing them with the complete defaults."""
    repo = FakeUserSettingsRepository(
        {"user_1": payload(voice="Marek") | {"updated_at": SAVED_UPDATED_AT}}
    )
    test_client, _ = settings_client(repo)

    response = test_client.put("/api/v1/settings", json=DEFAULT_PUT_SETTINGS)

    assert response.status_code == 200
    assert response.json() == DEFAULT_SETTINGS | {"updated_at": SAVED_UPDATED_AT}
    assert repo.put_calls == [("user_1", DEFAULT_PUT_SETTINGS)]


def test_put_settings_ignores_client_updated_at() -> None:
    """Ignore a client timestamp and return a server-set timestamp."""
    test_client, repo = settings_client()
    request_body = payload(updated_at="1999-12-31T23:59:59Z")

    response = test_client.put("/api/v1/settings", json=request_body)

    assert response.status_code == 200
    assert response.json()["updated_at"] == SAVED_UPDATED_AT
    assert repo.put_calls == [("user_1", DEFAULT_PUT_SETTINGS)]


def test_put_settings_allows_omitted_nullable_fallback_model() -> None:
    """Default an omitted nullable fallback model to null on full replacement."""
    test_client, repo = settings_client()
    request_body = payload()
    request_body.pop("fallback_model")

    response = test_client.put("/api/v1/settings", json=request_body)

    assert response.status_code == 200
    assert response.json()["fallback_model"] is None
    assert repo.put_calls == [("user_1", DEFAULT_PUT_SETTINGS)]


@pytest.mark.parametrize(
    "missing_field",
    [
        "reading_model",
        "voice",
        "pronunciation_style",
        "playback_speed",
        "sentence_highlighting",
        "custom_abbreviation_readings",
        "exports",
    ],
)
def test_put_settings_rejects_missing_required_field(missing_field: str) -> None:
    """Reject a request that omits any required full-object field."""
    test_client, repo = settings_client()
    request_body = payload()
    request_body.pop(missing_field)

    response = test_client.put("/api/v1/settings", json=request_body)

    assert_validation_error(response, repo)


@pytest.mark.parametrize("reading_model", ["unknown", "openai", "EDGE-TTS", ""])
def test_put_settings_rejects_unadvertised_reading_model(reading_model: str) -> None:
    """Reject reading models not advertised by the configured catalog."""
    test_client, repo = settings_client()

    response = test_client.put(
        "/api/v1/settings", json=payload(reading_model=reading_model)
    )

    assert_validation_error(response, repo)


def test_put_settings_rejects_openai_model_when_disabled() -> None:
    """Reject the OpenAI model when its provider is not configured."""
    test_client, repo = settings_client(openai_enabled=False)

    response = test_client.put(
        "/api/v1/settings",
        json=payload(reading_model="gpt-4o-mini-tts", voice="alloy"),
    )

    assert_validation_error(response, repo)


def test_put_settings_accepts_openai_model_when_enabled() -> None:
    """Accept the OpenAI model and one of its voices when configured."""
    test_client, repo = settings_client(openai_enabled=True)
    request_body = payload(reading_model="gpt-4o-mini-tts", voice="alloy")

    response = test_client.put("/api/v1/settings", json=request_body)

    assert response.status_code == 200
    assert response.json()["reading_model"] == "gpt-4o-mini-tts"
    assert response.json()["voice"] == "alloy"
    assert repo.put_calls == [("user_1", request_body)]


@pytest.mark.parametrize("fallback_model", [None, "edge-tts"])
def test_put_settings_accepts_nullable_advertised_fallback(
    fallback_model: str | None,
) -> None:
    """Accept null or an advertised model as the fallback."""
    test_client, repo = settings_client()
    request_body = payload(fallback_model=fallback_model)

    response = test_client.put("/api/v1/settings", json=request_body)

    assert response.status_code == 200
    assert repo.put_calls == [("user_1", request_body)]


@pytest.mark.parametrize("fallback_model", ["unknown", "gpt-4o-mini-tts"])
def test_put_settings_rejects_unadvertised_fallback_model(fallback_model: str) -> None:
    """Reject a fallback model absent from the configured catalog."""
    test_client, repo = settings_client(openai_enabled=False)

    response = test_client.put(
        "/api/v1/settings", json=payload(fallback_model=fallback_model)
    )

    assert_validation_error(response, repo)


def test_put_settings_accepts_enabled_openai_fallback_model() -> None:
    """Accept the OpenAI model as fallback when it is advertised."""
    test_client, repo = settings_client(openai_enabled=True)
    request_body = payload(fallback_model="gpt-4o-mini-tts")

    response = test_client.put("/api/v1/settings", json=request_body)

    assert response.status_code == 200
    assert repo.put_calls == [("user_1", request_body)]


@pytest.mark.parametrize("voice", [*EDGE_TTS_VOICES, *EDGE_TTS_VOICES.values()])
def test_put_settings_accepts_and_normalizes_every_edge_voice(voice: str) -> None:
    """Normalize every Edge friendly key and provider value to its friendly key."""
    test_client, repo = settings_client()
    expected_voice = next(
        key for key, provider_id in EDGE_TTS_VOICES.items() if voice in {key, provider_id}
    )
    expected = payload(voice=expected_voice)

    response = test_client.put("/api/v1/settings", json=payload(voice=voice))

    assert response.status_code == 200
    assert response.json()["voice"] == expected_voice
    assert repo.put_calls == [("user_1", expected)]


@pytest.mark.parametrize("voice", [*OPENAI_TTS_VOICES, *OPENAI_TTS_VOICES.values()])
def test_put_settings_accepts_every_openai_voice_when_enabled(voice: str) -> None:
    """Accept every OpenAI voice for the advertised OpenAI model."""
    test_client, repo = settings_client(openai_enabled=True)
    request_body = payload(reading_model="gpt-4o-mini-tts", voice=voice)

    response = test_client.put("/api/v1/settings", json=request_body)

    assert response.status_code == 200
    assert response.json()["voice"] == voice
    assert repo.put_calls == [("user_1", request_body)]


@pytest.mark.parametrize(
    "request_body",
    [
        payload(voice="alloy"),
        payload(reading_model="gpt-4o-mini-tts", voice="Zofia"),
        payload(voice="not-a-real-voice"),
    ],
)
def test_put_settings_rejects_unknown_or_cross_vendor_voice(request_body: dict) -> None:
    """Reject voices unknown to or outside the reading model's vendor."""
    openai_enabled = request_body["reading_model"] == "gpt-4o-mini-tts"
    test_client, repo = settings_client(openai_enabled=openai_enabled)

    response = test_client.put("/api/v1/settings", json=request_body)

    assert_validation_error(response, repo)


@pytest.mark.parametrize("pronunciation_style", ["natural", "clear"])
def test_put_settings_accepts_supported_pronunciation_style(
    pronunciation_style: str,
) -> None:
    """Accept both advertised pronunciation styles."""
    test_client, repo = settings_client()
    request_body = payload(pronunciation_style=pronunciation_style)

    response = test_client.put("/api/v1/settings", json=request_body)

    assert response.status_code == 200
    assert repo.put_calls == [("user_1", request_body)]


@pytest.mark.parametrize("pronunciation_style", ["expressive", "Natural", ""])
def test_put_settings_rejects_unsupported_pronunciation_style(
    pronunciation_style: str,
) -> None:
    """Reject pronunciation styles outside the advertised identifiers."""
    test_client, repo = settings_client()

    response = test_client.put(
        "/api/v1/settings",
        json=payload(pronunciation_style=pronunciation_style),
    )

    assert_validation_error(response, repo)


@pytest.mark.parametrize("playback_speed", [0.5, 1.0, 2.0])
def test_put_settings_accepts_playback_speed_range(playback_speed: float) -> None:
    """Accept playback speeds at and within both inclusive limits."""
    test_client, repo = settings_client()
    request_body = payload(playback_speed=playback_speed)

    response = test_client.put("/api/v1/settings", json=request_body)

    assert response.status_code == 200
    assert repo.put_calls == [("user_1", request_body)]


@pytest.mark.parametrize("playback_speed", [0.49, 2.01, "1.0", True])
def test_put_settings_rejects_invalid_playback_speed(playback_speed: object) -> None:
    """Reject out-of-range or non-strict playback speeds."""
    test_client, repo = settings_client()

    response = test_client.put(
        "/api/v1/settings", json=payload(playback_speed=playback_speed)
    )

    assert_validation_error(response, repo)


@pytest.mark.parametrize("sentence_highlighting", ["true", 1, 0, None])
def test_put_settings_rejects_non_boolean_sentence_highlighting(
    sentence_highlighting: object,
) -> None:
    """Reject values that are not strict JSON booleans."""
    test_client, repo = settings_client()

    response = test_client.put(
        "/api/v1/settings",
        json=payload(sentence_highlighting=sentence_highlighting),
    )

    assert_validation_error(response, repo)


def test_put_settings_rejects_empty_filename_pattern_after_trim() -> None:
    """Reject an export filename pattern empty after trimming."""
    test_client, repo = settings_client()
    exports = deepcopy(DEFAULT_PUT_SETTINGS["exports"])
    exports["filename_pattern"] = " \t "

    response = test_client.put("/api/v1/settings", json=payload(exports=exports))

    assert_validation_error(response, repo)


def test_put_settings_accepts_filename_pattern_at_maximum_length() -> None:
    """Accept an export filename pattern containing exactly 120 characters."""
    test_client, repo = settings_client()
    exports = deepcopy(DEFAULT_PUT_SETTINGS["exports"])
    exports["filename_pattern"] = "x" * 120
    request_body = payload(exports=exports)

    response = test_client.put("/api/v1/settings", json=request_body)

    assert response.status_code == 200
    assert repo.put_calls == [("user_1", request_body)]


def test_put_settings_rejects_filename_pattern_over_maximum_length() -> None:
    """Reject an export filename pattern longer than 120 characters."""
    test_client, repo = settings_client()
    exports = deepcopy(DEFAULT_PUT_SETTINGS["exports"])
    exports["filename_pattern"] = "x" * 121

    response = test_client.put("/api/v1/settings", json=payload(exports=exports))

    assert_validation_error(response, repo)


@pytest.mark.parametrize("mp3_quality", ["high", "STANDARD", ""])
def test_put_settings_rejects_unsupported_mp3_quality(mp3_quality: str) -> None:
    """Accept only the standard MP3 quality identifier."""
    test_client, repo = settings_client()
    exports = deepcopy(DEFAULT_PUT_SETTINGS["exports"])
    exports["mp3_quality"] = mp3_quality

    response = test_client.put("/api/v1/settings", json=payload(exports=exports))

    assert_validation_error(response, repo)


@pytest.mark.parametrize("text_format", ["md", "txt"])
def test_put_settings_accepts_supported_text_format(text_format: str) -> None:
    """Accept Markdown and plain-text export formats."""
    test_client, repo = settings_client()
    exports = deepcopy(DEFAULT_PUT_SETTINGS["exports"])
    exports["text_format"] = text_format
    request_body = payload(exports=exports)

    response = test_client.put("/api/v1/settings", json=request_body)

    assert response.status_code == 200
    assert repo.put_calls == [("user_1", request_body)]


@pytest.mark.parametrize("text_format", ["ssml", "pdf", "MD", ""])
def test_put_settings_rejects_unsupported_text_format(text_format: str) -> None:
    """Reject text export formats outside Markdown and plain text."""
    test_client, repo = settings_client()
    exports = deepcopy(DEFAULT_PUT_SETTINGS["exports"])
    exports["text_format"] = text_format

    response = test_client.put("/api/v1/settings", json=payload(exports=exports))

    assert_validation_error(response, repo)


def test_put_settings_trims_abbreviations_and_preserves_order() -> None:
    """Trim abbreviation fields while preserving their request order."""
    test_client, repo = settings_client()
    readings = [
        {"abbreviation": " AI ", "read_as": " sztuczna inteligencja "},
        {"abbreviation": f" {'x' * 50} ", "read_as": f" {'y' * 200} "},
    ]
    normalized = [
        {"abbreviation": "AI", "read_as": "sztuczna inteligencja"},
        {"abbreviation": "x" * 50, "read_as": "y" * 200},
    ]

    response = test_client.put(
        "/api/v1/settings", json=payload(custom_abbreviation_readings=readings)
    )

    assert response.status_code == 200
    assert response.json()["custom_abbreviation_readings"] == normalized
    assert repo.put_calls == [
        ("user_1", payload(custom_abbreviation_readings=normalized))
    ]


@pytest.mark.parametrize(
    "entry",
    [
        {"abbreviation": "   ", "read_as": "czytaj"},
        {"abbreviation": "AI", "read_as": " \t\n"},
        {"abbreviation": "x" * 51, "read_as": "czytaj"},
        {"abbreviation": "AI", "read_as": "y" * 201},
    ],
)
def test_put_settings_rejects_invalid_abbreviation_field(entry: dict) -> None:
    """Reject empty or overlong trimmed abbreviation fields."""
    test_client, repo = settings_client()

    response = test_client.put(
        "/api/v1/settings",
        json=payload(custom_abbreviation_readings=[entry]),
    )

    assert_validation_error(response, repo)


def test_put_settings_rejects_more_than_100_abbreviation_entries() -> None:
    """Reject an abbreviation list containing more than 100 entries."""
    test_client, repo = settings_client()
    readings = [
        {"abbreviation": f"A{index}", "read_as": f"czytaj {index}"}
        for index in range(101)
    ]

    response = test_client.put(
        "/api/v1/settings",
        json=payload(custom_abbreviation_readings=readings),
    )

    assert_validation_error(response, repo)


def test_put_settings_rejects_casefolded_duplicate_abbreviations() -> None:
    """Reject duplicate abbreviations after trimming and Unicode casefolding."""
    test_client, repo = settings_client()
    readings = [
        {"abbreviation": " Straße ", "read_as": "ulica"},
        {"abbreviation": "STRASSE", "read_as": "ulica"},
    ]

    response = test_client.put(
        "/api/v1/settings",
        json=payload(custom_abbreviation_readings=readings),
    )

    assert_validation_error(response, repo)


def test_put_settings_uses_owner_and_never_touches_readings() -> None:
    """Persist only for the authenticated owner without touching readings."""
    test_client, repo = settings_client(
        reading_repo=FailOnReadingRepositoryAccess()
    )

    response = test_client.put("/api/v1/settings", json=payload())

    assert response.status_code == 200
    assert repo.put_calls == [("user_1", DEFAULT_PUT_SETTINGS)]


def test_put_settings_requires_authentication() -> None:
    """Reject unauthenticated replacement before persistence."""
    test_client, repo = settings_client(auth=False)

    response = test_client.put("/api/v1/settings", json=payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"
    assert repo.put_calls == []
