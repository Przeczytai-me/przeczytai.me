import base64
import json

import pytest

from app.models import ReadingStatus
from app.repositories.readings import ProcessingStartError, ReadingRepository
from test_api import NOW, FakeRepo, client


class JobsFakeRepo(FakeRepo):
    def __init__(self, fail_start: bool = False) -> None:
        super().__init__()
        self.jobs: dict[tuple[str, str], dict] = {}
        self.job_status_calls: list[dict[str, object]] = []
        self.list_job_calls: list[tuple[str, int, str | None]] = []
        self.fail_start = fail_start

    def create_job(self, owner_user_id: str, reading_id: str, attempt: int) -> dict:
        job_id = self.next_id()
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

    def get_job(self, owner_user_id: str, job_id: str) -> dict | None:
        return self.jobs.get((owner_user_id, job_id))

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
        item = self.jobs.get((owner_user_id, job_id))
        if item is None:
            return
        item["status"] = str(status)
        item["updated_at"] = NOW
        if error is not None:
            item["error"] = error
        if failed_step is not None:
            item["failed_step"] = failed_step

    def list_jobs(
        self, owner_user_id: str, limit: int, cursor: str | None
    ) -> tuple[list[dict], str | None]:
        self.list_job_calls.append((owner_user_id, limit, cursor))
        items = sorted(
            (
                item
                for (user_id, _), item in self.jobs.items()
                if user_id == owner_user_id
            ),
            key=lambda item: str(item.get("job_id", "")),
            reverse=True,
        )
        start = int(cursor) + 1 if cursor is not None else 0
        page = items[start : start + limit]
        next_index = start + len(page) - 1
        next_cursor = str(next_index) if start + len(page) < len(items) else None
        return page, next_cursor

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
        self.started.append(
            {
                "owner_user_id": owner_user_id,
                "reading_id": reading_id,
                "original_text_key": original_text_key,
                "vendor": vendor,
                "voice": voice,
                "job_id": job_id,
                "abbreviation_readings": abbreviation_readings,
            }
        )


class RepositoryFakeTable:
    def __init__(self) -> None:
        self.put_calls: list[dict[str, object]] = []
        self.get_calls: list[dict[str, object]] = []
        self.update_calls: list[dict[str, object]] = []
        self.query_calls: list[dict[str, object]] = []
        self.get_response: dict[str, object] = {}
        self.query_response: dict[str, object] = {}

    def put_item(self, **kwargs: object) -> None:
        self.put_calls.append(kwargs)

    def get_item(self, **kwargs: object) -> dict[str, object]:
        self.get_calls.append(kwargs)
        return self.get_response

    def update_item(self, **kwargs: object) -> None:
        self.update_calls.append(kwargs)

    def query(self, **kwargs: object) -> dict[str, object]:
        self.query_calls.append(kwargs)
        return self.query_response


class FakeLambdaClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def invoke(self, **kwargs: object) -> dict[str, int]:
        self.calls.append(kwargs)
        return {"StatusCode": 202}


def repository(table: RepositoryFakeTable) -> ReadingRepository:
    repo = object.__new__(ReadingRepository)
    repo.table = table
    repo.processor_function_name = "processor"
    repo.lambda_client = FakeLambdaClient()
    return repo


def add_job(
    repo: JobsFakeRepo,
    owner_user_id: str,
    job_id: str,
    *,
    reading_id: str = "reading-1",
    attempt: int = 1,
    status: str = "uploaded",
    error: str | None = None,
    failed_step: str | None = None,
) -> dict:
    item = {
        "job_id": job_id,
        "reading_id": reading_id,
        "owner_user_id": owner_user_id,
        "attempt": attempt,
        "status": status,
        "error": error,
        "failed_step": failed_step,
        "created_at": NOW,
        "updated_at": NOW,
    }
    repo.jobs[(owner_user_id, job_id)] = item
    return item


