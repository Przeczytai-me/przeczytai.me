from pathlib import Path

import pytest

from app.audio import mp3_duration_seconds
from app.splitting import Chunk, split_sentences
from app.timing import build_timing_map


def chunk(index: int, text: str) -> Chunk:
    return Chunk(index=index, text=text, char_count=len(text))


def test_build_timing_map_allocates_chunk_duration_by_sentence_length() -> None:
    """Allocate a chunk duration proportionally and pin its final boundary."""
    result = build_timing_map([chunk(0, "Ja. Kotek.")], [1.0])

    assert result == {
        "version": 1,
        "duration_ms": 1000,
        "segments": [
            {
                "id": "segment-1",
                "text": "Ja.",
                "paragraph_index": 0,
                "start_ms": 0,
                "end_ms": 333,
            },
            {
                "id": "segment-2",
                "text": "Kotek.",
                "paragraph_index": 0,
                "start_ms": 333,
                "end_ms": 1000,
            },
        ],
    }


def test_build_timing_map_preserves_global_order_and_paragraph_indices() -> None:
    """Keep segment ids, time ranges, and paragraph numbers global across chunks."""
    chunks = [
        chunk(0, "Pierwszy. Drugi.\n\nTrzeci."),
        chunk(1, "Czwarty.\n\nPiąty. Szósty."),
    ]

    result = build_timing_map(chunks, [2.3456, 4.3214])
    segments = result["segments"]

    assert result["version"] == 1
    assert result["duration_ms"] == 6667
    assert [segment["id"] for segment in segments] == [
        "segment-1",
        "segment-2",
        "segment-3",
        "segment-4",
        "segment-5",
        "segment-6",
    ]
    assert [segment["paragraph_index"] for segment in segments] == [0, 0, 1, 2, 3, 3]
    assert [segment["text"] for segment in segments] == [
        "Pierwszy.",
        "Drugi.",
        "Trzeci.",
        "Czwarty.",
        "Piąty.",
        "Szósty.",
    ]
    assert segments[0]["start_ms"] == 0
    assert segments[-1]["end_ms"] == result["duration_ms"]
    assert segments[2]["end_ms"] == segments[3]["start_ms"] == 2346
    assert all(segment["start_ms"] <= segment["end_ms"] for segment in segments)
    assert all(
        current["start_ms"] == previous["end_ms"]
        for previous, current in zip(segments, segments[1:])
    )
    assert all(
        isinstance(segment[value], int)
        for segment in segments
        for value in ("start_ms", "end_ms")
    )


@pytest.mark.parametrize(
    ("chunks", "durations"),
    [
        ([chunk(0, "Pierwszy.")], []),
        ([chunk(0, "Pierwszy.")], [1.0, 2.0]),
    ],
)
def test_build_timing_map_rejects_length_mismatch(
    chunks: list[Chunk], durations: list[float]
) -> None:
    """Reject duration lists that do not align one-to-one with chunks."""
    with pytest.raises(ValueError):
        build_timing_map(chunks, durations)


def test_build_timing_map_uses_polish_abbreviation_sentence_rules() -> None:
    """Do not split protected Polish abbreviations into separate segments."""
    text = "Np. Ala czyta. Prof. Kowalski słucha. Koniec."
    expected = ["Np. Ala czyta.", "Prof. Kowalski słucha.", "Koniec."]

    assert split_sentences(text) == expected
    result = build_timing_map([chunk(0, text)], [9.0])

    assert [segment["text"] for segment in result["segments"]] == expected
    assert [segment["id"] for segment in result["segments"]] == [
        "segment-1",
        "segment-2",
        "segment-3",
    ]
    assert result["segments"][0]["start_ms"] == 0
    assert result["segments"][-1]["end_ms"] == 9000


def test_mp3_duration_seconds_returns_mutagen_info_length(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Read the exact MP3 duration reported by mutagen."""
    path = Path("/tmp/chunk.mp3")
    calls: list[Path] = []

    class FakeMp3:
        def __init__(self, received_path: Path) -> None:
            calls.append(received_path)
            self.info = type("Info", (), {"length": 12.375})()

    monkeypatch.setattr("app.audio.MP3", FakeMp3)

    assert mp3_duration_seconds(path) == 12.375
    assert calls == [path]
