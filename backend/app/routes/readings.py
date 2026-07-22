import json
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import RedirectResponse

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.errors import ApiException
from app.models import (
    AbbreviationReading,
    Job,
    Reading,
    ReadingCreateRequest,
    ReadingListResponse,
    ReadingStatus,
    TimingMapResponse,
)
from app.repositories.readings import ProcessingStartError, ReadingRepository
from app.storage import FileStorage, StorageError, StorageObjectNotFoundError
from app.tts import (
    TtsInputTooLargeError,
    TtsProviderUnavailableError,
    TtsSelection,
    UnsupportedTtsVendorError,
    ensure_tts_provider_available,
    resolve_tts_selection,
    validate_tts_input,
)

router = APIRouter(prefix="/api/v1/readings", tags=["readings"])
REQUIRED_READING_FIELDS = {
    "reading_id",
    "original_text_key",
    "status",
    "char_count",
    "created_at",
    "updated_at",
}
TERMINAL_READING_STATUSES = {
    ReadingStatus.COMPLETED,
    ReadingStatus.FAILED,
    ReadingStatus.FAILED_TO_START,
}


def get_reading_repository(settings: Settings = Depends(get_settings)) -> ReadingRepository:
    return ReadingRepository(settings.readings_table_name, settings.processor_function_name)


def get_file_storage(settings: Settings = Depends(get_settings)) -> FileStorage:
    return FileStorage(settings.files_bucket_name)


