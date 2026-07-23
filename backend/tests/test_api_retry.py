import pytest
from botocore.exceptions import ClientError

from app.models import ReadingStatus
from app.repositories import readings as readings_repository
from app.repositories.readings import ProcessingStartError
from test_api import NOW, FakeRepo, add_reading, client
from test_api_jobs import RepositoryFakeTable, repository

RetryConflictError = getattr(
    readings_repository,
    "RetryConflictError",
    type("RetryConflictError", (Exception,), {}),
)


class RetryFakeRepo(FakeRepo):
    def __init__(self, fail_start: bool = False, retry_conflict: bool = False) -> None:
        super().__init__()
        self.fail_start = fail_start
        self.retry_conflict = retry_conflict
        self.begin_retry_calls: list[tuple[str, str]] = []
        self.status_calls: list[tuple[str, str, str]] = []
        self.job_status_calls: list[dict[str, object]] = []

    def create(
        self,
        owner_user_id: str,
        reading_id: str,
        original_text_key: str,
        char_count: int,
        vendor: str | None,
        voice: str | None,
        abbreviation_readings: list[dict[str, str]] | None = None,
    ) -> dict:
        item = super().create(
            owner_user_id,
            reading_id,
            original_text_key,
            char_count,
            vendor,
            voice,
            abbreviation_readings,
        )
        item["attempts"] = 1
        return item

    def begin_retry(self, owner_user_id: str, reading_id: str) -> int:
        self.begin_retry_calls.append((owner_user_id, reading_id))
        item = self.items[(owner_user_id, reading_id)]
        if self.retry_conflict or item["status"] not in {
            "completed",
            "failed",
            "failed_to_start",
        }:
            raise RetryConflictError
        attempts = int(item.get("attempts", 1)) + 1
        item["attempts"] = attempts
        item["status"] = "uploaded"
        item["updated_at"] = NOW
        return attempts

    def create_job(self, owner_user_id: str, reading_id: str, attempt: int) -> dict:
        job_id = f"job-{len(self.jobs) + 1}"
        item = {
            "job_id": job_id,
            "reading_id": reading_id,
            "owner_user_id": owner_user_id,
            "attempt": attempt,
            "status": "uploaded",
            "error": None,
            "failed_step": None,
            "created_at": NOW,
            "updated_at": NOW,
        }
        self.jobs[(owner_user_id, job_id)] = item
        return item

    def set_status(
        self,
        owner_user_id: str,
        reading_id: str,
        status: ReadingStatus | str,
        metadata_patch: dict[str, object] | None = None,
    ) -> None:
        self.status_calls.append((owner_user_id, reading_id, str(status)))
        item = self.items[(owner_user_id, reading_id)]
        item["status"] = str(status)
        item["updated_at"] = NOW
        if metadata_patch:
            item.setdefault("metadata", {}).update(metadata_patch)

    def set_job_status(
        self,
        owner_user_id: str,
        job_id: str,
        status: ReadingStatus | str,
        error: str | None = None,
        failed_step: str | None = None,
    ) -> None:
        self.job_status_calls.append(
            {
                "owner_user_id": owner_user_id,
                "job_id": job_id,
                "status": str(status),
                "error": error,
                "failed_step": failed_step,
            }
        )
        super().set_job_status(owner_user_id, job_id, str(status), error, failed_step)

    def start_processing(
        self,
        owner_user_id: str,
        reading_id: str,
        original_text_key: str,
        vendor: str | None,
        voice: str | None,
        job_id: str,
        abbreviation_readings: list[dict[str, str]] | None = None,
    ) -> None:
        if self.fail_start:
            raise ProcessingStartError
        super().start_processing(
            owner_user_id,
            reading_id,
            original_text_key,
            vendor,
            voice,
            job_id,
            abbreviation_readings,
        )


class BeginRetryTable(RepositoryFakeTable):
    def update_item(self, **kwargs: object) -> dict[str, dict[str, int]]:
        self.update_calls.append(kwargs)
        return {"Attributes": {"attempts": 2}}


class ConflictingBeginRetryTable(RepositoryFakeTable):
    def update_item(self, **kwargs: object) -> None:
        self.update_calls.append(kwargs)
        raise ClientError(
            {
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "condition failed",
                }
            },
            "UpdateItem",
        )


def terminal_reading(
    repo: RetryFakeRepo,
    status: str = "completed",
    owner_user_id: str = "user_1",
) -> dict:
    item = add_reading(
        repo,
        owner_user_id,
        original_text="source",
        vendor="edge-tts",
        voice="pl-PL-ZofiaNeural",
    )
    item["status"] = status
    item["corrected_text_key"] = f"preserved/{item['reading_id']}/corrected.md"
    item["recording_key"] = f"preserved/{item['reading_id']}/recording.mp3"
    return item


