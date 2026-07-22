from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.errors import ApiException
from app.models import (
    DEFAULT_USER_SETTINGS,
    UserSettings,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from app.repositories.user_settings import UserSettingsRepository
from app.tts import TTS_PROVIDERS, get_tts_provider

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


def get_user_settings_repository(
    settings: Settings = Depends(get_settings),
) -> UserSettingsRepository:
    return UserSettingsRepository(settings.readings_table_name)


def _response(overrides: dict) -> UserSettingsResponse:
    effective = DEFAULT_USER_SETTINGS | {
        key: value for key, value in overrides.items() if key in DEFAULT_USER_SETTINGS
    }
    return UserSettingsResponse(
        settings=UserSettings(**effective),
        defaults=UserSettings(**DEFAULT_USER_SETTINGS),
    )


def _validation_error() -> ApiException:
    return ApiException("validation_error", "Invalid request", 422)


def _validated_overrides(update: UserSettingsUpdate) -> dict:
    overrides = update.model_dump(exclude_none=True)
    if update.tts_vendor is not None and update.tts_vendor not in TTS_PROVIDERS:
        raise _validation_error()
    if update.tts_voice is not None:
        voices = get_tts_provider(update.tts_vendor).voices
        if update.tts_voice not in voices and update.tts_voice not in voices.values():
            raise _validation_error()
    if update.playback_speed is not None and not 0.5 <= update.playback_speed <= 2.0:
        raise _validation_error()
    if update.export_format is not None and update.export_format != "mp3":
        raise _validation_error()
    if update.pronunciation_style is not None and len(update.pronunciation_style) > 120:
        raise _validation_error()

    readings = update.abbreviation_readings
    if readings is not None:
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
        overrides["abbreviation_readings"] = normalized
    return overrides


@router.get("", response_model=UserSettingsResponse)
async def get_user_settings(
    user: CurrentUser = Depends(get_current_user),
    repo: UserSettingsRepository = Depends(get_user_settings_repository),
) -> UserSettingsResponse:
    overrides = repo.get(user.user_id) or {}
    return _response(overrides)


@router.put("", response_model=UserSettingsResponse)
async def put_user_settings(
    update: UserSettingsUpdate,
    user: CurrentUser = Depends(get_current_user),
    repo: UserSettingsRepository = Depends(get_user_settings_repository),
) -> UserSettingsResponse:
    overrides = _validated_overrides(update)
    repo.put(user.user_id, overrides)
    return _response(overrides)