def _reading(item: dict) -> Reading:
    return Reading(
        id=item["reading_id"],
        original_text_key=item["original_text_key"],
        corrected_text_key=item.get("corrected_text_key"),
        recording_key=item.get("recording_key"),
        vendor=item.get("vendor"),
        voice=item.get("voice"),
        status=item["status"],
        metadata=item.get("metadata", {}),
        char_count=int(item["char_count"]),
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


def _is_reading_item(item: dict) -> bool:
    return all(item.get(field) is not None for field in REQUIRED_READING_FIELDS)


def _get_user_reading(
    owner_user_id: str,
    reading_id: str,
    repo: ReadingRepository,
) -> dict:
    item = repo.get(owner_user_id, reading_id)
    if not item or not _is_reading_item(item):
        raise ApiException("not_found", "Reading not found", 404)
    return item


def _normalize_original_text(original_text: str, max_text_chars: int) -> str:
    original_text = original_text.strip()
    if not original_text:
        raise ApiException("validation_error", "Original text must not be empty", 422)
    if len(original_text) > max_text_chars:
        raise ApiException("payload_too_large", "Original text is too large", 413)
    return original_text


def _normalize_abbreviation_readings(
    pairs: list[AbbreviationReading] | None,
) -> list[dict[str, str]] | None:
    if not pairs:
        return None
    if len(pairs) > 100:
        raise ApiException("validation_error", "Too many abbreviation readings", 422)

    normalized = []
    abbreviations = set()
    for pair in pairs:
        abbreviation = pair.abbreviation.strip()
        read_as = pair.read_as.strip()
        if not abbreviation or not read_as:
            raise ApiException("validation_error", "Abbreviation readings must not be empty", 422)
        if len(abbreviation) > 50 or len(read_as) > 200:
            raise ApiException("validation_error", "Abbreviation reading is too long", 422)
        key = abbreviation.casefold()
        if key in abbreviations:
            raise ApiException("validation_error", "Duplicate abbreviation reading", 422)
        abbreviations.add(key)
        normalized.append({"abbreviation": abbreviation, "read_as": read_as})
    return normalized


def _resolve_create_tts_selection(
    request: ReadingCreateRequest, original_text: str, settings: Settings
) -> TtsSelection:
    try:
        selection = resolve_tts_selection(request.vendor, request.voice)
        ensure_tts_provider_available(selection, settings)
        validate_tts_input(original_text, selection)
        return selection
    except UnsupportedTtsVendorError as exc:
        raise ApiException("validation_error", str(exc), 422) from exc
    except TtsProviderUnavailableError as exc:
        raise ApiException("provider_unavailable", str(exc), 503) from exc
    except TtsInputTooLargeError as exc:
        raise ApiException("payload_too_large", str(exc), 413) from exc


def _store_original_text(
    *,
    owner_user_id: str,
    reading_id: str,
    original_text: str,
    storage: FileStorage,
) -> str:
    original_text_key = storage.original_text_key(owner_user_id, reading_id)
    try:
        storage.put_text(original_text_key, original_text, "text/plain; charset=utf-8")
    except StorageError as exc:
        raise ApiException("storage_error", "Failed to store original text", 500) from exc
    return original_text_key


@router.post("", response_model=Reading, status_code=status.HTTP_202_ACCEPTED)
async def create_reading(
    request: ReadingCreateRequest,
    user: CurrentUser = Depends(get_current_user),
    repo: ReadingRepository = Depends(get_reading_repository),
    storage: FileStorage = Depends(get_file_storage),
    settings: Settings = Depends(get_settings),
) -> Reading:
    original_text = _normalize_original_text(request.original_text, settings.max_text_chars)
    abbreviation_readings = _normalize_abbreviation_readings(request.abbreviation_readings)
    selection = _resolve_create_tts_selection(request, original_text, settings)
    reading_id = repo.next_id()
    original_text_key = _store_original_text(
        owner_user_id=user.user_id,
        reading_id=reading_id,
        original_text=original_text,
        storage=storage,
    )
    item = repo.create(
        user.user_id,
        reading_id,
        original_text_key,
        len(original_text),
        selection.vendor,
        selection.voice,
        abbreviation_readings=abbreviation_readings,
    )
    job = repo.create_job(user.user_id, reading_id, attempt=1)
    try:
        repo.start_processing(
            user.user_id,
            reading_id,
            original_text_key,
            selection.vendor,
            selection.voice,
            job["job_id"],
            abbreviation_readings=abbreviation_readings,
        )
    except ProcessingStartError as exc:
        repo.mark_processing_start_failed(user.user_id, reading_id)
        repo.set_job_status(
            user.user_id,
            job["job_id"],
            ReadingStatus.FAILED_TO_START,
            error="Failed to start reading processing",
        )
        raise ApiException(
            "processing_start_failed",
            "Failed to start reading processing",
            500,
        ) from exc
    return _reading(item)


@router.get("", response_model=ReadingListResponse)
async def list_readings(
    user: CurrentUser = Depends(get_current_user),
    repo: ReadingRepository = Depends(get_reading_repository),
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = None,
) -> ReadingListResponse:
    items, next_cursor = repo.list(user.user_id, limit, cursor)
    return ReadingListResponse(
        items=[_reading(item) for item in items if _is_reading_item(item)],
        next_cursor=next_cursor,
    )


@router.get("/{reading_id}", response_model=Reading)
async def get_reading(
    reading_id: str,
    user: CurrentUser = Depends(get_current_user),
    repo: ReadingRepository = Depends(get_reading_repository),
) -> Reading:
    return _reading(_get_user_reading(user.user_id, reading_id, repo))


@router.get("/{reading_id}/timing-map", response_model=TimingMapResponse)
async def get_timing_map(
    reading_id: str,
    user: CurrentUser = Depends(get_current_user),
    repo: ReadingRepository = Depends(get_reading_repository),
    storage: FileStorage = Depends(get_file_storage),
) -> TimingMapResponse:
    item = _get_user_reading(user.user_id, reading_id, repo)
    if item["status"] not in TERMINAL_READING_STATUSES:
        raise ApiException("timing_map_not_ready", "Timing map is not ready", 409)
    timing_map_key = item.get("timing_map_key")
    if not timing_map_key:
        raise ApiException("timing_map_unavailable", "Timing map is not available", 404)
    try:
        timing_map = json.loads(storage.get_text(str(timing_map_key)))
    except StorageError as exc:
        raise ApiException("storage_error", "Failed to load timing map", 500) from exc
    return TimingMapResponse(
        reading_id=reading_id,
        duration=timing_map["duration"],
        segments=timing_map["segments"],
    )


@router.post("/{reading_id}/retry", response_model=Job, status_code=status.HTTP_202_ACCEPTED)
async def retry_reading(
    reading_id: str,
    user: CurrentUser = Depends(get_current_user),
    repo: ReadingRepository = Depends(get_reading_repository),
) -> Job:
    item = _get_user_reading(user.user_id, reading_id, repo)
    if item["status"] not in TERMINAL_READING_STATUSES:
        raise ApiException(
            "conflict",
            "A processing attempt is already active for this reading",
            409,
        )

    attempt = repo.increment_attempts(user.user_id, reading_id)
    job = repo.create_job(user.user_id, reading_id, attempt)
    repo.set_status(user.user_id, reading_id, ReadingStatus.UPLOADED)
    try:
        repo.start_processing(
            user.user_id,
            reading_id,
            item["original_text_key"],
            item["vendor"],
            item["voice"],
            job["job_id"],
        )
    except ProcessingStartError as exc:
        repo.mark_processing_start_failed(user.user_id, reading_id)
        repo.set_job_status(
            user.user_id,
            job["job_id"],
            ReadingStatus.FAILED_TO_START,
            error="Failed to start reading processing",
        )
        raise ApiException(
            "processing_start_failed",
            "Failed to start reading processing",
            500,
        ) from exc

    from app.routes.jobs import _job

    return _job(job)


@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reading(
    reading_id: str,
    user: CurrentUser = Depends(get_current_user),
    repo: ReadingRepository = Depends(get_reading_repository),
) -> Response:
    repo.delete(user.user_id, reading_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{reading_id}/recording")
async def download_recording(
    reading_id: str,
    user: CurrentUser = Depends(get_current_user),
    repo: ReadingRepository = Depends(get_reading_repository),
    storage: FileStorage = Depends(get_file_storage),
) -> Response:
    item = _get_user_reading(user.user_id, reading_id, repo)
    recording_key = item.get("recording_key")
    if not recording_key:
        raise ApiException("not_found", "Recording not found", 404)
    extension = Path(str(recording_key)).suffix or ".mp3"
    try:
        url = storage.download_url(str(recording_key), f"{reading_id}-recording{extension}")
    except StorageError as exc:
        raise ApiException("storage_error", "Failed to load recording", 500) from exc
    return RedirectResponse(url)


@router.get("/{reading_id}/corrected-text.md")
async def download_corrected_text(
    reading_id: str,
    user: CurrentUser = Depends(get_current_user),
    repo: ReadingRepository = Depends(get_reading_repository),
    storage: FileStorage = Depends(get_file_storage),
) -> Response:
    item = _get_user_reading(user.user_id, reading_id, repo)
    corrected_text_key = item.get("corrected_text_key")
    if not corrected_text_key:
        raise ApiException("not_found", "Corrected text not found", 404)
    try:
        corrected_text = storage.get_text(str(corrected_text_key))
    except StorageError as exc:
        raise ApiException("storage_error", "Failed to load corrected text", 500) from exc
    return Response(
        content=corrected_text,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{reading_id}.md"'},
    )


@router.get("/{reading_id}/original-text")
async def download_original_text(
    reading_id: str,
    user: CurrentUser = Depends(get_current_user),
    repo: ReadingRepository = Depends(get_reading_repository),
    storage: FileStorage = Depends(get_file_storage),
) -> Response:
    item = _get_user_reading(user.user_id, reading_id, repo)
    original_text_key = str(item["original_text_key"])
    try:
        original_text = storage.get_text(original_text_key)
    except StorageObjectNotFoundError as exc:
        raise ApiException("not_found", "Original text not found", 404) from exc
    except StorageError as exc:
        raise ApiException("storage_error", "Failed to load original text", 500) from exc
    extension = Path(original_text_key).suffix or ".txt"
    media_type = "text/markdown" if extension == ".md" else "text/plain"
    return Response(
        content=original_text,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{reading_id}{extension}"'},
    )
