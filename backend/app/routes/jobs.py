from fastapi import APIRouter, Depends, Query

from app.auth import CurrentUser, get_current_user
from app.job_serialization import serialize_job
from app.models import JobListResponse
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
        items=[serialize_job(item) for item in items if _is_job_item(item)],
        next_cursor=next_cursor,
    )
