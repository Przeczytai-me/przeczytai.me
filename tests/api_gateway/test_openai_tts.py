import os

import httpx
import pytest

from helpers import create_reading, wait_for_completed


@pytest.mark.skipif(
    os.getenv("RUN_OPENAI_CLOUD_TTS_TESTS") != "1",
    reason="Set RUN_OPENAI_CLOUD_TTS_TESTS=1 to run the paid OpenAI TTS cloud test.",
)
def test_openai_tts_cloud_processing(api_client: httpx.Client) -> None:
    created = create_reading(
        api_client,
        "Ala ma kota.",
        vendor="openai",
        voice="coral",
    )

    assert created["vendor"] == "openai"
    assert created["voice"] == "coral"

    completed = wait_for_completed(api_client, created["id"])
    assert completed["metadata"]["processor"] == "openai"
    assert completed["metadata"]["voice"] == "coral"
    assert completed["metadata"]["model"] == "gpt-4o-mini-tts"

    response = api_client.get(
        f"/api/v1/readings/{created['id']}/recording",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")
    assert response.content
