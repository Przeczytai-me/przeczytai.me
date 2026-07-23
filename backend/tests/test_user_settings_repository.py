from decimal import Decimal

import pytest

from app.repositories import user_settings
from app.repositories.user_settings import UserSettingsRepository


NOW = "2026-07-23T12:34:56Z"


class RecordingTable:
    def __init__(self) -> None:
        self.update_calls: list[dict] = []

    def update_item(self, **kwargs: object) -> None:
        self.update_calls.append(kwargs)


class FakeDynamoResource:
    def __init__(self, table: RecordingTable) -> None:
        self.table = table

    def Table(self, _table_name: str) -> RecordingTable:
        return self.table


def test_put_serializes_floats_and_aliases_settings_attribute(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    table = RecordingTable()
    monkeypatch.setattr(
        user_settings.boto3,
        "resource",
        lambda _service: FakeDynamoResource(table),
    )
    monkeypatch.setattr(user_settings, "_now", lambda: NOW)
    settings = {
        "playback_speed": 1.25,
        "nested": {"values": [0.5, 2.0]},
    }

    updated_at = UserSettingsRepository("table").put("user-1", settings)

    assert updated_at == NOW
    assert settings == {
        "playback_speed": 1.25,
        "nested": {"values": [0.5, 2.0]},
    }
    assert table.update_calls == [
        {
            "Key": {"pk": "USER#user-1", "sk": "SETTINGS"},
            "UpdateExpression": (
                "SET #settings = :settings, "
                "created_at = if_not_exists(created_at, :now), "
                "updated_at = :now"
            ),
            "ExpressionAttributeNames": {"#settings": "settings"},
            "ExpressionAttributeValues": {
                ":settings": {
                    "playback_speed": Decimal("1.25"),
                    "nested": {
                        "values": [
                            Decimal("0.5"),
                            Decimal("2.0"),
                        ]
                    },
                    "updated_at": NOW,
                },
                ":now": NOW,
            },
        }
    ]
