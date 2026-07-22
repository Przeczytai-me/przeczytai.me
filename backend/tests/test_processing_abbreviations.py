import asyncio
from pathlib import Path

from app.config import Settings
from app.processing import process_reading
from app.tts import TtsSelection
from test_processing import FakeRepo, FakeStorage


def run_processing(
    event: dict[str, object],
    storage: FakeStorage,
    repo: FakeRepo,
    synthesized_texts: list[str],
    settings: Settings | None = None,
) -> dict[str, str]:
    async def recording_synthesize(
        text: str,
        output_path: str,
        _selection: TtsSelection,
        _settings: Settings | None = None,
    ) -> None:
        synthesized_texts.append(text)
        Path(output_path).write_bytes(b"audio")

    return asyncio.run(
        process_reading(
            event,
            settings or Settings(readings_table_name="table", files_bucket_name="bucket"),
            storage,
            repo,
            recording_synthesize,
        )
    )


def test_processing_applies_abbreviations_after_normalize_and_before_storage_and_tts() -> None:
    """Store and synthesize custom expansions applied after regex normalization."""
    original_key = "users/user-1/readings/job-1/original.txt"
    original_text = "Np. jadę PKP."
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": original_key,
        "abbreviation_readings": [
            {"abbreviation": "Na przykład", "read_as": "Przykładowo"},
            {"abbreviation": "PKP", "read_as": "Pe Ka Pe"},
        ],
    }
    storage = FakeStorage()
    storage.texts[original_key] = original_text
    repo = FakeRepo()
    synthesized_texts: list[str] = []

    result = run_processing(event, storage, repo, synthesized_texts)

    corrected_key = storage.corrected_text_key("user-1", "job-1")
    expected = "Przykładowo jadę Pe Ka Pe."
    assert result == {"status": "completed"}
    assert storage.texts[original_key] == original_text
    assert storage.texts[corrected_key] == expected
    assert synthesized_texts == [expected]


def test_processing_applies_abbreviations_after_ai_normalize(monkeypatch) -> None:
    """Apply custom expansions to text returned by the optional AI normalization pass."""
    async def add_abbreviation(text: str) -> str:
        return f"{text} PKP."

    monkeypatch.setattr("app.processing.ai_normalize", add_abbreviation)
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
        "abbreviation_readings": [
            {"abbreviation": "PKP", "read_as": "Pe Ka Pe"},
        ],
    }
    storage = FakeStorage()
    repo = FakeRepo()
    synthesized_texts: list[str] = []
    settings = Settings(
        readings_table_name="table",
        files_bucket_name="bucket",
        ai_normalization_enabled=True,
    )

    result = run_processing(event, storage, repo, synthesized_texts, settings)

    corrected_key = storage.corrected_text_key("user-1", "job-1")
    expected = "Ala ma kota. Pe Ka Pe."
    assert result == {"status": "completed"}
    assert storage.texts[corrected_key] == expected
    assert synthesized_texts == [expected]


def test_processing_without_abbreviation_key_preserves_legacy_behavior() -> None:
    """Leave corrected and synthesized text unchanged for a legacy event."""
    original_key = "users/user-1/readings/job-1/original.txt"
    original_text = "Kod PKP pozostaje."
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": original_key,
    }
    storage = FakeStorage()
    storage.texts[original_key] = original_text
    repo = FakeRepo()
    synthesized_texts: list[str] = []

    result = run_processing(event, storage, repo, synthesized_texts)

    corrected_key = storage.corrected_text_key("user-1", "job-1")
    assert result == {"status": "completed"}
    assert storage.texts[original_key] == original_text
    assert storage.texts[corrected_key] == original_text
    assert synthesized_texts == [original_text]
