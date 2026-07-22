from app.storage import StorageError, StorageObjectNotFoundError
from test_api import FakeRepo, FakeStorage, add_reading, client


class MissingObjectStorage(FakeStorage):
    def get_text(self, key: str) -> str:
        raise StorageObjectNotFoundError(key)


class FailingStorage(FakeStorage):
    def get_text(self, key: str) -> str:
        raise StorageError(key)


def test_download_original_text() -> None:
    """Download original text as a plain-text attachment."""
    repo = FakeRepo()
    storage = FakeStorage()
    item = add_reading(repo, "user_1")
    storage.texts[item["original_text_key"]] = "Zażółć gęślą jaźń.\n"
    test_client, _ = client(repo, storage=storage)

    response = test_client.get(f"/api/v1/readings/{item['reading_id']}/original-text")

    assert response.status_code == 200
    assert response.text == "Zażółć gęślą jaźń.\n"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.headers["content-disposition"] == (
        f'attachment; filename="{item["reading_id"]}.txt"'
    )


def test_download_original_text_as_markdown() -> None:
    """Use markdown media type and suffix for a stored markdown source."""
    repo = FakeRepo()
    storage = FakeStorage()
    item = add_reading(repo, "user_1")
    item["original_text_key"] = f"users/user_1/readings/{item['reading_id']}/original.md"
    storage.texts[item["original_text_key"]] = "# Tytuł\n"
    test_client, _ = client(repo, storage=storage)

    response = test_client.get(f"/api/v1/readings/{item['reading_id']}/original-text")

    assert response.status_code == 200
    assert response.text == "# Tytuł\n"
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    assert response.headers["content-disposition"] == (
        f'attachment; filename="{item["reading_id"]}.md"'
    )


def test_download_original_text_defaults_to_txt_suffix() -> None:
    """Default the attachment suffix to txt when the stored key has none."""
    repo = FakeRepo()
    storage = FakeStorage()
    item = add_reading(repo, "user_1")
    item["original_text_key"] = f"users/user_1/readings/{item['reading_id']}/original"
    storage.texts[item["original_text_key"]] = "Tekst"
    test_client, _ = client(repo, storage=storage)

    response = test_client.get(f"/api/v1/readings/{item['reading_id']}/original-text")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert response.headers["content-disposition"] == (
        f'attachment; filename="{item["reading_id"]}.txt"'
    )


def test_download_original_text_for_other_user_returns_404() -> None:
    """Hide original text owned by another user."""
    repo = FakeRepo()
    item = add_reading(repo, "user_2")
    test_client, _ = client(repo)

    response = test_client.get(f"/api/v1/readings/{item['reading_id']}/original-text")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Reading not found"}
    }


def test_download_original_text_for_missing_reading_returns_404() -> None:
    """Return not found when the reading does not exist."""
    test_client, _ = client()

    response = test_client.get("/api/v1/readings/missing/original-text")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Reading not found"}
    }


def test_download_original_text_for_missing_object_returns_404() -> None:
    """Return not found when the reading's source object is missing."""
    repo = FakeRepo()
    item = add_reading(repo, "user_1")
    test_client, _ = client(repo, storage=MissingObjectStorage())

    response = test_client.get(f"/api/v1/readings/{item['reading_id']}/original-text")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Original text not found"}
    }


def test_download_original_text_storage_failure_returns_500() -> None:
    """Return a safe storage error when loading original text fails."""
    repo = FakeRepo()
    item = add_reading(repo, "user_1")
    test_client, _ = client(repo, storage=FailingStorage())

    response = test_client.get(f"/api/v1/readings/{item['reading_id']}/original-text")

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "storage_error", "message": "Failed to load original text"}
    }
    assert item["original_text_key"] not in response.text


def test_download_original_text_requires_authentication() -> None:
    """Reject original-text downloads without JWT claims."""
    test_client, _ = client(auth=False)

    response = test_client.get("/api/v1/readings/missing/original-text")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_original_text_endpoint_appears_in_openapi() -> None:
    """Publish the original-text endpoint in the OpenAPI schema."""
    test_client, _ = client()

    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/readings/{reading_id}/original-text" in response.json()["paths"]