def test_repository_create_job_writes_the_pinned_item(monkeypatch: pytest.MonkeyPatch) -> None:
    """Create an uploaded attempt item under the user job sort key."""
    monkeypatch.setattr("app.repositories.readings._now", lambda: NOW)
    table = RepositoryFakeTable()
    repo = repository(table)
    monkeypatch.setattr(repo, "next_id", lambda: "01JOBULID")

    item = repo.create_job("user-1", "reading-1", 1)

    assert item == {
        "pk": "USER#user-1",
        "sk": "JOB#01JOBULID",
        "job_id": "01JOBULID",
        "reading_id": "reading-1",
        "owner_user_id": "user-1",
        "attempt": 1,
        "status": "uploaded",
        "error": None,
        "failed_step": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    assert table.put_calls == [{"Item": item}]


def test_repository_get_job_uses_user_and_job_keys() -> None:
    """Fetch a job only from its owner's partition."""
    table = RepositoryFakeTable()
    expected = {"job_id": "job-1", "owner_user_id": "user-1"}
    table.get_response = {"Item": expected}
    repo = repository(table)

    result = repo.get_job("user-1", "job-1")

    assert result == expected
    assert table.get_calls == [
        {"Key": {"pk": "USER#user-1", "sk": "JOB#job-1"}}
    ]


def test_repository_set_job_status_updates_failure_fields_conditionally(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Update an existing job's status, timestamp, and supplied failure detail."""
    monkeypatch.setattr("app.repositories.readings._now", lambda: NOW)
    table = RepositoryFakeTable()
    repo = repository(table)

    repo.set_job_status(
        "user-1",
        "job-1",
        ReadingStatus.FAILED,
        error="Audio generation failed",
        failed_step="generating_audio",
    )

    assert len(table.update_calls) == 1
    request = table.update_calls[0]
    assert request["Key"] == {"pk": "USER#user-1", "sk": "JOB#job-1"}
    assert request["ConditionExpression"] == "attribute_exists(job_id)"
    values = request["ExpressionAttributeValues"]
    assert set(values.values()) == {
        "failed",
        NOW,
        "Audio generation failed",
        "generating_audio",
    }
    expression = str(request["UpdateExpression"])
    assert "updated_at" in expression
    assert "error" in expression
    assert "failed_step" in expression


def test_repository_set_job_status_omits_unsupplied_failure_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Leave failure detail untouched during ordinary stage transitions."""
    monkeypatch.setattr("app.repositories.readings._now", lambda: NOW)
    table = RepositoryFakeTable()
    repo = repository(table)

    repo.set_job_status("user-1", "job-1", ReadingStatus.NORMALIZING)

    request = table.update_calls[0]
    expression = str(request["UpdateExpression"])
    assert "error" not in expression
    assert "failed_step" not in expression
    assert set(request["ExpressionAttributeValues"].values()) == {"normalizing", NOW}


def test_repository_list_jobs_queries_newest_first_with_base64_cursor() -> None:
    """Query only job sort keys newest-first using the shared cursor convention."""
    table = RepositoryFakeTable()
    last_key = {"pk": "USER#user-1", "sk": "JOB#job-2"}
    table.query_response = {"Items": [{"job_id": "job-3"}], "LastEvaluatedKey": last_key}
    repo = repository(table)
    start_key = {"pk": "USER#user-1", "sk": "JOB#job-4"}
    cursor = base64.urlsafe_b64encode(json.dumps(start_key).encode()).decode()

    items, next_cursor = repo.list_jobs("user-1", 2, cursor)

    assert items == [{"job_id": "job-3"}]
    assert next_cursor is not None
    assert json.loads(base64.urlsafe_b64decode(next_cursor).decode()) == last_key
    request = table.query_calls[0]
    assert request["Limit"] == 2
    assert request["ScanIndexForward"] is False
    assert request["ExclusiveStartKey"] == start_key
    condition = request["KeyConditionExpression"].get_expression()
    partition, sort_key = condition["values"]
    partition_values = partition.get_expression()["values"]
    sort_key_values = sort_key.get_expression()["values"]
    assert (partition_values[0].name, partition_values[1]) == ("pk", "USER#user-1")
    assert (sort_key_values[0].name, sort_key_values[1]) == ("sk", "JOB#")


def test_repository_start_processing_includes_job_id_in_lambda_payload() -> None:
    """Link the asynchronous processor invocation to its distinct job."""
    repo = repository(RepositoryFakeTable())

    repo.start_processing(
        "user-1",
        "reading-1",
        "users/user-1/readings/reading-1/original.txt",
        "edge-tts",
        "pl-PL-ZofiaNeural",
        job_id="job-1",
    )

    assert isinstance(repo.lambda_client, FakeLambdaClient)
    request = repo.lambda_client.calls[0]
    assert request["FunctionName"] == "processor"
    assert request["InvocationType"] == "Event"
    assert json.loads(request["Payload"].decode()) == {
        "reading_id": "reading-1",
        "job_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/reading-1/original.txt",
        "vendor": "edge-tts",
        "voice": "pl-PL-ZofiaNeural",
        "abbreviation_readings": None,
    }


def test_list_jobs_returns_contract_shape() -> None:
    """Return the frontend ProcessingJob representation without legacy fields."""
    repo = JobsFakeRepo()
    add_job(repo, "user_1", "job-1", status="generating_audio")
    test_client, _ = client(repo)

    response = test_client.get("/api/v1/jobs")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": "job-1",
                "reading_id": "reading-1",
                "attempt": 1,
                "status": "generating_audio",
                "progress": None,
                "current_step": "Generowanie audio",
                "error": None,
                "created_at": NOW,
                "updated_at": NOW,
            }
        ],
        "next_cursor": None,
    }


@pytest.mark.parametrize(
    ("internal_status", "public_status", "current_step"),
    [
        ("uploaded", "uploaded", "Przesłano"),
        ("normalizing", "extracting_text", "Przetwarzanie tekstu"),
        ("processing", "extracting_text", "processing"),
        ("generating_audio", "generating_audio", "Generowanie audio"),
        ("merging_audio", "generating_audio", "Scalanie nagrania"),
        ("completed", "ready", "Gotowe"),
        ("failed", "failed", "Błąd przetwarzania"),
        ("failed_to_start", "failed", "Błąd uruchomienia"),
    ],
)
def test_list_jobs_maps_internal_status_and_polish_current_step(
    internal_status: str, public_status: str, current_step: str
) -> None:
    """Map persisted pipeline state to the frontend status and Polish step label."""
    repo = JobsFakeRepo()
    stored_error = "Text normalization failed" if internal_status == "failed" else None
    failed_step = "normalizing" if internal_status == "failed" else None
    add_job(
        repo,
        "user_1",
        "job-1",
        reading_id="reading-ready",
        status=internal_status,
        error=stored_error,
        failed_step=failed_step,
    )
    test_client, _ = client(repo)

    response = test_client.get("/api/v1/jobs")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["reading_id"] == "reading-ready"
    assert item["status"] == public_status
    assert item["current_step"] == current_step
    assert item["progress"] is None
    if internal_status == "failed":
        assert item["error"] == {
            "code": "processing_failed",
            "message": "Text normalization failed",
            "step": "normalizing",
        }
    elif internal_status == "failed_to_start":
        assert item["error"] == {
            "code": "processing_start_failed",
            "message": "Failed to start reading processing",
            "step": "start_processing",
        }
    else:
        assert item["error"] is None
    assert repo.jobs[("user_1", "job-1")]["status"] == internal_status
    assert "state" not in item
    assert "step_message" not in item
    assert "failed_step" not in item


def test_list_jobs_serializes_processing_failure_error() -> None:
    """Nest the stored safe processing error and failed stage for frontend use."""
    repo = JobsFakeRepo()
    add_job(
        repo,
        "user_1",
        "job-1",
        status="failed",
        error="Audio generation failed",
        failed_step="generating_audio",
    )
    test_client, _ = client(repo)

    item = test_client.get("/api/v1/jobs").json()["items"][0]

    assert item["error"] == {
        "code": "processing_failed",
        "message": "Audio generation failed",
        "step": "generating_audio",
    }


def test_list_jobs_serializes_processing_start_failure_error() -> None:
    """Expose a fixed safe startup error with the pinned startup step."""
    repo = JobsFakeRepo()
    add_job(
        repo,
        "user_1",
        "job-1",
        status="failed_to_start",
        error="provider detail that must not leak",
        failed_step="some-other-step",
    )
    test_client, _ = client(repo)

    item = test_client.get("/api/v1/jobs").json()["items"][0]

    assert item["error"] == {
        "code": "processing_start_failed",
        "message": "Failed to start reading processing",
        "step": "start_processing",
    }


def test_list_jobs_is_user_scoped() -> None:
    """List only jobs owned by the authenticated user."""
    repo = JobsFakeRepo()
    add_job(repo, "user_1", "job-mine", reading_id="reading-mine")
    add_job(repo, "user_2", "job-other", reading_id="reading-other")
    test_client, _ = client(repo)

    response = test_client.get("/api/v1/jobs")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == ["job-mine"]
    assert repo.list_job_calls == [("user_1", 20, None)]


def test_list_jobs_paginates_and_passes_cursor_through() -> None:
    """Pass repository cursors through and use them for the next page."""
    repo = JobsFakeRepo()
    add_job(repo, "user_1", "job-001")
    add_job(repo, "user_1", "job-002")
    add_job(repo, "user_1", "job-003")
    test_client, _ = client(repo)

    first = test_client.get("/api/v1/jobs", params={"limit": 2})
    second = test_client.get(
        "/api/v1/jobs",
        params={"limit": 2, "cursor": first.json()["next_cursor"]},
    )

    assert first.status_code == 200
    assert [item["id"] for item in first.json()["items"]] == ["job-003", "job-002"]
    assert first.json()["next_cursor"] == "1"
    assert second.status_code == 200
    assert [item["id"] for item in second.json()["items"]] == ["job-001"]
    assert second.json()["next_cursor"] is None
    assert repo.list_job_calls == [("user_1", 2, None), ("user_1", 2, "1")]


def test_deleted_reading_job_remains_listed() -> None:
    """Keep immutable processing history after its reading is deleted."""
    repo = JobsFakeRepo()
    reading = repo.create(
        "user_1",
        "reading-1",
        "users/user_1/readings/reading-1/original.txt",
        5,
        "edge-tts",
        "pl-PL-ZofiaNeural",
    )
    add_job(repo, "user_1", "job-1", reading_id=str(reading["reading_id"]))
    test_client, _ = client(repo)

    deleted = test_client.delete("/api/v1/readings/reading-1")
    response = test_client.get("/api/v1/jobs")

    assert deleted.status_code == 204
    assert repo.get("user_1", "reading-1") is None
    assert [item["id"] for item in response.json()["items"]] == ["job-1"]


@pytest.mark.parametrize("limit", [0, 51])
def test_list_jobs_validates_limit(limit: int) -> None:
    """Reject job page sizes outside the supported range."""
    test_client, _ = client(JobsFakeRepo())

    response = test_client.get("/api/v1/jobs", params={"limit": limit})

    assert response.status_code == 422


def test_list_jobs_skips_incomplete_items() -> None:
    """Skip job rows missing any required response field."""
    repo = JobsFakeRepo()
    complete = add_job(repo, "user_1", "job-complete")
    required = ["job_id", "reading_id", "attempt", "status", "created_at", "updated_at"]
    for index, field in enumerate(required):
        item = {**complete, "job_id": f"job-bad-{index}"}
        item.pop(field)
        repo.jobs[("user_1", f"job-bad-{index}")] = item
    test_client, _ = client(repo)

    response = test_client.get("/api/v1/jobs")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == ["job-complete"]


def test_list_jobs_requires_authentication() -> None:
    """Reject jobs listing when JWT claims are missing."""
    test_client, _ = client(JobsFakeRepo(), auth=False)

    response = test_client.get("/api/v1/jobs")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_jobs_endpoint_is_in_openapi() -> None:
    """Publish the jobs list operation in the API schema."""
    test_client, _ = client(JobsFakeRepo())

    response = test_client.get("/openapi.json")

    assert response.status_code == 200
    assert "get" in response.json()["paths"]["/api/v1/jobs"]


def test_create_reading_creates_initial_job_and_starts_it() -> None:
    """Create attempt one and link it to initial reading processing."""
    repo = JobsFakeRepo()
    test_client, _ = client(repo)

    response = test_client.post("/api/v1/readings", json={"original_text": "hello"})

    assert response.status_code == 202
    body = response.json()
    assert set(body) == {
        "id",
        "original_text_key",
        "corrected_text_key",
        "recording_key",
        "vendor",
        "voice",
        "status",
        "metadata",
        "char_count",
        "created_at",
        "updated_at",
    }
    assert len(repo.jobs) == 1
    job = next(iter(repo.jobs.values()))
    assert job["reading_id"] == body["id"]
    assert job["owner_user_id"] == "user_1"
    assert job["attempt"] == 1
    assert job["status"] == "uploaded"
    assert repo.started[0]["job_id"] == job["job_id"]
    assert repo.started[0]["reading_id"] == body["id"]


def test_create_reading_marks_job_failed_when_processing_start_fails() -> None:
    """Fail both reading and initial job when Lambda invocation cannot start."""
    repo = JobsFakeRepo(fail_start=True)
    test_client, _ = client(repo)

    response = test_client.post("/api/v1/readings", json={"original_text": "hello"})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "processing_start_failed"
    reading = next(iter(repo.items.values()))
    job = next(iter(repo.jobs.values()))
    assert reading["status"] == "failed_to_start"
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
