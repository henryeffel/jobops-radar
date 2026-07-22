from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import JobPostingCreate, JobPostingRead, JobPostingSort
from app.services import (
    DuplicateJobPostingError,
    create_job_posting,
    get_job_posting_by_id,
    get_job_posting_by_identity,
    list_job_postings,
)

router = APIRouter(prefix="/job-postings", tags=["job-postings"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=list[JobPostingRead],
)
def read_job_postings(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    company_name: Annotated[
        str | None,
        Query(min_length=1, max_length=255),
    ] = None,
    is_active: bool | None = None,
    sort: JobPostingSort = JobPostingSort.CREATED_AT,
) -> list[JobPostingRead]:
    postings = list_job_postings(
        db,
        limit=limit,
        offset=offset,
        company_name=company_name,
        is_active=is_active,
        sort=sort,
    )
    return [JobPostingRead.model_validate(posting) for posting in postings]


@router.post(
    "",
    response_model=JobPostingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_job_posting_route(
    data: JobPostingCreate,
    response: Response,
    db: DbSession,
) -> JobPostingRead:
    try:
        posting = create_job_posting(db, data)
    except DuplicateJobPostingError as exc:
        posting = get_job_posting_by_identity(
            db,
            source=exc.source,
            external_id=exc.external_id,
        )
        if posting is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc
        response.status_code = status.HTTP_200_OK

    return JobPostingRead.model_validate(posting)


@router.get(
    "/by-source/{source}/{external_id}",
    response_model=JobPostingRead,
)
def read_job_posting_by_source(
    source: str,
    external_id: str,
    db: DbSession,
) -> JobPostingRead:
    posting = get_job_posting_by_identity(db, source, external_id)
    if posting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found",
        )
    return JobPostingRead.model_validate(posting)


@router.get(
    "/{job_posting_id}",
    response_model=JobPostingRead,
)
def read_job_posting(
    job_posting_id: int,
    db: DbSession,
) -> JobPostingRead:
    posting = get_job_posting_by_id(db, job_posting_id)
    if posting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job posting not found",
        )
    return JobPostingRead.model_validate(posting)
