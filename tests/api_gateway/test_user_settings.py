import uuid
from collections.abc import Iterator

import httpx
import pytest


@pytest.fixture
def preserved_settings(api_client: httpx.Client) -> Iterator[dict]:
    response = api_client.get("/api/v1/settings")
    assert response.status_code == 200, response.text
    original = response.json()
    yield original

    original_payload = _settings_payload(original)
    current_response = api_client.get("/api/v1/settings")
    assert current_response.status_code == 200, current_response.text
    if _settings_payload(current_response.json()) == original_payload:
        return

    restore_response = api_client.put("/api/v1/settings", json=original_payload)
    assert restore_response.status_code == 200, restore_response.text


def test_user_settings_round_trip(
    api_client: httpx.Client,
    public_api_client: httpx.Client,
    preserved_settings: dict,
) -> None:
    unauthorized_get = public_api_client.get("/api/v1/settings")
    assert unauthorized_get.status_code == 401, unauthorized_get.text

    unauthorized_put = public_api_client.put("/api/v1/settings", json={})
    assert unauthorized_put.status_code == 401, unauthorized_put.text

    marker = f"API_TEST_{uuid.uuid4().hex[:8]}"
    settings_payload = _settings_payload(preserved_settings)
    settings_payload["custom_abbreviation_readings"] = [
        *settings_payload["custom_abbreviation_readings"],
        {"abbreviation": marker, "read_as": "test integracyjny"},
    ]

    put_response = api_client.put("/api/v1/settings", json=settings_payload)
    assert put_response.status_code == 200, put_response.text
    saved_settings = put_response.json()
    assert saved_settings["custom_abbreviation_readings"][-1] == {
        "abbreviation": marker,
        "read_as": "test integracyjny",
    }
    assert saved_settings["updated_at"]

    get_response = api_client.get("/api/v1/settings")
    assert get_response.status_code == 200, get_response.text
    assert get_response.json() == saved_settings


def _settings_payload(settings: dict) -> dict:
    return {key: value for key, value in settings.items() if key != "updated_at"}
