import asyncio
import json
import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.audio import merge_mp3_files, mp3_duration_seconds
from app.config import Settings, get_settings
from app.costs import CostBreakdown, RunUsage, estimate_cost
from app.models import ReadingStatus
from app.normalization import (
    RULE_BASED_NORMALIZATION_VERSION,
    ai_normalize,
    apply_abbreviation_readings,
    normalize,
)
from app.pricing import get_prices
from app.repositories.readings import ReadingRepository
from app.splitting import split_text
from app.storage import FileStorage
from app.timing import build_timing_map
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
TERMINAL_JOB_STATUSES = {"completed", "failed", "failed_to_start"}
JOB_FAILURE_MESSAGES = {
    ReadingStatus.NORMALIZING: "Text normalization failed",
    ReadingStatus.GENERATING_AUDIO: "Audio generation failed",
    ReadingStatus.MERGING_AUDIO: "Audio merging failed",
}


async def process_reading(
    event: dict[str, Any],
    settings: Settings | None = None,
    storage: FileStorage | None = None,
    repo: ReadingRepository | None = None,
    synthesize=synthesize_to_file,
) -> dict[str, str]:
    invocation_started = time.perf_counter()
    settings = settings or get_settings()
    storage = storage or FileStorage(settings.files_bucket_name)
    repo = repo or ReadingRepository(settings.readings_table_name, None)

    reading_id = str(event["reading_id"])
    job_id = event.get("job_id")
    owner_user_id = str(event["owner_user_id"])
    original_text_key = str(event["original_text_key"])
    pairs = event.get("abbreviation_readings")
    current_stage = ReadingStatus.NORMALIZING

    try:
        if job_id:
            existing_job = repo.get_job(owner_user_id, str(job_id))
            if existing_job and existing_job.get("status") in TERMINAL_JOB_STATUSES:
                return {"status": str(existing_job["status"])}
        else:
            existing = repo.get(owner_user_id, reading_id)
            if existing and existing.get("status") in TERMINAL_READING_STATUSES:
                return {"status": str(existing["status"])}

        selection = resolve_tts_selection(event.get("vendor"), event.get("voice"))
        ensure_tts_provider_available(selection, settings)
        original_text = storage.get_text(original_text_key)
        provider = validate_tts_input(original_text, selection)
        repo.set_status(owner_user_id, reading_id, current_stage)
        if job_id:
            repo.set_job_status(owner_user_id, str(job_id), current_stage)
        normalize_started = time.perf_counter()
        corrected = apply_abbreviation_readings(original_text, pairs)
        try:
            corrected = normalize(corrected)
            normalization_status = RULE_BASED_NORMALIZATION_VERSION
        except Exception:
            logger.exception(
                "text normalization failed",
                extra={"reading_id": reading_id, "owner_user_id": owner_user_id},
            )
            normalization_status = "failed"

        if settings.ai_normalization_enabled and normalization_status != "failed":
            try:
                corrected = await ai_normalize(corrected)
            except Exception:
                logger.exception(
                    "AI text normalization failed",
                    extra={"reading_id": reading_id, "owner_user_id": owner_user_id},
                )
        normalize_ms = round((time.perf_counter() - normalize_started) * 1000)

        corrected_text_key = storage.corrected_text_key(owner_user_id, reading_id, job_id=job_id)
        recording_key = storage.recording_key(
            owner_user_id,
            reading_id,
            provider.output_extension,
            job_id=job_id,
        )
        timing_map_key = storage.timing_map_key(owner_user_id, reading_id, job_id=job_id)
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
        chunk_paths = [Path("/tmp") / f"{reading_id}-{chunk.index:04d}.mp3" for chunk in chunks]
        current_stage = ReadingStatus.GENERATING_AUDIO
        repo.set_status(owner_user_id, reading_id, current_stage)
        if job_id:
            repo.set_job_status(owner_user_id, str(job_id), current_stage)
        synthesize_started = time.perf_counter()
        for chunk, chunk_path in zip(chunks, chunk_paths, strict=True):
            await synthesize(chunk.text, str(chunk_path), selection, settings)
        synthesize_ms = round((time.perf_counter() - synthesize_started) * 1000)
        durations = [mp3_duration_seconds(chunk_path) for chunk_path in chunk_paths]
        timing_map = build_timing_map(chunks, durations)
        timing_map_json = json.dumps(timing_map)
        storage.put_text(timing_map_key, timing_map_json, "application/json")
        current_stage = ReadingStatus.MERGING_AUDIO
        repo.set_status(owner_user_id, reading_id, current_stage)
        if job_id:
            repo.set_job_status(owner_user_id, str(job_id), current_stage)
        merge_started = time.perf_counter()
        merge_mp3_files(chunk_paths, recording_path)
        merge_ms = round((time.perf_counter() - merge_started) * 1000)
        recording = recording_path.read_bytes()
        storage.put_bytes(recording_key, recording, provider.content_type)

        metadata = {
            **tts_metadata(selection),
            "normalization": normalization_status,
            "chunks": len(chunks),
            "merge": "byte-concat-v1",
        }
        cost: CostBreakdown | None = None
        try:
            invocation_ms = round((time.perf_counter() - invocation_started) * 1000)
            usage = RunUsage(
                chars_synthesized=len(corrected),
                chunks=len(chunks),
                audio_ms=int(timing_map["duration_ms"]),
                stored_bytes=sum(
                    (
                        len(original_text.encode()),
                        len(corrected.encode()),
                        len(timing_map_json.encode()),
                        len(recording),
                    )
                ),
                compute_ms_by_stage={
                    "normalize": normalize_ms,
                    "synthesize": synthesize_ms,
                    "merge": merge_ms,
                    "overhead": max(0, invocation_ms - normalize_ms - synthesize_ms - merge_ms),
                },
                lambda_memory_mb=int(
                    os.environ.get("AWS_LAMBDA_FUNCTION_MEMORY_SIZE") or settings.lambda_memory_mb
                ),
                vendor=selection.vendor,
            )
            # Prices must come from the same source the creation guardrail uses,
            # otherwise an operator override would change what gets blocked but
            # not what gets recorded.
            cost = estimate_cost(usage, get_prices(settings.cost_price_overrides))
        except Exception:
            logger.exception(
                "reading cost calculation failed",
                extra={"reading_id": reading_id, "owner_user_id": owner_user_id},
            )

        if cost is None:
            repo.mark_completed(
                owner_user_id,
                reading_id,
                corrected_text_key,
                recording_key,
                metadata,
                timing_map_key,
            )
        else:
            try:
                repo.mark_completed(
                    owner_user_id,
                    reading_id,
                    corrected_text_key,
                    recording_key,
                    metadata,
                    timing_map_key,
                    cost=cost,
                )
            except Exception:
                logger.exception(
                    "reading cost persistence failed",
                    extra={"reading_id": reading_id, "owner_user_id": owner_user_id},
                )
                repo.mark_completed(
                    owner_user_id,
                    reading_id,
                    corrected_text_key,
                    recording_key,
                    metadata,
                    timing_map_key,
                )
            else:
                logger.info(
                    "reading cost recorded",
                    extra={
                        "reading_id": reading_id,
                        "owner_user_id": owner_user_id,
                        "total_usd_micros": cost.total_usd_micros,
                        "price_book_version": cost.price_book_version,
                    },
                )
                try:
                    try:
                        repo.add_cost_rollup(
                            owner_user_id,
                            datetime.now(UTC).strftime("%Y-%m"),
                            cost,
                            reading_id=reading_id,
                            voice=selection.voice,
                            run_key=str(job_id or reading_id),
                        )
                    except TypeError as exc:
                        if "run_key" not in str(exc):
                            raise
                        repo.add_cost_rollup(
                            owner_user_id,
                            datetime.now(UTC).strftime("%Y-%m"),
                            cost,
                            reading_id=reading_id,
                            voice=selection.voice,
                        )
                except Exception:
                    logger.exception(
                        "reading cost rollup failed",
                        extra={"reading_id": reading_id, "owner_user_id": owner_user_id},
                    )
        if job_id:
            repo.set_job_status(owner_user_id, str(job_id), ReadingStatus.COMPLETED)
        return {"status": "completed"}
    except Exception as exc:
        logger.exception(
            "reading processing failed",
            extra={
                "reading_id": reading_id,
                "owner_user_id": owner_user_id,
                "vendor": event.get("vendor"),
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
        if job_id:
            try:
                repo.set_job_status(
                    owner_user_id,
                    str(job_id),
                    ReadingStatus.FAILED,
                    error=JOB_FAILURE_MESSAGES[current_stage],
                    failed_step=current_stage.value,
                )
            except Exception:
                logger.exception(
                    "failed to mark job failed",
                    extra={"job_id": job_id, "owner_user_id": owner_user_id},
                )
        raise
    finally:
        for temporary_path in Path("/tmp").glob(f"{reading_id}*"):
            temporary_path.unlink(missing_ok=True)


def handler(event: dict[str, Any], _context: Any) -> dict[str, str]:
    return asyncio.run(process_reading(event))
