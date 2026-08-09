import asyncio
from pathlib import Path

import pytest
from test_processing import FakeRepo, FakeStorage

from app.config import Settings
from app.processing import process_reading
from app.proofreading import PROOFREADING_MODEL, PROOFREADING_PROMPT_VERSION, ProofreadingResult
from app.tts import TtsSelection


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
def test_processing_applies_custom_pairs_in_deterministic_stage(
    original_text: str,
    abbreviation: str,
    read_as: str,
    expected: str,
) -> None:
    """Apply custom pronunciation pairs after optional AI proofreading."""
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


def test_processing_applies_pairs_after_optional_ai_proofreading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Proofread raw source before applying deterministic abbreviation readings."""
    proofreading_inputs: list[str] = []

    async def correct_text(text: str, _settings: Settings) -> ProofreadingResult:
        proofreading_inputs.append(text)
        return ProofreadingResult(
            text="Np. Ala ma kota.",
            model=PROOFREADING_MODEL,
            prompt_version=PROOFREADING_PROMPT_VERSION,
        )

    monkeypatch.setattr("app.processing.proofread_text", correct_text)
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
    storage.texts[event["original_text_key"]] = "Np. Ala ma kotta."
    repo = FakeRepo()
    synthesized_texts: list[str] = []
    settings = Settings(
        readings_table_name="table",
        files_bucket_name="bucket",
        ai_normalization_enabled=True,
    )

    result = run_processing(event, storage, repo, synthesized_texts, settings)

    corrected_key = storage.corrected_text_key("user-1", "job-1")
    expected = "en pe Ala ma kota."
    assert result == {"status": "completed"}
    assert proofreading_inputs == ["Np. Ala ma kotta."]
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
