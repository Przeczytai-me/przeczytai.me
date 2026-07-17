import asyncio
from pathlib import Path

from app.config import Settings
from app.processing import process_reading
from app.tts import DEFAULT_TTS_VENDOR, EDGE_TTS_VOICE, OPENAI_TTS_MODEL, TtsSelection


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

    def corrected_text_key(self, owner_user_id: str, reading_id: str) -> str:
        return f"users/{owner_user_id}/readings/{reading_id}/corrected.md"

    def recording_key(self, owner_user_id: str, reading_id: str, extension: str = "mp3") -> str:
        return f"users/{owner_user_id}/readings/{reading_id}/recording.{extension}"


class FakeRepo:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict[str, object]] = {
            ("user-1", "job-1"): {"status": "processing"}
        }
        self.completed: dict[str, object] | None = None
        self.failed: dict[str, object] | None = None

    def get(self, owner_user_id: str, reading_id: str) -> dict[str, object] | None:
        return self.items.get((owner_user_id, reading_id))

    def mark_completed(
        self,
        owner_user_id: str,
        reading_id: str,
        corrected_text_key: str,
        recording_key: str,
        metadata: dict[str, object],
    ) -> None:
        self.completed = {
            "owner_user_id": owner_user_id,
            "reading_id": reading_id,
            "corrected_text_key": corrected_text_key,
            "recording_key": recording_key,
            "metadata": metadata,
        }
        self.items[(owner_user_id, reading_id)] = {"status": "completed"}

    def mark_failed(
        self,
        owner_user_id: str,
        reading_id: str,
        metadata: dict[str, object],
    ) -> None:
        self.failed = {
            "owner_user_id": owner_user_id,
            "reading_id": reading_id,
            "metadata": metadata,
        }
        self.items[(owner_user_id, reading_id)] = {"status": "failed"}


async def fake_synthesize(
    text: str,
    output_path: str,
    selection: TtsSelection,
    _settings: Settings | None = None,
) -> None:
    Path(output_path).write_bytes(f"mp3:{selection.vendor}:{selection.voice}:{text}".encode())


async def failing_synthesize(*_args: object) -> None:
    raise RuntimeError("provider failed")


def test_processing_generates_same_text_and_recording() -> None:
    """Generate corrected text, MP3 bytes, and mark the reading completed."""
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
    }
    storage = FakeStorage()
    repo = FakeRepo()

    result = asyncio.run(
        process_reading(
            event,
            Settings(readings_table_name="table", files_bucket_name="bucket"),
            storage,
            repo,
            fake_synthesize,
        )
    )

    corrected_text_key = "users/user-1/readings/job-1/corrected.md"
    recording_key = "users/user-1/readings/job-1/recording.mp3"
    assert result == {"status": "completed"}
    assert storage.texts[corrected_text_key] == "Ala ma kota."
    assert storage.bytes[recording_key] == b"mp3:edge-tts:pl-PL-ZofiaNeural:Ala ma kota."
    assert repo.completed == {
        "owner_user_id": "user-1",
        "reading_id": "job-1",
        "corrected_text_key": corrected_text_key,
        "recording_key": recording_key,
        "metadata": {
            "processor": DEFAULT_TTS_VENDOR,
            "voice": EDGE_TTS_VOICE,
            "normalization": "regex-v1",
        },
    }


def test_processing_uses_requested_voice() -> None:
    """Generate the recording with the selected voice from the event."""
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
        "vendor": "edge-tts",
        "voice": "Emma",
    }
    storage = FakeStorage()
    repo = FakeRepo()

    asyncio.run(
        process_reading(
            event,
            Settings(readings_table_name="table", files_bucket_name="bucket"),
            storage,
            repo,
            fake_synthesize,
        )
    )

    assert storage.bytes["users/user-1/readings/job-1/recording.mp3"] == (
        b"mp3:edge-tts:en-US-EmmaMultilingualNeural:Ala ma kota."
    )
    assert repo.completed is not None
    assert repo.completed["metadata"] == {
        "processor": DEFAULT_TTS_VENDOR,
        "voice": "en-US-EmmaMultilingualNeural",
        "normalization": "regex-v1",
    }


def test_processing_uses_requested_openai_vendor() -> None:
    """Generate the recording with the selected OpenAI provider."""
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
        "vendor": "openai",
        "voice": "coral",
    }
    storage = FakeStorage()
    repo = FakeRepo()

    asyncio.run(
        process_reading(
            event,
            Settings(
                readings_table_name="table",
                files_bucket_name="bucket",
                openai_tts_enabled=True,
            ),
            storage,
            repo,
            fake_synthesize,
        )
    )

    assert storage.bytes["users/user-1/readings/job-1/recording.mp3"] == (
        b"mp3:openai:coral:Ala ma kota."
    )
    assert repo.completed is not None
    assert repo.completed["metadata"] == {
        "processor": "openai",
        "voice": "coral",
        "model": OPENAI_TTS_MODEL,
        "normalization": "regex-v1",
    }


