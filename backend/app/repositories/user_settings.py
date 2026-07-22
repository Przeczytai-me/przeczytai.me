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

    def put(self, owner_user_id: str, overrides: dict) -> None:
        now = _now()
        self.table.put_item(
            Item={
                "pk": f"USER#{owner_user_id}",
                "sk": "SETTINGS",
                "settings": overrides,
                "created_at": now,
                "updated_at": now,
            }
        )
