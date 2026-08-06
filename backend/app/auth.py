from fastapi import Depends, Request

from app.config import Settings, get_settings
from app.errors import ApiException


class CurrentUser:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id


async def get_current_user(
    request: Request,
) -> CurrentUser:
    event = request.scope.get("aws.event") or {}
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    user_id = claims.get("sub")
    if isinstance(user_id, str) and user_id:
        return CurrentUser(user_id)
    raise ApiException("unauthorized", "Missing API Gateway JWT claims", 401)


async def require_admin(
    user: CurrentUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    admin_user_ids = {
        user_id.strip() for user_id in settings.admin_user_ids.split(",") if user_id.strip()
    }
    if user.user_id not in admin_user_ids:
        raise ApiException("forbidden", "Admin access required", 403)
    return user
