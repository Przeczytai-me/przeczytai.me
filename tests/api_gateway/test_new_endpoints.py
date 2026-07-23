import uuid
from collections.abc import Iterator
from pathlib import Path
from time import monotonic, sleep

import httpx
import pytest
from mutagen.mp3 import MP3

from helpers import wait_for_completed


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIO_DOWNLOAD_DIR = REPO_ROOT / "tested_assets" / "api_gateway"


@pytest.fixture
def preserved_settings(api_client: httpx.Client) -> Iterator[dict]:
    response = api_client.get("/api/v1/settings")
    assert response.status_code == 200, response.text
    original = response.json()
    yield original

    restore_payload = {
        key: value for key, value in original.items() if key != "updated_at"
    }
    restore_response = api_client.put("/api/v1/settings", json=restore_payload)
    assert restore_response.status_code == 200, restore_response.text


@pytest.fixture
def readings_to_delete(api_client: httpx.Client) -> Iterator[list[str]]:
    reading_ids: list[str] = []
    yield reading_ids

    for reading_id in reading_ids:
        response = api_client.delete(f"/api/v1/readings/{reading_id}")
        assert response.status_code in {204, 404}, response.text


def test_top_level_endpoints_against_deployed_api(
    api_client: httpx.Client,
    public_api_client: httpx.Client,
    preserved_settings: dict,
) -> None:
    protected_requests = [
        ("GET", "/api/v1/tts-options"),
        ("GET", "/api/v1/jobs"),
        ("GET", "/api/v1/settings"),
        ("PUT", "/api/v1/settings"),
    ]
    for method, path in protected_requests:
        response = public_api_client.request(
            method, path, json={} if method == "PUT" else None
        )
        assert response.status_code == 401, (
            f"{method} {path} should require authentication: "
            f"{response.status_code} {response.text}"
        )

    options_response = api_client.get("/api/v1/tts-options")
    assert options_response.status_code == 200, options_response.text
    options = options_response.json()
    assert options["vendors"]
    assert options["models"]
    assert options["voices"]
    assert options["defaults"]["model"]
    assert options["defaults"]["voice"]

    jobs_response = api_client.get("/api/v1/jobs", params={"limit": 20})
    assert jobs_response.status_code == 200, jobs_response.text
    jobs = jobs_response.json()
    assert isinstance(jobs["items"], list)
    assert "next_cursor" in jobs

    marker = f"API_TEST_{uuid.uuid4().hex[:8]}"
    settings_payload = {
        key: value for key, value in preserved_settings.items() if key != "updated_at"
    }
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


def test_reading_endpoints_and_audio_against_deployed_api(
    api_client: httpx.Client,
    readings_to_delete: list[str],
) -> None:
    unique_suffix = uuid.uuid4().hex
    original_text = f"Integracyjny test PKP. {unique_suffix}"
    expected_corrected_text = f"Integracyjny test Pe Ka Pe. {unique_suffix}"
    create_response = api_client.post(
        "/api/v1/readings",
        json={
            "original_text": original_text,
            "abbreviation_readings": [
                {"abbreviation": "PKP", "read_as": "Pe Ka Pe"},
            ],
        },
    )
    assert create_response.status_code == 202, create_response.text
    created = create_response.json()
    reading_id = created["id"]
    readings_to_delete.append(reading_id)
    assert created["status"] == "uploaded"

    original_response = api_client.get(f"/api/v1/readings/{reading_id}/original-text")
    assert original_response.status_code == 200, original_response.text
    assert original_response.text == original_text
    assert original_response.headers["content-type"].startswith("text/plain")
    assert (
        f'filename="{reading_id}.txt"'
        in original_response.headers["content-disposition"]
    )

    initial_jobs_response = api_client.get("/api/v1/jobs", params={"limit": 50})
    assert initial_jobs_response.status_code == 200, initial_jobs_response.text
    initial_job = _find_job(
        initial_jobs_response.json()["items"], reading_id, attempt=1
    )
    assert initial_job["error"] is None

    completed = wait_for_completed(api_client, reading_id)
    assert completed["status"] == "completed"

    corrected_response = api_client.get(
        f"/api/v1/readings/{reading_id}/corrected-text.md"
    )
    assert corrected_response.status_code == 200, corrected_response.text
    assert corrected_response.text == expected_corrected_text

    timing_response = api_client.get(f"/api/v1/readings/{reading_id}/timing-map")
    assert timing_response.status_code == 200, timing_response.text
    timing_map = timing_response.json()
    assert timing_map["reading_id"] == reading_id
    assert timing_map["duration_ms"] > 0
    assert timing_map["segments"]
    assert timing_map["segments"][0]["start_ms"] == 0
    assert timing_map["segments"][-1]["end_ms"] == timing_map["duration_ms"]

    audio_path = _download_recording(api_client, reading_id)
    assert audio_path.parent == AUDIO_DOWNLOAD_DIR
    assert audio_path.is_file()
    assert audio_path.stat().st_size > 0
    assert MP3(audio_path).info.length > 0

    retry_response = api_client.post(f"/api/v1/readings/{reading_id}/retry")
    assert retry_response.status_code == 202, retry_response.text
    retry_job = retry_response.json()
    assert retry_job["reading_id"] == reading_id
    assert retry_job["attempt"] == 2
    assert retry_job["status"] == "uploaded"
    assert retry_job["error"] is None

    retried = wait_for_completed(api_client, reading_id)
    assert retried["status"] == "completed"

    listed_retry = _wait_for_job_status(
        api_client,
        reading_id,
        attempt=2,
        expected_status="ready",
    )
    assert listed_retry["id"] == retry_job["id"]


def _find_job(items: list[dict], reading_id: str, attempt: int) -> dict:
    matching = [
        item
        for item in items
        if item["reading_id"] == reading_id and item["attempt"] == attempt
    ]
    assert len(matching) == 1, (
        f"Expected one job for reading={reading_id} attempt={attempt}, got {matching}"
    )
    return matching[0]


def _wait_for_job_status(
    api_client: httpx.Client,
    reading_id: str,
    *,
    attempt: int,
    expected_status: str,
    timeout_seconds: float = 30.0,
) -> dict:
    deadline = monotonic() + timeout_seconds
    last_job: dict | None = None
    while monotonic() < deadline:
        response = api_client.get("/api/v1/jobs", params={"limit": 50})
        assert response.status_code == 200, response.text
        last_job = _find_job(response.json()["items"], reading_id, attempt)
        if last_job["status"] == expected_status:
            return last_job
        if last_job["status"] == "failed":
            pytest.fail(f"Job failed while waiting for {expected_status}: {last_job}")
        sleep(1)

    pytest.fail(
        f"Job did not reach {expected_status} within {timeout_seconds}s: {last_job}"
    )


def _download_recording(api_client: httpx.Client, reading_id: str) -> Path:
    redirect_response = api_client.get(
        f"/api/v1/readings/{reading_id}/recording",
        follow_redirects=False,
    )
    assert redirect_response.status_code == 307, redirect_response.text
    assert "location" in redirect_response.headers

    download_response = httpx.get(
        redirect_response.headers["location"],
        follow_redirects=True,
        timeout=60.0,
    )
    assert download_response.status_code == 200, download_response.text
    assert download_response.headers["content-type"].startswith("audio/")
    assert download_response.content

    AUDIO_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = AUDIO_DOWNLOAD_DIR / f"{reading_id}-recording.mp3"
    audio_path.write_bytes(download_response.content)
    return audio_path
