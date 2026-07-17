import asyncio

from fastapi.testclient import TestClient
from starlette.requests import Request

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.main import app
from app.repositories.readings import ProcessingStartError
from app.routes.readings import get_file_storage, get_reading_repository
from app.tts import DEFAULT_TTS_VENDOR, EDGE_TTS_VOICE, OPENAI_TTS_INPUT_MAX_CHARS

NOW = "2026-05-04T12:00:00Z"


class FakeRepo:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict] = {}
        self.deleted: list[tuple[str, str]] = []
        self.started: list[dict[str, str | None]] = []

    def create(
        self,
        owner_user_id: str,
        reading_id: str,
        original_text_key: str,
        char_count: int,
        vendor: str | None,
        voice: str | None,
    ) -> dict:
        item = {
            "reading_id": reading_id,
            "owner_user_id": owner_user_id,
            "original_text_key": original_text_key,
            "corrected_text_key": None,
            "recording_key": None,
            "vendor": vendor,
            "voice": voice,
            "status": "processing",
            "metadata": {},
            "char_count": char_count,
            "created_at": NOW,
            "updated_at": NOW,
        }
        self.items[(owner_user_id, reading_id)] = item
        return item

    def next_id(self) -> str:
        return f"id-{len(self.items) + 1}"

    def start_processing(
        self,
        owner_user_id: str,
        reading_id: str,
        original_text_key: str,
        vendor: str | None,
        voice: str | None,
    ) -> None:
        self.started.append(
            {
                "owner_user_id": owner_user_id,
                "reading_id": reading_id,
                "original_text_key": original_text_key,
                "vendor": vendor,
                "voice": voice,
            }
        )

    def mark_processing_start_failed(self, owner_user_id: str, reading_id: str) -> None:
        item = self.items[(owner_user_id, reading_id)]
        item["status"] = "failed_to_start"
        item["metadata"] = {"processing_start_error": "lambda_invoke_failed"}
        item["updated_at"] = NOW

    def list(
        self, owner_user_id: str, limit: int, cursor: str | None
    ) -> tuple[list[dict], str | None]:
        del cursor
        items = [item for (user_id, _), item in self.items.items() if user_id == owner_user_id]
        return items[:limit], None

    def get(self, owner_user_id: str, reading_id: str) -> dict | None:
        return self.items.get((owner_user_id, reading_id))

    def delete(self, owner_user_id: str, reading_id: str) -> None:
        self.deleted.append((owner_user_id, reading_id))
        self.items.pop((owner_user_id, reading_id), None)

    def mark_completed(
        self,
        owner_user_id: str,
        reading_id: str,
        corrected_text_key: str,
        recording_key: str,
        metadata: dict[str, object],
    ) -> None:
        item = self.items[(owner_user_id, reading_id)]
        item["corrected_text_key"] = corrected_text_key
        item["recording_key"] = recording_key
        item["metadata"] = metadata
        item["status"] = "completed"
        item["updated_at"] = NOW


class FailingProcessingRepo(FakeRepo):
    def start_processing(
        self,
        owner_user_id: str,
        reading_id: str,
        original_text_key: str,
        vendor: str | None,
        voice: str | None,
    ) -> None:
        del owner_user_id, reading_id, original_text_key, vendor, voice
        raise ProcessingStartError


class FakeStorage:
    def __init__(self) -> None:
        self.texts: dict[str, str] = {}

    def original_text_key(self, owner_user_id: str, reading_id: str) -> str:
        return f"users/{owner_user_id}/readings/{reading_id}/original.txt"

    def corrected_text_key(self, owner_user_id: str, reading_id: str) -> str:
        return f"users/{owner_user_id}/readings/{reading_id}/corrected.md"

    def recording_key(self, owner_user_id: str, reading_id: str) -> str:
        return f"users/{owner_user_id}/readings/{reading_id}/recording.mp3"

    def put_text(self, key: str, content: str, content_type: str) -> None:
        del content_type
        self.texts[key] = content

    def put_bytes(self, key: str, content: bytes, content_type: str) -> None:
        del content_type
        self.texts[key] = content.decode()

    def get_text(self, key: str) -> str:
        return self.texts[key]

    def download_url(self, key: str, filename: str) -> str:
        return f"https://files.example/{key}?filename={filename}"


def add_reading(
    repo: FakeRepo,
    owner_user_id: str,
    original_text: str = "hello",
    vendor: str | None = None,
    voice: str | None = None,
) -> dict:
    reading_id = repo.next_id()
    return repo.create(
        owner_user_id,
        reading_id,
        f"users/{owner_user_id}/readings/{reading_id}/original.txt",
        len(original_text),
        vendor,
        voice,
    )


