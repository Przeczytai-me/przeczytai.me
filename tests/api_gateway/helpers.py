import os
import time
import uuid
from typing import Any

import httpx
import pytest


DEFAULT_TEXT = "Ala ma kota."


def create_reading(
    client: httpx.Client,
    text: str | None = None,
    vendor: str | None = None,
    voice: str | None = None,
) -> dict[str, Any]:
    original_text = text or f"{DEFAULT_TEXT} api-gateway-{uuid.uuid4()}"
    payload = {"original_text": original_text}
    if vendor:
        payload["vendor"] = vendor
    if voice:
        payload["voice"] = voice
    response = client.post("/api/v1/readings", json=payload)
    assert response.status_code == 202, response.text
    data = response.json()
    data["submitted_text"] = original_text
    return data


def wait_for_completed(
    client: httpx.Client,
    reading_id: str,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    timeout = timeout_seconds or float(
        os.getenv("API_GATEWAY_PROCESSING_TIMEOUT_SECONDS", "120")
    )
    deadline = time.monotonic() + timeout
    last_payload: dict[str, Any] | None = None

    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/readings/{reading_id}")
        assert response.status_code == 200, response.text
        last_payload = response.json()
        status = last_payload["status"]
        if status == "completed":
            return last_payload
        if status == "failed_to_start":
            pytest.fail(f"Reading processing failed to start: {last_payload}")
        time.sleep(3)

    pytest.fail(
        f"Reading {reading_id} did not complete within {timeout} seconds: {last_payload}"
    )
