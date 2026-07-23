import asyncio

import pytest

from app.config import Settings
from app.models import ReadingStatus
from app.processing import process_reading
from test_processing import FakeRepo, FakeStorage, fake_synthesize


class JobsFakeRepo(FakeRepo):
    def __init__(self, job_status: str = "uploaded") -> None:
        super().__init__()
        self.jobs: dict[tuple[str, str], dict[str, object]] = {
            ("user-1", "processing-job-1"): {
                "job_id": "processing-job-1",
                "reading_id": "job-1",
                "owner_user_id": "user-1",
                "attempt": 1,
                "status": job_status,
            }
        }
        self.get_job_calls: list[tuple[str, str]] = []
        self.job_status_calls: list[dict[str, object]] = []

    def get_job(self, owner_user_id: str, job_id: str) -> dict[str, object] | None:
        self.get_job_calls.append((owner_user_id, job_id))
        return self.jobs.get((owner_user_id, job_id))

    def set_job_status(
        self,
        owner_user_id: str,
        job_id: str,
        status: ReadingStatus | str,
        error: str | None = None,
        failed_step: str | None = None,
    ) -> None:
        call = {
            "owner_user_id": owner_user_id,
            "job_id": job_id,
            "status": str(status),
            "error": error,
            "failed_step": failed_step,
        }
        self.job_status_calls.append(call)
        job = self.jobs.get((owner_user_id, job_id))
        if job is None:
            return
        job["status"] = str(status)
        if error is not None:
            job["error"] = error
        if failed_step is not None:
            job["failed_step"] = failed_step


def job_event() -> dict[str, str]:
    return {
        "reading_id": "job-1",
        "job_id": "processing-job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
    }


def settings() -> Settings:
    return Settings(readings_table_name="table", files_bucket_name="bucket")


def test_processing_updates_job_through_all_stages_and_completes() -> None:
    """Mirror every successful reading transition onto its job."""
    repo = JobsFakeRepo()

    result = asyncio.run(
        process_reading(job_event(), settings(), FakeStorage(), repo, fake_synthesize)
    )

    assert result == {"status": "completed"}
    assert repo.get_job_calls == [("user-1", "processing-job-1")]
    assert [call["status"] for call in repo.job_status_calls] == [
        "normalizing",
        "generating_audio",
        "merging_audio",
        "completed",
    ]
    assert all(call["owner_user_id"] == "user-1" for call in repo.job_status_calls)
    assert all(call["job_id"] == "processing-job-1" for call in repo.job_status_calls)
    assert repo.jobs[("user-1", "processing-job-1")]["status"] == "completed"


@pytest.mark.parametrize(
    ("failed_stage", "safe_error"),
    [
        ("normalizing", "Text normalization failed"),
        ("generating_audio", "Audio generation failed"),
        ("merging_audio", "Audio merging failed"),
    ],
)
def test_processing_marks_job_failed_with_stage_safe_error(
    failed_stage: str,
    safe_error: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Store a stage-derived job error without leaking the raw exception."""

    class FailingReadStorage(FakeStorage):
        def get_text(self, key: str) -> str:
            del key
            raise RuntimeError("private provider detail")

    async def failing_synthesize(*_args: object) -> None:
        raise RuntimeError("private provider detail")

    def failing_merge(*_args: object) -> None:
        raise RuntimeError("private provider detail")

    storage: FakeStorage = FakeStorage()
    synthesize = fake_synthesize
    if failed_stage == "normalizing":
        storage = FailingReadStorage()
    elif failed_stage == "generating_audio":
        synthesize = failing_synthesize
    else:
        monkeypatch.setattr("app.processing.merge_mp3_files", failing_merge)
    repo = JobsFakeRepo()

    with pytest.raises(RuntimeError, match="private provider detail"):
        asyncio.run(process_reading(job_event(), settings(), storage, repo, synthesize))

    assert repo.job_status_calls[-1] == {
        "owner_user_id": "user-1",
        "job_id": "processing-job-1",
        "status": "failed",
        "error": safe_error,
        "failed_step": failed_stage,
    }
    assert repo.jobs[("user-1", "processing-job-1")]["error"] == safe_error
    assert "private provider detail" not in str(repo.jobs[("user-1", "processing-job-1")])


@pytest.mark.parametrize("terminal_status", ["completed", "failed", "failed_to_start"])
def test_processing_exits_early_for_terminal_job(terminal_status: str) -> None:
    """Use terminal job state for idempotency when a job id is present."""
    repo = JobsFakeRepo(job_status=terminal_status)
    synthesized: list[str] = []

    async def recording_synthesize(*args: object) -> None:
        synthesized.append(str(args[0]))

    result = asyncio.run(
        process_reading(job_event(), settings(), FakeStorage(), repo, recording_synthesize)
    )

    assert result == {"status": terminal_status}
    assert repo.get_job_calls == [("user-1", "processing-job-1")]
    assert repo.job_status_calls == []
    assert repo.transitions == []
    assert synthesized == []


def test_processing_legacy_event_makes_no_job_calls() -> None:
    """Keep events without a job id compatible with reading-only processing."""
    event = job_event()
    event.pop("job_id")
    repo = JobsFakeRepo()

    result = asyncio.run(process_reading(event, settings(), FakeStorage(), repo, fake_synthesize))

    assert result == {"status": "completed"}
    assert repo.get_job_calls == []
    assert repo.job_status_calls == []
    assert [status for status, _ in repo.transitions] == [
        "normalizing",
        "generating_audio",
        "merging_audio",
        "completed",
    ]
