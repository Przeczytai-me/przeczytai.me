from fastapi import APIRouter, Depends, Query

from app.auth import CurrentUser, get_current_user
from app.models import Job, JobListResponse
from app.repositories.readings import ReadingRepository
from app.routes.readings import get_reading_repository

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])
REQUIRED_JOB_FIELDS = {
    "job_id",
    "reading_id",
    "attempt",
    "status",
    "created_at",
    "updated_at",
}
STEP_MESSAGES = {
    "uploaded": "Przesłano",
    "normalizing": "Przetwarzanie tekstu",
    "generating_audio": "Generowanie audio",
    "merging_audio": "Scalanie nagrania",
    "completed": "Gotowe",
    "failed": "Błąd przetwarzania",
    "failed_to_start": "Błąd uruchomienia",
}


def _job(item: dict) -> Job:
    job_status = str(item["status"])
    if job_status == "completed":
        state = "ready"
    elif job_status in {"failed", "failed_to_start"}:
        state = "failed"
    else:
        state = "active"
    return Job(
        id=item["job_id"],
        reading_id=item["reading_id"],
        attempt=int(item["attempt"]),
        status=job_status,
        state=state,
        step_message=STEP_MESSAGES.get(job_status, job_status),
        progress=None,
        error=item.get("error"),
        failed_step=item.get("failed_step"),
        created_at=item["created_at"],
        updated_at=item["updated_at"],
    )


def _is_job_item(item: dict) -> bool:
    return all(item.get(field) is not None for field in REQUIRED_JOB_FIELDS)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    user: CurrentUser = Depends(get_current_user),
    repo: ReadingRepository = Depends(get_reading_repository),
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = None,
) -> JobListResponse:
    items, next_cursor = repo.list_jobs(user.user_id, limit, cursor)
    return JobListResponse(
        items=[_job(item) for item in items if _is_job_item(item)],
        next_cursor=next_cursor,
    )
