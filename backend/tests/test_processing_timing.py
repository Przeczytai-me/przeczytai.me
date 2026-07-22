import asyncio
import json
from pathlib import Path

import pytest

from app.config import Settings
from app.processing import process_reading
from app.repositories.readings import ReadingRepository
from app.splitting import split_paragraphs, split_sentences, split_text
from app.storage import FileStorage
from app.tts import TtsSelection

NOW = "2026-07-22T12:00:00Z"
ORIGINAL_KEY = "users/user-1/readings/reading-1/original.txt"
ORIGINAL_TEXT = "Ala ma kota. Ola ma psa.\n\nTo drugi akapit."


class TimingStorage:
    def __init__(self) -> None:
        self.texts = {ORIGINAL_KEY: ORIGINAL_TEXT}
        self.bytes: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}

    def get_text(self, key: str) -> str:
        return self.texts[key]

    def put_text(self, key: str, content: str, content_type: str) -> None:
        self.texts[key] = content
        self.content_types[key] = content_type

    def put_bytes(self, key: str, content: bytes, content_type: str) -> None:
        self.bytes[key] = content
        self.content_types[key] = content_type

    def corrected_text_key(
        self, owner_user_id: str, reading_id: str, job_id: str | None = None
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

    def timing_map_key(
        self, owner_user_id: str, reading_id: str, job_id: str | None = None
    ) -> str:
        filename = "timing.json" if job_id is None else f"timing-{job_id}.json"
        return f"users/{owner_user_id}/readings/{reading_id}/{filename}"


class TimingRepo:
    def __init__(self) -> None:
        self.completed: dict[str, object] | None = None
        self.reading_status = "uploaded"
        self.job_status = "uploaded"

    def get(self, owner_user_id: str, reading_id: str) -> dict[str, str] | None:
        del owner_user_id, reading_id
        return {"status": self.reading_status}

    def get_job(self, owner_user_id: str, job_id: str) -> dict[str, str] | None:
        del owner_user_id, job_id
        return {"status": self.job_status}

    def set_status(
        self,
        owner_user_id: str,
        reading_id: str,
        status: str,
        metadata_patch: dict[str, object] | None = None,
    ) -> None:
        del owner_user_id, reading_id, metadata_patch
        self.reading_status = str(status)

    def set_job_status(
        self,
        owner_user_id: str,
        job_id: str,
        status: str,
        error: str | None = None,
        failed_step: str | None = None,
    ) -> None:
        del owner_user_id, job_id, error, failed_step
        self.job_status = str(status)

    def mark_completed(
        self,
        owner_user_id: str,
        reading_id: str,
        corrected_text_key: str,
        recording_key: str,
        *args: object,
        timing_map_key: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        for argument in args:
            if isinstance(argument, str):
                timing_map_key = argument
            elif isinstance(argument, dict):
                metadata = argument
        assert timing_map_key is not None
        assert metadata is not None
        self.completed = {
            "owner_user_id": owner_user_id,
            "reading_id": reading_id,
            "corrected_text_key": corrected_text_key,
            "recording_key": recording_key,
            "timing_map_key": timing_map_key,
            "metadata": metadata,
        }
        self.reading_status = "completed"


class RepositoryFakeTable:
    def __init__(self) -> None:
        self.update_calls: list[dict[str, object]] = []

    def update_item(self, **kwargs: object) -> None:
        self.update_calls.append(kwargs)


async def fake_synthesize(
    text: str,
    output_path: str,
    selection: TtsSelection,
    settings: Settings,
) -> None:
    del selection, settings
    Path(output_path).write_bytes(f"mp3:{text}".encode())


def processing_event(job_id: str | None) -> dict[str, str]:
    event = {
        "reading_id": "reading-1",
        "owner_user_id": "user-1",
        "original_text_key": ORIGINAL_KEY,
    }
    if job_id is not None:
        event["job_id"] = job_id
    return event


@pytest.mark.parametrize(
    ("job_id", "filename"),
    [(None, "timing.json"), ("job-2", "timing-job-2.json")],
)
def test_processing_persists_timing_map_and_completes_with_its_key(
    job_id: str | None,
    filename: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Persist parseable timing JSON under the event-scoped key before completion."""
    storage = TimingStorage()
    repo = TimingRepo()
    duration_paths: list[Path] = []
    fixed_durations = iter([2.5, 3.75])

    def fixed_mp3_duration(path: Path) -> float:
        assert path.is_file()
        assert path.read_bytes().startswith(b"mp3:")
        duration_paths.append(path)
        return next(fixed_durations)

    def merge_after_durations(paths: list[Path], output: Path) -> None:
        assert paths == duration_paths
        output.write_bytes(b"merged-mp3")

    monkeypatch.setattr("app.processing.mp3_duration_seconds", fixed_mp3_duration)
    monkeypatch.setattr("app.processing.merge_mp3_files", merge_after_durations)

    result = asyncio.run(
        process_reading(
            processing_event(job_id),
            Settings(
                readings_table_name="table",
                files_bucket_name="bucket",
                max_chunk_chars=30,
            ),
            storage,
            repo,
            fake_synthesize,
        )
    )

    timing_key = f"users/user-1/readings/reading-1/{filename}"
    corrected_key = storage.corrected_text_key("user-1", "reading-1", job_id)
    corrected_chunks = split_text(storage.texts[corrected_key], 30)
    expected_sentences = [
        sentence
        for corrected_chunk in corrected_chunks
        for paragraph in split_paragraphs(corrected_chunk.text)
        for sentence in split_sentences(paragraph)
    ]
    timing = json.loads(storage.texts[timing_key])

    assert result == {"status": "completed"}
    assert storage.content_types[timing_key] == "application/json"
    assert timing["version"] == 1
    assert timing["duration_ms"] == 6250
    assert [segment["text"] for segment in timing["segments"]] == expected_sentences
    assert timing["segments"][0]["start_ms"] == 0
    assert timing["segments"][-1]["end_ms"] == 6250
    assert [segment["id"] for segment in timing["segments"]] == [
        f"segment-{index}" for index in range(1, len(timing["segments"]) + 1)
    ]
    assert all(
        isinstance(segment[field], int)
        for segment in timing["segments"]
        for field in ("paragraph_index", "start_ms", "end_ms")
    )
    assert [path.name for path in duration_paths] == [
        "reading-1-0000.mp3",
        "reading-1-0001.mp3",
    ]
    assert repo.completed is not None
    assert repo.completed["timing_map_key"] == timing_key


@pytest.mark.parametrize(
    ("job_id", "expected"),
    [
        (None, "users/user-1/readings/reading-1/timing.json"),
        ("job-2", "users/user-1/readings/reading-1/timing-job-2.json"),
    ],
)
def test_file_storage_builds_event_scoped_timing_map_keys(
    job_id: str | None, expected: str
) -> None:
    """Use legacy and job-scoped timing object names consistently."""
    storage = FileStorage(None)

    assert storage.timing_map_key("user-1", "reading-1", job_id) == expected


def test_mark_completed_persists_timing_map_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Publish the timing object key atomically with the completed reading outputs."""
    monkeypatch.setattr("app.repositories.readings._now", lambda: NOW)
    table = RepositoryFakeTable()
    repo = object.__new__(ReadingRepository)
    repo.table = table

    repo.mark_completed(
        owner_user_id="user-1",
        reading_id="reading-1",
        corrected_text_key="users/user-1/readings/reading-1/corrected.md",
        recording_key="users/user-1/readings/reading-1/recording.mp3",
        timing_map_key="users/user-1/readings/reading-1/timing.json",
        metadata={"chunks": 2},
    )

    assert len(table.update_calls) == 1
    request = table.update_calls[0]
    assert "timing_map_key = :timing_map_key" in str(request["UpdateExpression"])
    assert request["ExpressionAttributeValues"][":timing_map_key"] == (
        "users/user-1/readings/reading-1/timing.json"
    )
    assert request["ExpressionAttributeValues"][":status"] == "completed"
