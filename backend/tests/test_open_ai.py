import asyncio
import os
from pathlib import Path

import pytest

from app.config import Settings
from app.tts import resolve_tts_selection, synthesize_to_file


BACKEND_DIR = Path(__file__).resolve().parents[1]
TESTED_ASSETS_DIR = BACKEND_DIR.parent / "tested_assets"


@pytest.mark.skipif(
    os.getenv("RUN_OPENAI_TTS_TESTS") != "1",
    reason="Set RUN_OPENAI_TTS_TESTS=1 to run the paid OpenAI TTS test.",
)
def test_openai_tts_generates_mp3() -> None:
    """Call the real OpenAI TTS provider and write a non-empty MP3 file."""
    TESTED_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TESTED_ASSETS_DIR / "openai-tts-smoke.mp3"
    settings = Settings(_env_file=BACKEND_DIR / ".env")
    selection = resolve_tts_selection("openai", "coral")

    asyncio.run(
        synthesize_to_file(
            "Ala ma kota.",
            str(output_path),
            selection,
            settings,
        )
    )

    assert output_path.is_file()
    assert output_path.stat().st_size > 0
