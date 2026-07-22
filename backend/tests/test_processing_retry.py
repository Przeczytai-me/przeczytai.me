import asyncio

import pytest

from app.config import Settings
from app.processing import process_reading
from app.storage import FileStorage
from test_processing import FakeStorage, fake_synthesize
from test_processing_jobs import JobsFakeRepo, job_event


class RetryStorage(FakeStorage):
    def corrected_text_key(
        self,
        owner_user_id: str,
        reading_id: str,
        job_id: str | None = None,
    ) -> str:
        filename = "corrected.md" if job_id is None else f"corrected-{job_id}.md"
        return f"users/{owner_user_id}/readings/{reading_id}/{filename}"

    def recording_key(
        self,
        owner_user_id: str,
        reading_id: str,
        extension: str = "mp3",
        job_id: str | None = None,
    ) -> str:
        filename = f"recording.{extension}" if job_id is None else f"recording-{job_id}.{extension}"
        return f"users/{owner_user_id}/readings/{reading_id}/{filename}"


class RetryRepo(JobsFakeRepo):
    def __init__(self, reading_status: str = "uploaded") -> None:
        super().__init__(job_status="uploaded")
        self.items[("user-1", "job-1")] = {
            "status": reading_status,
            "metadata": {},
            "corrected_text_key": "users/user-1/readings/job-1/corrected.md",
            "recording_key": "users/user-1/readings/job-1/recording.mp3",
        }

    def mark_completed(
        self,
        owner_user_id: str,
        reading_id: str,
        corrected_text_key: str,
        recording_key: str,
        metadata: dict[str, object],
    ) -> None:
        super().mark_completed(
            owner_user_id,
            reading_id,
            corrected_text_key,
            recording_key,
            metadata,
        )
        item = self.items[(owner_user_id, reading_id)]
        item["corrected_text_key"] = corrected_text_key
        item["recording_key"] = recording_key


def processing_settings() -> Settings:
    return Settings(readings_table_name="table", files_bucket_name="bucket")


def test_file_storage_key_helpers_keep_legacy_unscoped_names() -> None:
    """Keep legacy output object names when no job id is supplied."""
    storage = FileStorage(None)

    assert storage.corrected_text_key("user-1", "reading-1") == (
        "users/user-1/readings/reading-1/corrected.md"
    )
    assert storage.recording_key("user-1", "reading-1") == (
        "users/user-1/readings/reading-1/recording.mp3"
    )
    assert storage.recording_key("user-1", "reading-1", "wav") == (
        "users/user-1/readings/reading-1/recording.wav"
    )


def test_file_storage_key_helpers_scope_retry_outputs_to_job() -> None:
    """Include the job id in corrected text and recording object names."""
    storage = FileStorage(None)

    assert storage.corrected_text_key("user-1", "reading-1", job_id="job-2") == (
        "users/user-1/readings/reading-1/corrected-job-2.md"
    )
    assert storage.recording_key("user-1", "reading-1", job_id="job-2") == (
        "users/user-1/readings/reading-1/recording-job-2.mp3"
    )
    assert storage.recording_key("user-1", "reading-1", "wav", job_id="job-2") == (
        "users/user-1/readings/reading-1/recording-job-2.wav"
    )


def test_processing_with_job_writes_scoped_outputs_and_completes_with_them() -> None:
    """Write retry outputs under job-scoped keys before publishing them."""
    storage = RetryStorage()
    repo = RetryRepo()

    result = asyncio.run(
        process_reading(job_event(), processing_settings(), storage, repo, fake_synthesize)
    )

    corrected_key = "users/user-1/readings/job-1/corrected-processing-job-1.md"
    recording_key = "users/user-1/readings/job-1/recording-processing-job-1.mp3"
    assert result == {"status": "completed"}
    assert storage.texts[corrected_key] == "Ala ma kota."
    assert storage.bytes[recording_key] == (b"mp3:edge-tts:pl-PL-ZofiaNeural:Ala ma kota.")
    assert repo.completed is not None
    assert repo.completed["corrected_text_key"] == corrected_key
    assert repo.completed["recording_key"] == recording_key
    assert repo.items[("user-1", "job-1")]["corrected_text_key"] == corrected_key
    assert repo.items[("user-1", "job-1")]["recording_key"] == recording_key


def test_failed_retry_preserves_previous_item_keys_and_stored_objects() -> None:
    """Leave successful outputs untouched when a retry fails during synthesis."""
    storage = RetryStorage()
    old_corrected_key = "users/user-1/readings/job-1/corrected.md"
    old_recording_key = "users/user-1/readings/job-1/recording.mp3"
    storage.texts[old_corrected_key] = "Previous corrected text"
    storage.bytes[old_recording_key] = b"previous recording"
    repo = RetryRepo(reading_status="completed")

    async def failing_synthesize(*_args: object) -> None:
        raise RuntimeError("retry synthesis failed")

    with pytest.raises(RuntimeError, match="retry synthesis failed"):
        asyncio.run(
            process_reading(
                job_event(),
                processing_settings(),
                storage,
                repo,
                failing_synthesize,
            )
        )

    item = repo.items[("user-1", "job-1")]
    assert item["corrected_text_key"] == old_corrected_key
    assert item["recording_key"] == old_recording_key
    assert storage.texts[old_corrected_key] == "Previous corrected text"
    assert storage.bytes[old_recording_key] == b"previous recording"
    assert (
        storage.texts["users/user-1/readings/job-1/corrected-processing-job-1.md"] == "Ala ma kota."
    )
    assert repo.completed is None
    assert repo.jobs[("user-1", "processing-job-1")]["status"] == "failed"


def test_completed_reading_with_fresh_job_still_processes() -> None:
    """Use fresh job state instead of completed reading state for early exit."""
    storage = RetryStorage()
    repo = RetryRepo(reading_status="completed")
    synthesized: list[str] = []

    async def recording_synthesize(*args: object) -> None:
        synthesized.append(str(args[0]))
        await fake_synthesize(*args)

    result = asyncio.run(
        process_reading(
            job_event(),
            processing_settings(),
            storage,
            repo,
            recording_synthesize,
        )
    )

    assert result == {"status": "completed"}
    assert synthesized == ["Ala ma kota."]
    assert repo.get_job_calls == [("user-1", "processing-job-1")]
    assert repo.jobs[("user-1", "processing-job-1")]["status"] == "completed"


def test_processing_legacy_event_keeps_unscoped_output_keys() -> None:
    """Keep legacy event output writes compatible when no job id is present."""
    event = job_event()
    event.pop("job_id")
    storage = RetryStorage()
    repo = RetryRepo()

    result = asyncio.run(
        process_reading(event, processing_settings(), storage, repo, fake_synthesize)
    )

    corrected_key = "users/user-1/readings/job-1/corrected.md"
    recording_key = "users/user-1/readings/job-1/recording.mp3"
    assert result == {"status": "completed"}
    assert storage.texts[corrected_key] == "Ala ma kota."
    assert storage.bytes[recording_key] == b"mp3:edge-tts:pl-PL-ZofiaNeural:Ala ma kota."
    assert repo.completed is not None
    assert repo.completed["corrected_text_key"] == corrected_key
    assert repo.completed["recording_key"] == recording_key
    assert repo.get_job_calls == []
    assert repo.job_status_calls == []
