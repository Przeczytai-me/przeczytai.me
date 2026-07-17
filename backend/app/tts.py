import json
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache

from app.config import Settings


class TtsVendor(StrEnum):
    EDGE_TTS = "edge-tts"
    OPENAI = "openai"


DEFAULT_TTS_VENDOR = TtsVendor.EDGE_TTS

EDGE_TTS_VOICES = {
    "Zofia": "pl-PL-ZofiaNeural",
    "Marek": "pl-PL-MarekNeural",
    "Ava": "en-US-AvaMultilingualNeural",
    "Andrew": "en-US-AndrewMultilingualNeural",
    "Brian": "en-US-BrianMultilingualNeural",
    "Emma": "en-US-EmmaMultilingualNeural",
}
EDGE_TTS_VOICE = EDGE_TTS_VOICES["Zofia"]

OPENAI_TTS_MODEL = "gpt-4o-mini-tts"
OPENAI_TTS_INPUT_MAX_CHARS = 4096
OPENAI_TTS_VOICE = "alloy"
OPENAI_TTS_VOICES = {
    "alloy": "alloy",
    "ash": "ash",
    "ballad": "ballad",
    "coral": "coral",
    "echo": "echo",
    "fable": "fable",
    "marin": "marin",
    "nova": "nova",
    "onyx": "onyx",
    "sage": "sage",
    "shimmer": "shimmer",
    "verse": "verse",
    "cedar": "cedar",
}


class UnsupportedTtsVendorError(Exception):
    pass


class TtsInputTooLargeError(Exception):
    pass


class TtsProviderUnavailableError(Exception):
    pass


class TtsConfigurationError(Exception):
    pass


@dataclass(frozen=True)
class TtsSelection:
    vendor: TtsVendor
    voice: str


Synthesizer = Callable[[str, str, TtsSelection, Settings | None], Awaitable[None]]
ConfigCheck = Callable[[Settings | None], bool]


@dataclass(frozen=True)
class TtsProvider:
    vendor: TtsVendor
    default_voice: str
    voices: Mapping[str, str]
    synthesizer: Synthesizer
    is_configured: ConfigCheck | None = None
    model: str | None = None
    output_extension: str = "mp3"
    content_type: str = "audio/mpeg"
    max_input_chars: int | None = None

    def resolve_voice(self, voice: str | None) -> str:
        if not voice:
            return self.default_voice
        normalized_voice = voice.strip()
        if normalized_voice in self.voices:
            return self.voices[normalized_voice]
        if normalized_voice in self.voices.values():
            return normalized_voice
        return self.default_voice


async def _synthesize_edge_tts_to_file(
    text: str,
    output_path: str,
    selection: TtsSelection,
    settings: Settings | None,
) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, selection.voice)
    await communicate.save(output_path)


def _openai_tts_configured(settings: Settings | None) -> bool:
    return bool(settings and settings.openai_tts_enabled)


async def _synthesize_openai_to_file(
    text: str,
    output_path: str,
    selection: TtsSelection,
    settings: Settings | None,
) -> None:
    from openai import AsyncOpenAI

    api_key = get_openai_api_key(settings)
    if not api_key:
        raise TtsProviderUnavailableError(f"{TtsVendor.OPENAI} TTS is not configured")

    async with AsyncOpenAI(api_key=api_key) as client:
        async with client.audio.speech.with_streaming_response.create(
            model=OPENAI_TTS_MODEL,
            voice=selection.voice,
            input=text,
            response_format="mp3",
        ) as response:
            await response.stream_to_file(output_path)


