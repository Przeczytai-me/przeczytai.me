import asyncio
import logging
import re
from pathlib import Path

import pytest

from app.config import Settings
from app.costs import CostBreakdown
from app.processing import process_reading
from app.tts import TtsSelection


class FakeStorage:
    def __init__(self) -> None:
        self.texts = {
            "users/user-1/readings/job-1/original.txt": "Ala ma kota.",
        }
        self.bytes: dict[str, bytes] = {}

    def get_text(self, key: str) -> str:
        return self.texts[key]

    def put_text(self, key: str, content: str, content_type: str) -> None:
        del content_type
        self.texts[key] = content

    def put_bytes(self, key: str, content: bytes, content_type: str) -> None:
        del content_type
        self.bytes[key] = content

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


class FakeRepo:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict[str, object]] = {
            ("user-1", "job-1"): {"status": "uploaded", "metadata": {}}
        }
        self.completed: dict[str, object] | None = None
        self.cost: CostBreakdown | None = None
        self.rollups: list[tuple[str, str, CostBreakdown]] = []

    def get(self, owner_user_id: str, reading_id: str) -> dict[str, object] | None:
        return self.items.get((owner_user_id, reading_id))

    def mark_completed(
        self,
        owner_user_id: str,
        reading_id: str,
        corrected_text_key: str,
        recording_key: str,
        metadata: dict[str, object],
        timing_map_key: str,
        *,
        cost: CostBreakdown | None = None,
    ) -> None:
        self.cost = cost
        self.completed = {
            "owner_user_id": owner_user_id,
            "reading_id": reading_id,
            "corrected_text_key": corrected_text_key,
            "recording_key": recording_key,
            "timing_map_key": timing_map_key,
            "metadata": metadata,
        }
        item = self.items.setdefault((owner_user_id, reading_id), {})
        item.update({"status": "completed", "metadata": metadata})

    def add_cost_rollup(self, owner_user_id: str, month: str, cost: CostBreakdown) -> None:
        self.rollups.append((owner_user_id, month, cost))

    def set_status(
        self,
        owner_user_id: str,
        reading_id: str,
        status: str,
        metadata_patch: dict[str, object] | None = None,
    ) -> None:
        item = self.items.setdefault((owner_user_id, reading_id), {"metadata": {}})
        item["status"] = str(status)
        metadata = item.setdefault("metadata", {})
        if metadata_patch:
            assert isinstance(metadata, dict)
            metadata.update(metadata_patch)


async def fake_synthesize(
    text: str,
    output_path: str,
    _selection: TtsSelection,
    _settings: Settings | None = None,
) -> None:
    Path(output_path).write_bytes(f"mp3:{text}".encode())


async def failing_synthesize(*_args: object) -> None:
    raise RuntimeError("provider failed")


def test_completed_run_records_usage_cost_log_and_rollup(monkeypatch, caplog) -> None:
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", raising=False)
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
        "abbreviation_readings": [{"abbreviation": "PKP", "read_as": "pe ka pe"}],
    }
    storage = FakeStorage()
    original_text = "PKP jedzie."
    storage.texts[event["original_text_key"]] = original_text
    repo = FakeRepo()

    with caplog.at_level(logging.INFO, logger="app.processing"):
        result = asyncio.run(
            process_reading(
                event,
                Settings(readings_table_name="table", files_bucket_name="bucket"),
                storage,
                repo,
                fake_synthesize,
            )
        )

    assert result == {"status": "completed"}
    assert isinstance(repo.cost, CostBreakdown)
    assert repo.cost.total_usd_micros > 0
    assert repo.completed is not None
    metadata = repo.completed["metadata"]
    assert isinstance(metadata, dict)
    usage = metadata["cost_usage"]
    assert isinstance(usage, dict)
    corrected = storage.texts[storage.corrected_text_key("user-1", "job-1")]
    assert len(corrected) != len(original_text)
    assert usage["chars_synthesized"] == len(corrected)
    stages = usage["compute_ms_by_stage"]
    assert isinstance(stages, dict)
    assert {"normalize", "synthesize", "merge"} <= stages.keys()
    assert all(stages[stage] >= 0 for stage in ("normalize", "synthesize", "merge"))
    stored_bytes = sum(len(text.encode()) for text in storage.texts.values()) + sum(
        len(content) for content in storage.bytes.values()
    )
    assert usage["stored_bytes"] == stored_bytes > 0
    assert isinstance(usage["lambda_memory_mb"], int)
    assert usage["lambda_memory_mb"] > 0
    assert len(repo.rollups) == 1
    owner_user_id, month, rollup_cost = repo.rollups[0]
    assert owner_user_id == "user-1"
    assert re.fullmatch(r"\d{4}-\d{2}", month)
    assert rollup_cost == repo.cost
    cost_logs = [record for record in caplog.records if hasattr(record, "total_usd_micros")]
    assert len(cost_logs) == 1
    assert cost_logs[0].total_usd_micros == repo.cost.total_usd_micros


def test_processing_uses_lambda_memory_environment(monkeypatch) -> None:
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_MEMORY_SIZE", "1536")
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
    }
    repo = FakeRepo()

    result = asyncio.run(
        process_reading(
            event,
            Settings(readings_table_name="table", files_bucket_name="bucket"),
            FakeStorage(),
            repo,
            fake_synthesize,
        )
    )

    assert result == {"status": "completed"}
    assert repo.completed is not None
    metadata = repo.completed["metadata"]
    assert isinstance(metadata, dict)
    usage = metadata["cost_usage"]
    assert isinstance(usage, dict)
    assert usage["lambda_memory_mb"] == 1536


def test_synthesis_failure_records_no_cost_or_rollup() -> None:
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
    }
    repo = FakeRepo()

    with pytest.raises(RuntimeError, match="provider failed"):
        asyncio.run(
            process_reading(
                event,
                Settings(readings_table_name="table", files_bucket_name="bucket"),
                FakeStorage(),
                repo,
                failing_synthesize,
            )
        )

    assert repo.cost is None
    assert repo.rollups == []


def test_cost_failure_does_not_fail_completed_reading(monkeypatch) -> None:
    def fail_cost_calculation(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("cost calculation failed")

    monkeypatch.setattr("app.processing.estimate_cost", fail_cost_calculation)
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
    }
    repo = FakeRepo()

    result = asyncio.run(
        process_reading(
            event,
            Settings(readings_table_name="table", files_bucket_name="bucket"),
            FakeStorage(),
            repo,
            fake_synthesize,
        )
    )

    assert result == {"status": "completed"}
    assert repo.completed is not None
    assert repo.cost is None
    assert repo.rollups == []
