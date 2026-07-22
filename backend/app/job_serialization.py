from app.models import Job, JobError


STATUS_MAP = {
    "uploaded": "uploaded",
    "normalizing": "extracting_text",
    "processing": "extracting_text",
    "generating_audio": "generating_audio",
    "merging_audio": "generating_audio",
    "completed": "ready",
    "failed": "failed",
    "failed_to_start": "failed",
}
CURRENT_STEPS = {
    "uploaded": "Przesłano",
    "normalizing": "Przetwarzanie tekstu",
    "generating_audio": "Generowanie audio",
    "merging_audio": "Scalanie nagrania",
    "completed": "Gotowe",
    "failed": "Błąd przetwarzania",
    "failed_to_start": "Błąd uruchomienia",
}


def serialize_job(item: dict) -> Job:
    internal_status = str(item["status"])
    error = None
    if internal_status == "failed":
        error = JobError(
            code="processing_failed",
            message=item["error"],
            step=item["failed_step"],
        )
    elif internal_status == "failed_to_start":
        error = JobError(
            code="processing_start_failed",
            message="Failed to start reading processing",
            step="start_processing",
        )

    return Job(
        id=item["job_id"],
        reading_id=item["reading_id"],
        attempt=int(item["attempt"]),
        status=STATUS_MAP.get(internal_status, internal_status),
        progress=None,
        current_step=CURRENT_STEPS.get(internal_status, internal_status),
        error=error,
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )
