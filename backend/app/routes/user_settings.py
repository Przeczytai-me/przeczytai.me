from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.errors import ApiException
from app.models import (
    DEFAULT_USER_SETTINGS,
    PRONUNCIATION_STYLES,
    UserSettings,
    UserSettingsUpdate,
)
from app.repositories.user_settings import UserSettingsRepository
from app.routes.tts_options import configured_providers

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


def get_user_settings_repository(
    settings: Settings = Depends(get_settings),
) -> UserSettingsRepository:
    return UserSettingsRepository(settings.readings_table_name)


def _response(overrides: dict) -> UserSettings:
    effective = DEFAULT_USER_SETTINGS | {
        key: value for key, value in overrides.items() if key in DEFAULT_USER_SETTINGS
    }
    if isinstance(effective["exports"], dict):
        effective["exports"] = DEFAULT_USER_SETTINGS["exports"] | effective["exports"]
    return UserSettings(**effective)


def _validation_error() -> ApiException:
    return ApiException("validation_error", "Invalid request", 422)


def _validated_settings(update: UserSettingsUpdate, settings: Settings) -> dict:
    validated = update.model_dump()
    providers_by_model = {
        str(provider.model or provider.vendor): provider
        for provider in configured_providers(settings)
    }
    if update.reading_model not in providers_by_model:
        raise _validation_error()
    if update.fallback_model is not None and update.fallback_model not in providers_by_model:
        raise _validation_error()
    voices = providers_by_model[update.reading_model].voices
    if update.voice in voices:
        validated["voice"] = update.voice
    elif update.voice in voices.values():
        validated["voice"] = next(
            voice_id for voice_id, provider_id in voices.items() if provider_id == update.voice
        )
    else:
        raise _validation_error()
    if update.pronunciation_style not in {style["id"] for style in PRONUNCIATION_STYLES}:
        raise _validation_error()
    if not 0.5 <= update.playback_speed <= 2.0:
        raise _validation_error()

    filename_pattern = update.exports.filename_pattern.strip()
    if (
        not filename_pattern
        or len(filename_pattern) > 120
        or update.exports.mp3_quality != "standard"
        or update.exports.text_format not in {"md", "txt"}
    ):
        raise _validation_error()
    validated["exports"]["filename_pattern"] = filename_pattern

    readings = update.custom_abbreviation_readings
    if len(readings) > 100:
        raise _validation_error()
    normalized = []
    abbreviations = set()
    for reading in readings:
        abbreviation = reading.abbreviation.strip()
        read_as = reading.read_as.strip()
        normalized_abbreviation = abbreviation.casefold()
        if (
            not abbreviation
            or not read_as
            or len(abbreviation) > 50
            or len(read_as) > 200
            or normalized_abbreviation in abbreviations
        ):
            raise _validation_error()
        abbreviations.add(normalized_abbreviation)
        normalized.append({"abbreviation": abbreviation, "read_as": read_as})
    validated["custom_abbreviation_readings"] = normalized
    return validated


@router.get("", response_model=UserSettings)
async def get_user_settings(
    user: CurrentUser = Depends(get_current_user),
    repo: UserSettingsRepository = Depends(get_user_settings_repository),
) -> UserSettings:
    overrides = repo.get(user.user_id) or {}
    return _response(overrides)


@router.put("", response_model=UserSettings)
async def put_user_settings(
    update: UserSettingsUpdate,
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    repo: UserSettingsRepository = Depends(get_user_settings_repository),
) -> UserSettings:
    validated = _validated_settings(update, settings)
    updated_at = repo.put(user.user_id, validated)
    return _response(validated | {"updated_at": updated_at})
