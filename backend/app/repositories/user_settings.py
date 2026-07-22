from datetime import UTC, datetime

import boto3


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class UserSettingsRepository:
    def __init__(self, table_name: str) -> None:
        self.table = boto3.resource("dynamodb").Table(table_name)

    def get(self, owner_user_id: str) -> dict | None:
        response = self.table.get_item(
            Key={"pk": f"USER#{owner_user_id}", "sk": "SETTINGS"}
        )
        return response.get("Item", {}).get("settings")

    def put(self, owner_user_id: str, settings: dict) -> str:
        now = _now()
        self.table.update_item(
            Key={"pk": f"USER#{owner_user_id}", "sk": "SETTINGS"},
            UpdateExpression=(
                "SET settings = :settings, created_at = if_not_exists(created_at, :now), "
                "updated_at = :now"
            ),
            ExpressionAttributeValues={
                ":settings": settings | {"updated_at": now},
                ":now": now,
            },
        )
        return now
