import re

from app.config import Settings
from app.tts import (
    DEFAULT_TTS_VENDOR,
    EDGE_TTS_VOICE,
    EDGE_TTS_VOICES,
    OPENAI_TTS_MODEL,
    OPENAI_TTS_VOICE,
    OPENAI_TTS_VOICES,
)
from test_api import client


def _language(provider_voice: str) -> str | None:
    match = re.match(r"^([a-z]{2}-[A-Z]{2})-", provider_voice)
    return match.group(1) if match else None


def _voice_options(voices: dict[str, str]) -> list[dict[str, str | None]]:
    return [
        {
            "id": voice_id,
            "label": voice_id.capitalize(),
            "provider_voice": provider_voice,
            "language": _language(provider_voice),
            "preview_url": None,
        }
        for voice_id, provider_voice in voices.items()
    ]


def test_tts_options_returns_edge_tts_catalog() -> None:
    """Return the complete Edge TTS catalog in its configured order."""
    test_client, _ = client(settings=Settings(max_text_chars=10, openai_tts_enabled=False))

    response = test_client.get("/api/v1/tts-options")

    assert response.status_code == 200
    assert response.json() == {
        "default_vendor": "edge-tts",
        "vendors": [
            {
                "id": "edge-tts",
                "label": "Edge TTS",
                "model": None,
                "default_voice": "Zofia",
                "voices": _voice_options(EDGE_TTS_VOICES),
            }
        ],
    }


def test_tts_options_includes_openai_when_enabled() -> None:
    """Advertise the complete OpenAI catalog only when it is enabled."""
    test_client, _ = client(
        settings=Settings(max_text_chars=10, openai_tts_enabled=True)
    )

    response = test_client.get("/api/v1/tts-options")

    assert response.status_code == 200
    openai = response.json()["vendors"][1]
    assert openai == {
        "id": "openai",
        "label": "OpenAI",
        "model": "gpt-4o-mini-tts",
        "default_voice": "alloy",
        "voices": _voice_options(OPENAI_TTS_VOICES),
    }


def test_tts_options_excludes_openai_when_disabled() -> None:
    """Do not advertise OpenAI when the effective settings disable it."""
    test_client, _ = client(
        settings=Settings(max_text_chars=10, openai_tts_enabled=False)
    )

    response = test_client.get("/api/v1/tts-options")

    assert response.status_code == 200
    assert [vendor["id"] for vendor in response.json()["vendors"]] == ["edge-tts"]


def test_tts_options_defaults_use_friendly_voice_ids() -> None:
    """Expose registry defaults as stable frontend-facing identifiers."""
    test_client, _ = client(
        settings=Settings(max_text_chars=10, openai_tts_enabled=True)
    )

    response = test_client.get("/api/v1/tts-options")

    assert response.status_code == 200
    body = response.json()
    vendors = {vendor["id"]: vendor for vendor in body["vendors"]}
    assert body["default_vendor"] == DEFAULT_TTS_VENDOR == "edge-tts"
    assert vendors["edge-tts"]["default_voice"] == "Zofia"
    assert EDGE_TTS_VOICES["Zofia"] == EDGE_TTS_VOICE
    assert vendors["openai"]["default_voice"] == "alloy"
    assert OPENAI_TTS_VOICES["alloy"] == OPENAI_TTS_VOICE
    assert vendors["openai"]["model"] == OPENAI_TTS_MODEL == "gpt-4o-mini-tts"


def test_tts_options_derives_languages_from_provider_voices() -> None:
    """Derive locale languages and leave non-locale provider voices null."""
    test_client, _ = client(
        settings=Settings(max_text_chars=10, openai_tts_enabled=True)
    )

    response = test_client.get("/api/v1/tts-options")

    assert response.status_code == 200
    vendors = {vendor["id"]: vendor for vendor in response.json()["vendors"]}
    assert [voice["language"] for voice in vendors["edge-tts"]["voices"]] == [
        _language(provider_voice) for provider_voice in EDGE_TTS_VOICES.values()
    ]
    assert [voice["language"] for voice in vendors["openai"]["voices"]] == [
        None for _ in OPENAI_TTS_VOICES
    ]
    edge_voices = {voice["id"]: voice for voice in vendors["edge-tts"]["voices"]}
    assert edge_voices["Zofia"]["language"] == "pl-PL"
    assert edge_voices["Ava"]["language"] == "en-US"


def test_tts_options_requires_authentication() -> None:
    """Reject TTS options requests without JWT claims."""
    test_client, _ = client(auth=False)

    response = test_client.get("/api/v1/tts-options")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_tts_options_appears_in_openapi() -> None:
    """Publish the TTS options endpoint in the OpenAPI schema."""
    test_client, _ = client()

    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/tts-options" in response.json()["paths"]