def client(
    repo: FakeRepo | None = None,
    auth: bool = True,
    storage: FakeStorage | None = None,
    settings: Settings | None = None,
) -> tuple[TestClient, FakeRepo]:
    app.dependency_overrides.clear()
    repo = repo or FakeRepo()
    storage = storage or FakeStorage()
    settings = settings or Settings(max_text_chars=10)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_reading_repository] = lambda: repo
    app.dependency_overrides[get_file_storage] = lambda: storage
    if auth:
        app.dependency_overrides[get_current_user] = lambda: CurrentUser("user_1")
    return TestClient(app), repo


def test_health() -> None:
    """Return ok from the public health endpoint."""
    test_client, _ = client()
    assert test_client.get("/api/v1/health").json() == {"status": "ok"}


def test_docs_are_public() -> None:
    """Keep interactive docs public for browser access."""
    app.dependency_overrides.clear()
    test_client = TestClient(app)

    assert test_client.get("/docs").status_code == 200
    assert test_client.get("/redoc").status_code == 200
    assert test_client.get("/openapi.json").status_code == 200


def test_create_rejects_empty_original_text() -> None:
    """Reject reading creation when original text is blank."""
    test_client, _ = client()
    response = test_client.post("/api/v1/readings", json={"original_text": "   "})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_rejects_large_original_text() -> None:
    """Reject reading creation when original text exceeds the limit."""
    test_client, _ = client()
    response = test_client.post("/api/v1/readings", json={"original_text": "x" * 11})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_create_and_get_reading() -> None:
    """Create a reading and fetch it by id."""
    storage = FakeStorage()
    test_client, _ = client(storage=storage)
    response = test_client.post(
        "/api/v1/readings",
        json={"original_text": "hello", "voice": "Ola"},
    )
    assert response.status_code == 202
    created = response.json()

    assert created["original_text_key"] == "users/user_1/readings/id-1/original.txt"
    assert created["corrected_text_key"] is None
    assert created["recording_key"] is None
    assert created["vendor"] == DEFAULT_TTS_VENDOR
    assert created["voice"] == EDGE_TTS_VOICE
    assert created["status"] == "processing"
    assert created["char_count"] == 5
    assert storage.texts[created["original_text_key"]] == "hello"

    detail = test_client.get(f"/api/v1/readings/{created['id']}").json()
    assert detail["original_text_key"] == created["original_text_key"]


def test_create_uses_requested_supported_voice() -> None:
    """Use a requested Edge TTS voice when it is supported."""
    test_client, repo = client()

    response = test_client.post(
        "/api/v1/readings",
        json={"original_text": "hello", "voice": "Marek"},
    )

    assert response.status_code == 202
    assert response.json()["voice"] == "pl-PL-MarekNeural"
    assert repo.started[0]["vendor"] == DEFAULT_TTS_VENDOR
    assert repo.started[0]["voice"] == "pl-PL-MarekNeural"


def test_create_uses_requested_openai_vendor() -> None:
    """Store and start processing with the requested OpenAI TTS provider."""
    test_client, repo = client(settings=Settings(max_text_chars=5000, openai_tts_enabled=True))

    response = test_client.post(
        "/api/v1/readings",
        json={"original_text": "hello", "vendor": "openai", "voice": "coral"},
    )

    assert response.status_code == 202
    created = response.json()
    assert created["vendor"] == "openai"
    assert created["voice"] == "coral"
    assert repo.started[0]["vendor"] == "openai"
    assert repo.started[0]["voice"] == "coral"


