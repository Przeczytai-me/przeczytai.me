import re

from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.models import (
    PRONUNCIATION_STYLES,
    TtsDefaults,
    TtsModelOption,
    TtsOptionsResponse,
    TtsVendorOption,
    TtsVoiceOption,
)
from app.tts import TTS_PROVIDERS, TtsProvider, TtsVendor

router = APIRouter(prefix="/api/v1/tts-options", tags=["tts-options"])
VENDOR_LABELS = {
    TtsVendor.EDGE_TTS: "Edge TTS",
    TtsVendor.OPENAI: "OpenAI",
}


def _voice_option(voice_id: str, provider_id: str) -> TtsVoiceOption:
    if "Multilingual" in provider_id:
        language = "multilingual"
    else:
        match = re.match(r"^([a-z]{2}-[A-Z]{2})-", provider_id)
        language = match.group(1) if match else "multilingual"
    return TtsVoiceOption(
        id=voice_id,
        provider_id=provider_id,
        label=voice_id.capitalize(),
        language=language,
        preview_url=None,
    )


def configured_providers(settings: Settings) -> list[TtsProvider]:
    return [
        provider
        for provider in TTS_PROVIDERS.values()
        if not provider.is_configured or provider.is_configured(settings)
    ]


@router.get("", response_model=TtsOptionsResponse)
async def get_tts_options(
    _: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> TtsOptionsResponse:
    providers = configured_providers(settings)
    return TtsOptionsResponse(
        vendors=[
            TtsVendorOption(id=provider.vendor, label=VENDOR_LABELS[provider.vendor])
            for provider in providers
        ],
        models=[
            TtsModelOption(
                id=provider.model or provider.vendor,
                vendor_id=provider.vendor,
                label="OpenAI TTS" if provider.vendor == TtsVendor.OPENAI else "Edge TTS",
            )
            for provider in providers
        ],
        voices=[
            _voice_option(voice_id, provider_id)
            for provider in providers
            for voice_id, provider_id in provider.voices.items()
        ],
        pronunciation_styles=PRONUNCIATION_STYLES,
        defaults=TtsDefaults(
            model="edge-tts",
            voice="Zofia",
            pronunciation_style="natural",
        ),
    )