def test_processing_marks_failed_when_synthesis_fails() -> None:
    """Record a terminal failure instead of letting async Lambda retry paid work."""
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
        "vendor": "openai",
        "voice": "coral",
    }
    storage = FakeStorage()
    repo = FakeRepo()

    result = asyncio.run(
        process_reading(
            event,
            Settings(
                readings_table_name="table",
                files_bucket_name="bucket",
                openai_tts_enabled=True,
            ),
            storage,
            repo,
            failing_synthesize,
        )
    )

    assert result == {"status": "failed"}
    assert repo.failed == {
        "owner_user_id": "user-1",
        "reading_id": "job-1",
        "metadata": {"processing_error": "RuntimeError"},
    }
    assert repo.completed is None


def test_processing_normalizes_dirty_text() -> None:
    from app.normalization import normalize as real_normalize

    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
    }
    storage = FakeStorage()
    original_text = "  Np.  Ala\tma kota!!!  "
    storage.texts[event["original_text_key"]] = original_text
    repo = FakeRepo()

    result = asyncio.run(
        process_reading(
            event,
            Settings(readings_table_name="table", files_bucket_name="bucket"),
            storage,
            repo,
            fake_synthesize,
        )
    )

    expected = real_normalize(original_text)
    corrected_text_key = storage.corrected_text_key("user-1", "job-1")
    recording_key = storage.recording_key("user-1", "job-1")
    assert result == {"status": "completed"}
    assert storage.texts[corrected_text_key] != original_text
    assert storage.texts[corrected_text_key] == expected
    assert storage.bytes[recording_key].endswith(expected.encode())
    assert repo.completed is not None
    assert repo.completed["metadata"]["normalization"] == "regex-v1"


def test_processing_falls_back_when_normalize_raises(monkeypatch) -> None:
    def raise_normalization_error(_text: str) -> str:
        raise RuntimeError("normalization failed")

    monkeypatch.setattr("app.processing.normalize", raise_normalization_error)
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
    }
    storage = FakeStorage()
    original_text = "  Nie zmieniaj mnie!!!  "
    storage.texts[event["original_text_key"]] = original_text
    repo = FakeRepo()

    result = asyncio.run(
        process_reading(
            event,
            Settings(readings_table_name="table", files_bucket_name="bucket"),
            storage,
            repo,
            fake_synthesize,
        )
    )

    corrected_text_key = storage.corrected_text_key("user-1", "job-1")
    recording_key = storage.recording_key("user-1", "job-1")
    assert result == {"status": "completed"}
    assert storage.texts[corrected_text_key] == original_text
    assert storage.bytes[recording_key].endswith(original_text.encode())
    assert repo.completed is not None
    assert repo.completed["metadata"]["normalization"] == "failed"


def test_processing_routes_through_ai_normalize_when_enabled(monkeypatch) -> None:
    async def add_ai_marker(text: str) -> str:
        return f"{text} [AI]"

    monkeypatch.setattr("app.processing.ai_normalize", add_ai_marker)
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
    }
    storage = FakeStorage()
    repo = FakeRepo()

    result = asyncio.run(
        process_reading(
            event,
            Settings(
                readings_table_name="table",
                files_bucket_name="bucket",
                ai_normalization_enabled=True,
            ),
            storage,
            repo,
            fake_synthesize,
        )
    )

    expected = "Ala ma kota. [AI]"
    corrected_text_key = storage.corrected_text_key("user-1", "job-1")
    recording_key = storage.recording_key("user-1", "job-1")
    assert result == {"status": "completed"}
    assert storage.texts[corrected_text_key] == expected
    assert storage.bytes[recording_key].endswith(expected.encode())


def test_processing_falls_back_to_regex_when_ai_normalize_raises(monkeypatch) -> None:
    async def failing_ai_normalize(_text: str) -> str:
        raise RuntimeError("ai provider failed")

    monkeypatch.setattr("app.processing.ai_normalize", failing_ai_normalize)
    event = {
        "reading_id": "job-1",
        "owner_user_id": "user-1",
        "original_text_key": "users/user-1/readings/job-1/original.txt",
    }
    storage = FakeStorage()
    repo = FakeRepo()

    result = asyncio.run(
        process_reading(
            event,
            Settings(
                readings_table_name="table",
                files_bucket_name="bucket",
                ai_normalization_enabled=True,
            ),
            storage,
            repo,
            fake_synthesize,
        )
    )

    corrected_text_key = storage.corrected_text_key("user-1", "job-1")
    assert result == {"status": "completed"}
    assert storage.texts[corrected_text_key] == "Ala ma kota."
    assert repo.completed is not None
    assert repo.completed["metadata"]["normalization"] == "regex-v1"
