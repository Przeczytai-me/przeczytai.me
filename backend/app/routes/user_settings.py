from fastapi import APIRouter, Depends

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.models import DEFAULT_USER_SETTINGS, UserSettings, UserSettingsResponse
from app.repositories.user_settings import UserSettingsRepository

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


def get_user_settings_repository(
    settings: Settings = Depends(get_settings),
) -> UserSettingsRepository:
    return UserSettingsRepository(settings.readings_table_name)


@router.get("", response_model=UserSettingsResponse)
async def get_user_settings(
    user: CurrentUser = Depends(get_current_user),
    repo: UserSettingsRepository = Depends(get_user_settings_repository),
) -> UserSettingsResponse:
    overrides = repo.get(user.user_id) or {}
    effective = DEFAULT_USER_SETTINGS | {
        key: value for key, value in overrides.items() if key in DEFAULT_USER_SETTINGS
    }
    return UserSettingsResponse(
        settings=UserSettings(**effective),
        defaults=UserSettings(**DEFAULT_USER_SETTINGS),
    )
