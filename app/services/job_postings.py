from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import JobPosting
from app.schemas import JobPostingCreate


class DuplicateJobPostingError(ValueError):
    def __init__(self, source: str, external_id: str) -> None:
        self.source = source
        self.external_id = external_id
        super().__init__(
            f"Job posting already exists: source={source!r}, "
            f"external_id={external_id!r}"
        )


def get_job_posting_by_id(
    db: Session,
    job_posting_id: int,
) -> JobPosting | None:
    return db.get(JobPosting, job_posting_id)


def get_job_posting_by_identity(
    db: Session,
    source: str,
    external_id: str,
) -> JobPosting | None:
    statement = select(JobPosting).where(
        JobPosting.source == source,
        JobPosting.external_id == external_id,
    )
    return db.scalar(statement)


def create_job_posting(
    db: Session,
    data: JobPostingCreate,
) -> JobPosting:
    existing = get_job_posting_by_identity(
        db,
        source=data.source,
        external_id=data.external_id,
    )
    if existing is not None:
        raise DuplicateJobPostingError(data.source, data.external_id)

    posting = JobPosting(**data.model_dump())
    db.add(posting)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        duplicate = get_job_posting_by_identity(
            db,
            source=data.source,
            external_id=data.external_id,
        )
        if duplicate is not None:
            raise DuplicateJobPostingError(
                data.source,
                data.external_id,
            ) from exc
        raise

    db.refresh(posting)
    return posting
