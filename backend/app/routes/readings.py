from pathlib import Path

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import RedirectResponse

from app.auth import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.errors import ApiException
from app.models import Reading, ReadingCreateRequest, ReadingListResponse
from app.repositories.readings import ProcessingStartError, ReadingRepository
from app.storage import FileStorage, StorageError
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
    )
    try:
        repo.start_processing(
            user.user_id,
            reading_id,
            original_text_key,
            selection.vendor,
            selection.voice,
        )
    except ProcessingStartError as exc:
        repo.mark_processing_start_failed(user.user_id, reading_id)
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