# Add another vendor here: register its synthesizer, voices, limits, and (when it needs
# credentials) an `is_configured` check. The API, repository, and processor stay on the same path.
TTS_PROVIDERS: dict[TtsVendor, TtsProvider] = {
    TtsVendor.EDGE_TTS: TtsProvider(
        vendor=TtsVendor.EDGE_TTS,
        default_voice=EDGE_TTS_VOICE,
        voices=EDGE_TTS_VOICES,
        synthesizer=_synthesize_edge_tts_to_file,
    ),
    TtsVendor.OPENAI: TtsProvider(
        vendor=TtsVendor.OPENAI,
        default_voice=OPENAI_TTS_VOICE,
        voices=OPENAI_TTS_VOICES,
        synthesizer=_synthesize_openai_to_file,
        is_configured=_openai_tts_configured,
        model=OPENAI_TTS_MODEL,
        max_input_chars=OPENAI_TTS_INPUT_MAX_CHARS,
    ),
}


def get_tts_provider(vendor: str | None) -> TtsProvider:
    normalized_vendor = (vendor or DEFAULT_TTS_VENDOR).strip().lower() or DEFAULT_TTS_VENDOR
    try:
        return TTS_PROVIDERS[TtsVendor(normalized_vendor)]
    except ValueError as exc:
        raise UnsupportedTtsVendorError(f"Unsupported TTS vendor: {normalized_vendor}") from exc


def resolve_tts_selection(vendor: str | None, voice: str | None) -> TtsSelection:
    provider = get_tts_provider(vendor)
    return TtsSelection(
        vendor=provider.vendor,
        voice=provider.resolve_voice(voice),
    )


def ensure_tts_provider_available(selection: TtsSelection, settings: Settings | None) -> None:
    provider = get_tts_provider(selection.vendor)
    if provider.is_configured and not provider.is_configured(settings):
        raise TtsProviderUnavailableError(f"{selection.vendor} TTS is not configured")


def tts_metadata(selection: TtsSelection) -> dict[str, object]:
    provider = get_tts_provider(selection.vendor)
    metadata = {
        "processor": provider.vendor,
        "voice": selection.voice,
    }
    return metadata | ({"model": provider.model} if provider.model else {})


def validate_tts_input(text: str, selection: TtsSelection) -> TtsProvider:
    provider = get_tts_provider(selection.vendor)
    if provider.max_input_chars is not None and len(text) > provider.max_input_chars:
        raise TtsInputTooLargeError(
            f"{selection.vendor} TTS input must be {provider.max_input_chars} characters or fewer"
        )
    return provider


# Cached for the container's lifetime: a rotated secret is only picked up once the Lambda
# execution environment recycles.
@lru_cache
def _get_secret_string(secret_id: str) -> str:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    try:
        response = boto3.client("secretsmanager").get_secret_value(SecretId=secret_id)
    except (BotoCoreError, ClientError) as exc:
        raise TtsConfigurationError("Failed to load OpenAI API key secret") from exc

    secret_string = response.get("SecretString")
    if secret_string:
        return str(secret_string)

    secret_binary = response.get("SecretBinary")
    if isinstance(secret_binary, bytes):
        return secret_binary.decode()
    if isinstance(secret_binary, str):
        return secret_binary
    raise TtsConfigurationError("OpenAI API key secret is empty")


def _extract_openai_api_key(secret: str) -> str:
    secret = secret.strip()
    if not secret:
        return ""
    try:
        payload = json.loads(secret)
    except json.JSONDecodeError:
        return secret
    if isinstance(payload, str):
        return payload.strip()
    if not isinstance(payload, dict):
        return ""
    for key in ("OPENAI_API_KEY", "openai_api_key", "api_key"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def get_openai_api_key(settings: Settings | None) -> str | None:
    if not settings:
        return None
    if api_key := (settings.openai_api_key or "").strip():
        return api_key
    if secret_id := (settings.openai_api_key_secret_arn or "").strip():
        return _extract_openai_api_key(_get_secret_string(secret_id)) or None
    return None


async def synthesize_to_file(
    text: str,
    output_path: str,
    selection: TtsSelection,
    settings: Settings | None = None,
) -> None:
    provider = validate_tts_input(text, selection)
    await provider.synthesizer(text, output_path, selection, settings)
