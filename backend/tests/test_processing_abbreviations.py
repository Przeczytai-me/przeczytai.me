import asyncio
from pathlib import Path

import pytest

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


@pytest.mark.parametrize(
    ("original_text", "abbreviation", "read_as", "expected"),
    [
        ("Np. Ala ma kota.", "Np.", "en pe", "en pe Ala ma kota."),
        ("To m.in. działa.", "m.in.", "em in", "To em in działa."),
    ],
)
def test_processing_applies_custom_pairs_before_rule_based_normalization(
    original_text: str,
    abbreviation: str,
    read_as: str,
    expected: str,
) -> None:
    """Apply a custom pair to original text before rule-based normalization runs."""
    original_key = "users/user-1/readings/job-1/original.txt"
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": original_key,
        "abbreviation_readings": [
            {"abbreviation": abbreviation, "read_as": read_as},
        ],
    }
    storage = FakeStorage()
    storage.texts[original_key] = original_text
    repo = FakeRepo()
    synthesized_texts: list[str] = []

    result = run_processing(event, storage, repo, synthesized_texts)

    corrected_key = storage.corrected_text_key("user-1", "job-1")
    corrected = storage.texts[corrected_key]
    assert result == {"status": "completed"}
    assert storage.texts[original_key] == original_text
    assert corrected == expected
    assert synthesized_texts == [corrected]


def test_processing_custom_pair_for_non_builtin_abbreviation_still_works() -> None:
    """Apply custom pairs even when normalization has no built-in rule for them."""
    original_key = "users/user-1/readings/job-1/original.txt"
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": original_key,
        "abbreviation_readings": [{"abbreviation": "PKP", "read_as": "Pe Ka Pe"}],
    }
    storage = FakeStorage()
    storage.texts[original_key] = "Jadę PKP."
    repo = FakeRepo()
    synthesized_texts: list[str] = []

    result = run_processing(event, storage, repo, synthesized_texts)

    corrected_key = storage.corrected_text_key("user-1", "job-1")
    assert result == {"status": "completed"}
    assert storage.texts[corrected_key] == "Jadę Pe Ka Pe."
    assert synthesized_texts == ["Jadę Pe Ka Pe."]


def test_processing_applies_pairs_before_optional_ai_normalize(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pass custom-expanded and regex-normalized text into optional AI normalization."""
    ai_inputs: list[str] = []

    async def add_abbreviation(text: str) -> str:
        ai_inputs.append(text)
        return f"{text} PKP."

    monkeypatch.setattr("app.processing.ai_normalize", add_abbreviation)
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
        "abbreviation_readings": [
            {"abbreviation": "Np.", "read_as": "en pe"},
            {"abbreviation": "PKP", "read_as": "Pe Ka Pe"},
        ],
    }
    storage = FakeStorage()
    storage.texts[event["original_text_key"]] = "Np. Ala ma kota."
    repo = FakeRepo()
    synthesized_texts: list[str] = []
    settings = Settings(
        readings_table_name="table",
        files_bucket_name="bucket",
        ai_normalization_enabled=True,
    )

    result = run_processing(event, storage, repo, synthesized_texts, settings)

    corrected_key = storage.corrected_text_key("user-1", "job-1")
    expected = "en pe Ala ma kota. PKP."
    assert result == {"status": "completed"}
    assert ai_inputs == ["en pe Ala ma kota."]
    assert storage.texts[corrected_key] == expected
    assert synthesized_texts == [expected]


def test_processing_without_abbreviation_key_preserves_current_behavior() -> None:
    """Leave corrected and synthesized text unchanged when no custom pairs are provided."""
    original_key = "users/user-1/readings/job-1/original.txt"
    original_text = "Np. Kod PKP pozostaje."
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
    expected = original_text
    assert result == {"status": "completed"}
    assert storage.texts[original_key] == original_text
    assert storage.texts[corrected_key] == expected
    assert synthesized_texts == [expected]
