import os
import shutil
import subprocess
import warnings
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import quote

import httpx
import pytest
from dotenv import load_dotenv

from helpers import create_reading, wait_for_completed


REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(Path(__file__).with_name(".env"))

CLERK_API_URL = "https://api.clerk.com/v1"
DEFAULT_CLERK_JWT_TEMPLATE = "przeczytai-api"
DEFAULT_CLERK_JWT_EXPIRES_IN_SECONDS = 600


def _clerk_headers(secret_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
    }


def _clerk_error(action: str, response: httpx.Response) -> str:
    try:
        detail = response.json()
    except ValueError:
        detail = response.text
    return f"Clerk could not {action} ({response.status_code}): {detail}"


@pytest.fixture(scope="session")
def api_base_url() -> str:
    url = os.getenv("API_BASE_URL") or os.getenv("API_GATEWAY_BASE_URL")
    if url:
        return url.rstrip("/")

    if not shutil.which("terraform"):
        pytest.skip(
            "Set API_BASE_URL or install Terraform before running API Gateway tests."
        )

    tf_dir = REPO_ROOT / "infrastructure" / "environments" / "dev"
    result = subprocess.run(
        ["terraform", f"-chdir={tf_dir}", "output", "-raw", "api_base_url"],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        pytest.skip(
            "Set API_BASE_URL or deploy the dev Terraform stack before running these tests."
        )
    return result.stdout.strip().rstrip("/")


@pytest.fixture(scope="session")
def api_bearer_token() -> Iterator[str]:
    token = os.getenv("CLERK_JWT")
    if token:
        yield token
        return

    secret_key = os.getenv("CLERK_SECRET_KEY")
    test_user_id = os.getenv("CLERK_TEST_USER_ID")
    if not secret_key or not test_user_id:
        pytest.skip(
            "Set CLERK_SECRET_KEY and CLERK_TEST_USER_ID, or set CLERK_JWT, "
            "to run API Gateway tests against protected routes."
        )

    template = os.getenv("CLERK_JWT_TEMPLATE", DEFAULT_CLERK_JWT_TEMPLATE)
    expires_in_seconds = int(
        os.getenv(
            "CLERK_JWT_EXPIRES_IN_SECONDS",
            str(DEFAULT_CLERK_JWT_EXPIRES_IN_SECONDS),
        )
    )
    with httpx.Client(
        base_url=CLERK_API_URL,
        headers=_clerk_headers(secret_key),
        timeout=30.0,
    ) as client:
        response = client.post("/sessions", json={"user_id": test_user_id})
        if response.is_error:
            pytest.fail(_clerk_error("create a test session", response))
        session_id = response.json()["id"]

        try:
            response = client.post(
                f"/sessions/{session_id}/tokens/{quote(template, safe='')}",
                json={"expires_in_seconds": expires_in_seconds},
            )
            if response.is_error:
                pytest.fail(_clerk_error("create a test JWT", response))

            yield response.json()["jwt"]
        finally:
            revoke_response = client.post(f"/sessions/{session_id}/revoke")
            if revoke_response.is_error:
                warnings.warn(
                    _clerk_error(f"revoke test session {session_id}", revoke_response),
                    stacklevel=1,
                )


@pytest.fixture
def public_api_client(api_base_url: str) -> httpx.Client:
    with httpx.Client(base_url=api_base_url, timeout=60.0) as client:
        yield client


@pytest.fixture
def api_client(api_base_url: str, api_bearer_token: str) -> httpx.Client:
    with httpx.Client(
        base_url=api_base_url,
        headers={"Authorization": f"Bearer {api_bearer_token}"},
        timeout=60.0,
    ) as client:
        yield client


@pytest.fixture(scope="session")
def completed_reading(api_base_url: str, api_bearer_token: str) -> dict[str, Any]:
    with httpx.Client(
        base_url=api_base_url,
        headers={"Authorization": f"Bearer {api_bearer_token}"},
        timeout=60.0,
    ) as client:
        created = create_reading(client)
        completed = wait_for_completed(client, created["id"])
        completed["submitted_text"] = created["submitted_text"]
        return completed
