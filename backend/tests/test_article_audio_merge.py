"""Opt-in listening test for TTS chunk boundaries in a full article.

How to run this test:
Edge:
    RUN_ARTICLE_AUDIO_MERGE_TEST=1 .venv/bin/pytest -s tests/test_article_audio_merge.py

OpenAI:
    RUN_ARTICLE_AUDIO_MERGE_TEST=1 \
    ARTICLE_TTS_VENDOR=openai \
    ARTICLE_TTS_VOICE=coral \
    .venv/bin/pytest -s tests/test_article_audio_merge.py
"""

import asyncio
import json
import os
from pathlib import Path

import pytest
from mutagen.mp3 import MP3

from app.audio import merge_mp3_files
from app.config import Settings
from app.normalization import normalize
from app.splitting import Chunk, split_text
from app.tts import resolve_tts_selection, synthesize_to_file


BACKEND_DIR = Path(__file__).resolve().parents[1]
ARTICLE_PATH = Path(__file__).parent / "fixtures" / "article.md"
OUTPUT_DIR = BACKEND_DIR.parent / "tested_assets" / "article-audio-merge"


def _mp3_duration_seconds(path: Path) -> float:
    return MP3(path).info.length


def _seam_report(chunks: list[Chunk], durations: list[float]) -> list[dict[str, object]]:
    elapsed = 0.0
    seams: list[dict[str, object]] = []
    for index, duration in enumerate(durations[:-1]):
        elapsed += duration
        seams.append(
            {
                "after_chunk": index,
                "at_seconds": round(elapsed, 3),
                "text_before": chunks[index].text[-120:],
                "text_after": chunks[index + 1].text[:120],
            }
        )
    return seams


async def _synthesize_chunks(
    chunks: list[Chunk],
    paths: list[Path],
    settings: Settings,
    vendor: str,
    voice: str | None,
) -> None:
    selection = resolve_tts_selection(vendor, voice)
    for chunk, path in zip(chunks, paths, strict=True):
        await synthesize_to_file(chunk.text, str(path), selection, settings)


@pytest.mark.skipif(
    os.getenv("RUN_ARTICLE_AUDIO_MERGE_TEST") != "1",
    reason=(
        "Paste an article into tests/fixtures/article.md and set "
        "RUN_ARTICLE_AUDIO_MERGE_TEST=1 to run this network TTS listening test."
    ),
)
def test_article_chunks_are_merged_into_listenable_audio() -> None:
    """Generate a real recording and report every seam for manual listening."""
    article = ARTICLE_PATH.read_text(encoding="utf-8").strip()
    assert article, f"Paste the article to test into {ARTICLE_PATH}"

    settings = Settings(_env_file=BACKEND_DIR / ".env")
    normalized_article = normalize(article)
    default_chunk_chars = min(
        settings.max_chunk_chars,
        max(1, len(normalized_article) // 2),
    )
    max_chunk_chars = int(os.getenv("ARTICLE_AUDIO_MAX_CHUNK_CHARS", str(default_chunk_chars)))
    chunks = split_text(normalized_article, max_chunk_chars=max_chunk_chars)
    assert len(chunks) >= 2, (
        "This test needs at least two chunks to exercise a merge; paste a longer article "
        "or lower ARTICLE_AUDIO_MAX_CHUNK_CHARS."
    )

    vendor = os.getenv("ARTICLE_TTS_VENDOR", "edge-tts")
    voice = os.getenv("ARTICLE_TTS_VOICE")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    chunk_paths = [OUTPUT_DIR / f"chunk-{chunk.index:04d}.mp3" for chunk in chunks]
    merged_path = OUTPUT_DIR / "article-merged.mp3"
    report_path = OUTPUT_DIR / "seams.json"

    asyncio.run(_synthesize_chunks(chunks, chunk_paths, settings, vendor, voice))

    durations = [_mp3_duration_seconds(path) for path in chunk_paths]
    merge_mp3_files(chunk_paths, merged_path)
    merged_duration = _mp3_duration_seconds(merged_path)
    expected_duration = sum(durations)
    duration_tolerance = max(0.5, len(chunks) * 0.2)

    report = {
        "article": str(ARTICLE_PATH),
        "audio": str(merged_path),
        "vendor": vendor,
        "voice": voice or "provider default",
        "max_chunk_chars": max_chunk_chars,
        "chunks": len(chunks),
        "merged_duration_seconds": round(merged_duration, 3),
        "seams": _seam_report(chunks, durations),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    assert merged_path.read_bytes() == b"".join(path.read_bytes() for path in chunk_paths)
    assert merged_duration == pytest.approx(expected_duration, abs=duration_tolerance)

    print(f"\nListen to: {merged_path}")
    print(f"Seam timestamps: {report_path}")
