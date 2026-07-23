import re

from app.config import Settings
from app.tts import EDGE_TTS_VOICES, OPENAI_TTS_MODEL, OPENAI_TTS_VOICES
from test_api import client


def _language(provider_id: str) -> str:
    if "Multilingual" in provider_id:
        return "multilingual"
    match = re.match(r"^([a-z]{2}-[A-Z]{2})-", provider_id)
    return match.group(1) if match else "multilingual"


def _voice_options(
    voices: dict[str, str], *, openai: bool = False
) -> list[dict[str, str | None]]:
    return [
        {
            "id": voice_id,
            "provider_id": provider_id,
            "label": voice_id.capitalize(),
            "language": "multilingual" if openai else _language(provider_id),
            "preview_url": None,
        }
        for voice_id, provider_id in voices.items()
    ]


EDGE_OPTIONS = {
    "vendors": [{"id": "edge-tts", "label": "Edge TTS"}],
    "models": [{"id": "edge-tts", "vendor_id": "edge-tts", "label": "Edge TTS"}],
    "voices": _voice_options(EDGE_TTS_VOICES),
    "pronunciation_styles": [
        {"id": "natural", "label": "Naturalny"},
        {"id": "clear", "label": "Wyraźny"},
    ],
    "defaults": {
        "model": "edge-tts",
        "voice": "Zofia",
        "pronunciation_style": "natural",
    },
}


def test_tts_options_returns_frontend_edge_catalog() -> None:
    """Return the frontend contract with the complete ordered Edge catalog."""
    test_client, _ = client(
        settings=Settings(max_text_chars=10, openai_tts_enabled=False)
    )

    response = test_client.get("/api/v1/tts-options")

    assert response.status_code == 200
    assert response.json() == EDGE_OPTIONS


def test_tts_options_adds_openai_catalog_when_enabled() -> None:
    """Append the OpenAI vendor, model, and voices only when configured."""
    test_client, _ = client(
        settings=Settings(max_text_chars=10, openai_tts_enabled=True)
    )

    response = test_client.get("/api/v1/tts-options")

    assert response.status_code == 200
    assert response.json() == {
        **EDGE_OPTIONS,
        "vendors": EDGE_OPTIONS["vendors"] + [{"id": "openai", "label": "OpenAI"}],
        "models": EDGE_OPTIONS["models"]
        + [
            {
                "id": OPENAI_TTS_MODEL,
                "vendor_id": "openai",
                "label": "OpenAI TTS",
            }
        ],
        "voices": EDGE_OPTIONS["voices"]
        + _voice_options(OPENAI_TTS_VOICES, openai=True),
    }


def test_tts_options_uses_multilingual_language_for_multilingual_voices() -> None:
    """Label multilingual Edge voices independently of their locale prefix."""
    test_client, _ = client(
        settings=Settings(max_text_chars=10, openai_tts_enabled=False)
    )

    voices = {
        voice["id"]: voice
        for voice in test_client.get("/api/v1/tts-options").json()["voices"]
    }

    assert voices["Zofia"]["language"] == "pl-PL"
    assert voices["Ava"]["language"] == "multilingual"


def test_tts_options_excludes_all_openai_entries_when_disabled() -> None:
    """Exclude every OpenAI catalog entry when OpenAI is disabled."""
    test_client, _ = client(
        settings=Settings(max_text_chars=10, openai_tts_enabled=False)
    )

    body = test_client.get("/api/v1/tts-options").json()

    assert [vendor["id"] for vendor in body["vendors"]] == ["edge-tts"]
    assert [model["id"] for model in body["models"]] == ["edge-tts"]
    assert [voice["id"] for voice in body["voices"]] == list(EDGE_TTS_VOICES)


def test_tts_options_requires_authentication() -> None:
    """Reject TTS options requests without JWT claims."""
    test_client, _ = client(
        auth=False,
        settings=Settings(max_text_chars=10, openai_tts_enabled=False),
    )

    response = test_client.get("/api/v1/tts-options")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_tts_options_appears_in_openapi() -> None:
    """Publish the protected TTS options endpoint in OpenAPI."""
    test_client, _ = client(
        settings=Settings(max_text_chars=10, openai_tts_enabled=False)
    )

    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    assert "get" in response.json()["paths"]["/api/v1/tts-options"]