def test_repository_create_stores_first_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Store an attempts counter initialized to one on every new reading."""
    monkeypatch.setattr("app.repositories.readings._now", lambda: NOW)
    table = RepositoryFakeTable()
    repo = repository(table)

    item = repo.create(
        "user-1",
        "reading-1",
        "users/user-1/readings/reading-1/original.txt",
        5,
        "edge-tts",
        "pl-PL-ZofiaNeural",
    )

    assert item["attempts"] == 1
    assert table.put_calls == [{"Item": item}]


def test_repository_begin_retry_is_atomic_terminal_only_and_legacy_safe() -> None:
    """Claim a terminal reading and increment its attempt in one conditional update."""
    table = BeginRetryTable()
    repo = repository(table)

    attempt = repo.begin_retry("user-1", "reading-1")

    assert attempt == 2
    assert len(table.update_calls) == 1
    request = table.update_calls[0]
    assert request["Key"] == {"pk": "USER#user-1", "sk": "READING#reading-1"}
    update = str(request["UpdateExpression"])
    assert "attempts = if_not_exists(attempts," in update
    condition = str(request["ConditionExpression"])
    values = request["ExpressionAttributeValues"]
    one_placeholder = next(key for key, value in values.items() if value == 1)
    assert update.count(one_placeholder) == 2
    uploaded_placeholder = next(key for key, value in values.items() if value == "uploaded")
    assert uploaded_placeholder in update
    for terminal_status in ("completed", "failed", "failed_to_start"):
        placeholder = next(key for key, value in values.items() if value == terminal_status)
        assert placeholder in condition
    status_name = next(
        name for name, value in request["ExpressionAttributeNames"].items() if value == "status"
    )
    assert status_name in update
    assert status_name in condition
    assert request["ReturnValues"] == "UPDATED_NEW"


def test_repository_begin_retry_translates_conditional_failure_to_conflict() -> None:
    """Translate a lost terminal-state race into the repository conflict signal."""
    repo = repository(ConflictingBeginRetryTable())

    with pytest.raises(RetryConflictError):
        repo.begin_retry("user-1", "reading-1")


def test_retry_completed_reading_returns_new_job_and_reuses_stored_inputs() -> None:
    """Retry with a frontend job response and all inputs persisted on the reading."""
    repo = RetryFakeRepo()
    test_client, _ = client(repo)
    created_response = test_client.post(
        "/api/v1/readings",
        json={
            "original_text": "hello",
            "vendor": "edge-tts",
            "voice": "Marek",
            "abbreviation_readings": [
                {"abbreviation": "Np.", "read_as": "en pe"},
                {"abbreviation": "m.in.", "read_as": "między innymi"},
            ],
        },
    )
    assert created_response.status_code == 202
    reading_id = created_response.json()["id"]
    item = repo.items[("user_1", reading_id)]
    assert item["attempts"] == 1
    item["status"] = "completed"
    item["corrected_text_key"] = "preserved/corrected.md"
    item["recording_key"] = "preserved/recording.mp3"
    preserved_keys = (item["corrected_text_key"], item["recording_key"])

    response = test_client.post(f"/api/v1/readings/{reading_id}/retry")

    assert response.status_code == 202
    assert response.json() == {
        "id": "job-2",
        "reading_id": reading_id,
        "attempt": 2,
        "status": "uploaded",
        "progress": None,
        "current_step": "Przesłano",
        "error": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    assert repo.begin_retry_calls == [("user_1", reading_id)]
    assert repo.status_calls == []
    assert repo.started[-1] == {
        "owner_user_id": "user_1",
        "reading_id": reading_id,
        "original_text_key": item["original_text_key"],
        "vendor": item["vendor"],
        "voice": item["voice"],
        "job_id": "job-2",
        "abbreviation_readings": [
            {"abbreviation": "Np.", "read_as": "en pe"},
            {"abbreviation": "m.in.", "read_as": "między innymi"},
        ],
    }
    assert (item["corrected_text_key"], item["recording_key"]) == preserved_keys


def test_retry_legacy_reading_without_attempts_creates_attempt_two() -> None:
    """Treat a legacy reading with no attempts attribute as attempt one."""
    repo = RetryFakeRepo()
    item = terminal_reading(repo)
    item.pop("attempts")
    test_client, _ = client(repo)

    response = test_client.post(f"/api/v1/readings/{item['reading_id']}/retry")

    assert response.status_code == 202
    assert response.json()["attempt"] == 2
    assert item["attempts"] == 2


@pytest.mark.parametrize("ownership", ["missing", "foreign"])
def test_retry_missing_or_foreign_reading_returns_not_found(ownership: str) -> None:
    """Hide absent and other-user readings behind the same not-found error."""
    repo = RetryFakeRepo()
    reading_id = "missing"
    if ownership == "foreign":
        reading_id = str(terminal_reading(repo, owner_user_id="user_2")["reading_id"])
    test_client, _ = client(repo)

    response = test_client.post(f"/api/v1/readings/{reading_id}/retry")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Reading not found"}}
    assert repo.begin_retry_calls == []
    assert repo.jobs == {}


@pytest.mark.parametrize(
    "reading_status",
    ["uploaded", "normalizing", "generating_audio", "merging_audio"],
)
def test_retry_non_terminal_reading_returns_conflict(reading_status: str) -> None:
    """Reject a retry while any processing attempt is active."""
    repo = RetryFakeRepo()
    item = add_reading(repo, "user_1", "source")
    item["status"] = reading_status
    test_client, _ = client(repo)

    response = test_client.post(f"/api/v1/readings/{item['reading_id']}/retry")

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "A processing attempt is already active for this reading",
        }
    }
    assert repo.begin_retry_calls == [("user_1", item["reading_id"])]
    assert repo.jobs == {}
    assert repo.started == []


@pytest.mark.parametrize("reading_status", ["completed", "failed", "failed_to_start"])
def test_retry_is_allowed_from_every_terminal_status(reading_status: str) -> None:
    """Allow retries from each and only each terminal reading status."""
    repo = RetryFakeRepo()
    item = terminal_reading(repo, reading_status)
    test_client, _ = client(repo)

    response = test_client.post(f"/api/v1/readings/{item['reading_id']}/retry")

    assert response.status_code == 202
    assert response.json()["attempt"] == 2
    assert response.json()["reading_id"] == item["reading_id"]


def test_retry_returns_conflict_when_atomic_claim_loses_a_race() -> None:
    """Return conflict when another request claims the terminal reading first."""
    repo = RetryFakeRepo(retry_conflict=True)
    item = terminal_reading(repo)
    test_client, _ = client(repo)

    response = test_client.post(f"/api/v1/readings/{item['reading_id']}/retry")

    assert response.status_code == 409
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "A processing attempt is already active for this reading",
        }
    }
    assert repo.begin_retry_calls == [("user_1", item["reading_id"])]
    assert repo.jobs == {}
    assert repo.started == []


def test_immediate_second_retry_returns_conflict() -> None:
    """Reject a duplicate retry after the first request flips status to uploaded."""
    repo = RetryFakeRepo()
    item = terminal_reading(repo)
    test_client, _ = client(repo)
    path = f"/api/v1/readings/{item['reading_id']}/retry"

    first = test_client.post(path)
    second = test_client.post(path)

    assert first.status_code == 202
    assert second.status_code == 409
    assert second.json() == {
        "error": {
            "code": "conflict",
            "message": "A processing attempt is already active for this reading",
        }
    }
    assert item["attempts"] == 2
    assert len(repo.jobs) == 1
    assert len(repo.started) == 1


def test_retry_start_failure_marks_reading_and_job_without_replacing_outputs() -> None:
    """Fail retry startup while preserving the last successful output pointers."""
    repo = RetryFakeRepo(fail_start=True)
    item = terminal_reading(repo)
    preserved_keys = (item["corrected_text_key"], item["recording_key"])
    test_client, _ = client(repo)

    response = test_client.post(f"/api/v1/readings/{item['reading_id']}/retry")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "processing_start_failed",
            "message": "Failed to start reading processing",
        }
    }
    job = next(iter(repo.jobs.values()))
    assert item["status"] == "failed_to_start"
    assert (item["corrected_text_key"], item["recording_key"]) == preserved_keys
    assert job["attempt"] == 2
    assert job["status"] == "failed_to_start"
    assert job["error"] == "Failed to start reading processing"
    assert job["failed_step"] == "start_processing"
    assert repo.job_status_calls == [
        {
            "owner_user_id": "user_1",
            "job_id": job["job_id"],
            "status": "failed_to_start",
            "error": "Failed to start reading processing",
            "failed_step": "start_processing",
        }
    ]
    listed_job = test_client.get("/api/v1/jobs").json()["items"][0]
    assert listed_job["error"] == {
        "code": "processing_start_failed",
        "message": "Failed to start reading processing",
        "step": "start_processing",
    }


def test_retry_requires_authentication() -> None:
    """Reject retry requests without authenticated Clerk claims."""
    test_client, _ = client(RetryFakeRepo(), auth=False)

    response = test_client.post("/api/v1/readings/reading-1/retry")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_retry_endpoint_is_in_openapi() -> None:
    """Publish the protected retry operation in the API schema."""
    test_client, _ = client(RetryFakeRepo())

    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    assert "post" in response.json()["paths"]["/api/v1/readings/{reading_id}/retry"]