def test_create_rejects_openai_when_provider_is_not_configured() -> None:
    """Reject OpenAI TTS requests before creating a reading if credentials are absent."""
    test_client, _ = client(settings=Settings(max_text_chars=5000, openai_tts_enabled=False))

    response = test_client.post(
        "/api/v1/readings",
        json={"original_text": "hello", "vendor": "openai", "voice": "coral"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "provider_unavailable"


def test_create_rejects_unsupported_vendor() -> None:
    """Reject unknown vendors instead of silently switching providers."""
    test_client, _ = client()

    response = test_client.post(
        "/api/v1/readings",
        json={"original_text": "hello", "vendor": "aws-polly"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_create_rejects_openai_text_over_vendor_limit() -> None:
    """Reject OpenAI TTS requests that exceed the Speech API input limit."""
    original_text = "x" * (OPENAI_TTS_INPUT_MAX_CHARS + 1)
    test_client, _ = client(
        settings=Settings(max_text_chars=len(original_text) + 1, openai_tts_enabled=True)
    )

    response = test_client.post(
        "/api/v1/readings",
        json={"original_text": original_text, "vendor": "openai"},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_create_returns_500_when_processing_start_fails() -> None:
    """Return a processing error when async startup fails."""
    repo = FailingProcessingRepo()
    test_client, _ = client(repo)

    response = test_client.post("/api/v1/readings", json={"original_text": "hello"})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "processing_start_failed"
    assert repo.get("user_1", "id-1")["status"] == "failed_to_start"


def test_list_is_user_scoped() -> None:
    """List only readings owned by the authenticated user."""
    repo = FakeRepo()
    add_reading(repo, "user_1", "mine")
    add_reading(repo, "user_2", "other")
    test_client, _ = client(repo)

    response = test_client.get("/api/v1/readings").json()
    assert [item["id"] for item in response["items"]] == ["id-1"]


def test_list_skips_malformed_reading_items() -> None:
    """Skip partial rows left by asynchronous processing races."""
    repo = FakeRepo()
    add_reading(repo, "user_1", "mine")
    repo.items[("user_1", "bad")] = {
        "pk": "USER#user_1",
        "sk": "READING#bad",
        "status": "completed",
    }
    test_client, _ = client(repo)

    response = test_client.get("/api/v1/readings")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == ["id-1"]


def test_get_missing_returns_404() -> None:
    """Return not found for a missing reading id."""
    test_client, _ = client()
    response = test_client.get("/api/v1/readings/missing")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_get_other_user_item_returns_404() -> None:
    """Hide readings owned by another user."""
    repo = FakeRepo()
    item = add_reading(repo, "user_2", "other")
    test_client, _ = client(repo)

    response = test_client.get(f"/api/v1/readings/{item['reading_id']}")
    assert response.status_code == 404


def test_delete_reading() -> None:
    """Delete a reading owned by the authenticated user."""
    repo = FakeRepo()
    item = add_reading(repo, "user_1")
    test_client, _ = client(repo)

    response = test_client.delete(f"/api/v1/readings/{item['reading_id']}")
    assert response.status_code == 204
    assert repo.get("user_1", item["reading_id"]) is None


def test_download_corrected_text() -> None:
    """Download corrected text as a markdown attachment."""
    repo = FakeRepo()
    storage = FakeStorage()
    item = add_reading(repo, "user_1")
    item["corrected_text_key"] = storage.corrected_text_key("user_1", item["reading_id"])
    storage.texts[item["corrected_text_key"]] = "# Hello\n"
    test_client, _ = client(repo, storage=storage)

    response = test_client.get(f"/api/v1/readings/{item['reading_id']}/corrected-text.md")

    assert response.status_code == 200
    assert response.text == "# Hello\n"
    assert response.headers["content-type"].startswith("text/markdown")
    assert (
        response.headers["content-disposition"] == f'attachment; filename="{item["reading_id"]}.md"'
    )


def test_download_corrected_text_missing_returns_404() -> None:
    """Return not found before corrected text is ready."""
    repo = FakeRepo()
    item = add_reading(repo, "user_1")
    test_client, _ = client(repo)

    response = test_client.get(f"/api/v1/readings/{item['reading_id']}/corrected-text.md")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_download_recording() -> None:
    """Redirect to a temporary recording download URL."""
    repo = FakeRepo()
    storage = FakeStorage()
    item = add_reading(repo, "user_1")
    item["recording_key"] = storage.recording_key("user_1", item["reading_id"])
    test_client, _ = client(repo, storage=storage)

    response = test_client.get(
        f"/api/v1/readings/{item['reading_id']}/recording",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == (
        "https://files.example/"
        f"users/user_1/readings/{item['reading_id']}/recording.mp3"
        f"?filename={item['reading_id']}-recording.mp3"
    )


def test_download_recording_uses_stored_extension() -> None:
    """Name the download after the stored recording, not a hardcoded .mp3."""
    repo = FakeRepo()
    storage = FakeStorage()
    item = add_reading(repo, "user_1")
    item["recording_key"] = f"users/user_1/readings/{item['reading_id']}/recording.wav"
    test_client, _ = client(repo, storage=storage)

    response = test_client.get(
        f"/api/v1/readings/{item['reading_id']}/recording",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"].endswith(f"?filename={item['reading_id']}-recording.wav")


def test_download_recording_missing_returns_404() -> None:
    """Return not found before recording output is ready."""
    repo = FakeRepo()
    item = add_reading(repo, "user_1")
    test_client, _ = client(repo)

    response = test_client.get(f"/api/v1/readings/{item['reading_id']}/recording")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_missing_jwt_returns_401() -> None:
    """Reject protected endpoints without JWT claims."""
    test_client, _ = client(auth=False)
    response = test_client.get("/api/v1/readings")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_auth_reads_api_gateway_jwt_claims() -> None:
    """Read the current user id from API Gateway JWT claims."""
    request = Request(
        {
            "type": "http",
            "headers": [],
            "aws.event": {
                "requestContext": {
                    "authorizer": {
                        "jwt": {
                            "claims": {
                                "sub": "user_gateway",
                            }
                        }
                    }
                }
            },
        }
    )

    user = asyncio.run(get_current_user(request))
    assert user.user_id == "user_gateway"
