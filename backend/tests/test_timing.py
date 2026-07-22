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
        "duration": 1.0,
        "segments": [
            {
                "id": "s0001",
                "text": "Ja.",
                "start": 0.0,
                "end": 0.333,
                "paragraph": 0,
            },
            {
                "id": "s0002",
                "text": "Kotek.",
                "start": 0.333,
                "end": 1.0,
                "paragraph": 0,
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
    assert result["duration"] == 6.667
    assert [segment["id"] for segment in segments] == [
        "s0001",
        "s0002",
        "s0003",
        "s0004",
        "s0005",
        "s0006",
    ]
    assert [segment["paragraph"] for segment in segments] == [0, 0, 1, 2, 3, 3]
    assert [segment["text"] for segment in segments] == [
        "Pierwszy.",
        "Drugi.",
        "Trzeci.",
        "Czwarty.",
        "Piąty.",
        "Szósty.",
    ]
    assert segments[0]["start"] == 0.0
    assert segments[-1]["end"] == result["duration"]
    assert segments[2]["end"] == segments[3]["start"] == 2.346
    assert all(segment["start"] <= segment["end"] for segment in segments)
    assert all(
        current["start"] >= previous["end"]
        for previous, current in zip(segments, segments[1:])
    )
    assert all(
        isinstance(segment[value], float)
        for segment in segments
        for value in ("start", "end")
    )
    assert all(
        segment[value] == round(segment[value], 3)
        for segment in segments
        for value in ("start", "end")
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
        "s0001",
        "s0002",
        "s0003",
    ]
    assert result["segments"][0]["start"] == 0.0
    assert result["segments"][-1]["end"] == 9.0


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
