import asyncio
import logging
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.repositories.readings import ReadingRepository
from app.storage import FileStorage
from app.tts import (
    ensure_tts_provider_available,
    resolve_tts_selection,
    synthesize_to_file,
    tts_metadata,
    validate_tts_input,
)


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TERMINAL_READING_STATUSES = {"completed", "failed"}


async def process_reading(
    event: dict[str, Any],
    settings: Settings | None = None,
    storage: FileStorage | None = None,
    repo: ReadingRepository | None = None,
    synthesize=synthesize_to_file,
) -> dict[str, str]:
    settings = settings or get_settings()
    storage = storage or FileStorage(settings.files_bucket_name)
    repo = repo or ReadingRepository(settings.readings_table_name, None)

    reading_id = str(event["reading_id"])
    owner_user_id = str(event["owner_user_id"])
    original_text_key = str(event["original_text_key"])
    selection = resolve_tts_selection(event.get("vendor"), event.get("voice"))
    recording_path: Path | None = None

    existing = repo.get(owner_user_id, reading_id)
    if existing and existing.get("status") in TERMINAL_READING_STATUSES:
        return {"status": str(existing["status"])}

    try:
        ensure_tts_provider_available(selection, settings)
        original_text = storage.get_text(original_text_key)
        provider = validate_tts_input(original_text, selection)
        corrected_text_key = storage.corrected_text_key(owner_user_id, reading_id)
        recording_key = storage.recording_key(owner_user_id, reading_id, provider.output_extension)
        recording_path = Path("/tmp") / f"{reading_id}.{provider.output_extension}"

        logger.info(
            "processing reading",
            extra={
                "reading_id": reading_id,
                "owner_user_id": owner_user_id,
                "vendor": selection.vendor,
                "voice": selection.voice,
            },
        )

        storage.put_text(corrected_text_key, original_text, "text/markdown; charset=utf-8")
        await synthesize(original_text, str(recording_path), selection, settings)
        storage.put_bytes(recording_key, recording_path.read_bytes(), provider.content_type)

        repo.mark_completed(
            owner_user_id,
            reading_id,
            corrected_text_key,
            recording_key,
            tts_metadata(selection),
        )
        return {"status": "completed"}
    except Exception as exc:
        logger.exception(
            "reading processing failed",
            extra={
                "reading_id": reading_id,
                "owner_user_id": owner_user_id,
                "vendor": selection.vendor,
            },
        )
        try:
            repo.mark_failed(owner_user_id, reading_id, {"processing_error": type(exc).__name__})
        except Exception:
            logger.exception(
                "failed to mark reading failed",
                extra={"reading_id": reading_id, "owner_user_id": owner_user_id},
            )
        return {"status": "failed"}
    finally:
        if recording_path:
            recording_path.unlink(missing_ok=True)


def handler(event: dict[str, Any], _context: Any) -> dict[str, str]:
    return asyncio.run(process_reading(event))
