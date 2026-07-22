import re

from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.models import TtsOptionsResponse, TtsVendorOptions, TtsVoiceOption
from app.tts import DEFAULT_TTS_VENDOR, TTS_PROVIDERS, TtsProvider, TtsVendor

router = APIRouter(prefix="/api/v1/tts-options", tags=["tts-options"])
VENDOR_LABELS = {
    TtsVendor.EDGE_TTS: "Edge TTS",
    TtsVendor.OPENAI: "OpenAI",
}


def _voice_option(voice_id: str, provider_voice: str) -> TtsVoiceOption:
    match = re.match(r"^([a-z]{2}-[A-Z]{2})-", provider_voice)
    return TtsVoiceOption(
        id=voice_id,
        label=voice_id.capitalize(),
        provider_voice=provider_voice,
        language=match.group(1) if match else None,
        preview_url=None,
    )


def _vendor_options(provider: TtsProvider) -> TtsVendorOptions:
    return TtsVendorOptions(
        id=provider.vendor,
        label=VENDOR_LABELS[provider.vendor],
        model=provider.model,
        default_voice=next(
            voice_id
            for voice_id, provider_voice in provider.voices.items()
            if provider_voice == provider.default_voice
        ),
        voices=[_voice_option(*voice) for voice in provider.voices.items()],
    )


@router.get("", response_model=TtsOptionsResponse)
async def get_tts_options(
    _: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> TtsOptionsResponse:
    providers = [
        provider
        for provider in TTS_PROVIDERS.values()
        if not provider.is_configured or provider.is_configured(settings)
    ]
    return TtsOptionsResponse(
        default_vendor=DEFAULT_TTS_VENDOR,
        vendors=[_vendor_options(provider) for provider in providers],
    )
