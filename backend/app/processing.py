import asyncio
import logging
from pathlib import Path
from typing import Any

from app.audio import merge_mp3_files
from app.config import Settings, get_settings
from app.models import ReadingStatus
from app.normalization import RULE_BASED_NORMALIZATION_VERSION, apply_abbreviation_readings, ai_normalize, normalize
from app.repositories.readings import ReadingRepository
from app.splitting import split_text
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
    pairs = event.get("abbreviation_readings")
    selection = resolve_tts_selection(event.get("vendor"), event.get("voice"))
    current_stage = ReadingStatus.NORMALIZING

    existing = repo.get(owner_user_id, reading_id)
    try:
        if existing and existing.get("status") in TERMINAL_READING_STATUSES:
            return {"status": str(existing["status"])}

        ensure_tts_provider_available(selection, settings)
        original_text = storage.get_text(original_text_key)
        provider = validate_tts_input(original_text, selection)
        repo.set_status(owner_user_id, reading_id, current_stage)
        try:
            corrected = normalize(original_text)
            normalization_status = RULE_BASED_NORMALIZATION_VERSION
        except Exception:
            logger.exception(
                "text normalization failed",
                extra={"reading_id": reading_id, "owner_user_id": owner_user_id},
            )
            corrected = original_text
            normalization_status = "failed"

        if settings.ai_normalization_enabled and normalization_status != "failed":
            try:
                corrected = await ai_normalize(corrected)
            except Exception:
                logger.exception(
                    "AI text normalization failed",
                    extra={"reading_id": reading_id, "owner_user_id": owner_user_id},
                )

        corrected = apply_abbreviation_readings(corrected, pairs)
        corrected_text_key = storage.corrected_text_key(owner_user_id, reading_id)
        recording_key = storage.recording_key(owner_user_id, reading_id, provider.output_extension)
        recording_path = Path("/tmp") / f"{reading_id}.{provider.output_extension}"
        chunks = split_text(corrected, settings.max_chunk_chars)

        logger.info(
            "processing reading",
            extra={
                "reading_id": reading_id,
                "owner_user_id": owner_user_id,
                "vendor": selection.vendor,
                "voice": selection.voice,
            },
        )

        storage.put_text(corrected_text_key, corrected, "text/markdown; charset=utf-8")
        chunk_paths = [
            Path("/tmp") / f"{reading_id}-{chunk.index:04d}.mp3" for chunk in chunks
        ]
        current_stage = ReadingStatus.GENERATING_AUDIO
        repo.set_status(owner_user_id, reading_id, current_stage)
        for chunk, chunk_path in zip(chunks, chunk_paths, strict=True):
            await synthesize(chunk.text, str(chunk_path), selection, settings)
        current_stage = ReadingStatus.MERGING_AUDIO
        repo.set_status(owner_user_id, reading_id, current_stage)
        merge_mp3_files(chunk_paths, recording_path)
        storage.put_bytes(recording_key, recording_path.read_bytes(), provider.content_type)

        metadata = {
            **tts_metadata(selection),
            "normalization": normalization_status,
            "chunks": len(chunks),
            "merge": "byte-concat-v1",
        }
        repo.mark_completed(
            owner_user_id,
            reading_id,
            corrected_text_key,
            recording_key,
            metadata,
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
            repo.set_status(
                owner_user_id,
                reading_id,
                ReadingStatus.FAILED,
                {"failed_stage": current_stage.value, "error": str(exc)[:500]},
            )
        except Exception:
            logger.exception(
                "failed to mark reading failed",
                extra={"reading_id": reading_id, "owner_user_id": owner_user_id},
            )
        raise
    finally:
        for temporary_path in Path("/tmp").glob(f"{reading_id}*"):
            temporary_path.unlink(missing_ok=True)


def handler(event: dict[str, Any], _context: Any) -> dict[str, str]:
    return asyncio.run(process_reading(event))
