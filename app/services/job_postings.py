from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import JobPosting, JobRequirement
from app.schemas import (
    JobPostingCreate,
    JobPostingSort,
    JobRequirementDraft,
)


class DuplicateJobPostingError(ValueError):
    def __init__(self, source: str, external_id: str) -> None:
        self.source = source
        self.external_id = external_id
        super().__init__(
            f"Job posting already exists: source={source!r}, "
            f"external_id={external_id!r}"
        )


class JobPostingBundleConstraintError(ValueError):
    """Raised after an atomic posting bundle violates a DB constraint."""

    def __init__(self) -> None:
        super().__init__("Job posting bundle violates a database constraint")


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


def build_job_postings_statement(
    limit: int = 20,
    offset: int = 0,
    company_name: str | None = None,
    is_active: bool | None = None,
    sort: JobPostingSort = JobPostingSort.CREATED_AT,
) -> Select[tuple[JobPosting]]:
    statement = select(JobPosting)
    if company_name is not None:
        statement = statement.where(JobPosting.company_name == company_name)
    if is_active is not None:
        statement = statement.where(JobPosting.is_active.is_(is_active))

    if sort == JobPostingSort.EXPIRATION_DATE:
        statement = statement.order_by(
            JobPosting.expiration_date.asc().nulls_last(),
            JobPosting.id.desc(),
        )
    else:
        statement = statement.order_by(
            JobPosting.created_at.desc(),
            JobPosting.id.desc(),
        )

    statement = statement.limit(limit).offset(offset)
    return statement


def list_job_postings(
    db: Session,
    limit: int = 20,
    offset: int = 0,
    company_name: str | None = None,
    is_active: bool | None = None,
    sort: JobPostingSort = JobPostingSort.CREATED_AT,
) -> list[JobPosting]:
    statement = build_job_postings_statement(
        limit=limit,
        offset=offset,
        company_name=company_name,
        is_active=is_active,
        sort=sort,
    )
    return list(db.scalars(statement).all())


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


def create_job_posting_with_requirements(
    db: Session,
    posting_data: JobPostingCreate,
    requirements_data: Sequence[JobRequirementDraft],
) -> tuple[JobPosting, list[JobRequirement]]:
    posting = JobPosting(**posting_data.model_dump())
    requirements: list[JobRequirement] = []

    try:
        db.add(posting)
        db.flush()

        requirements = [
            JobRequirement(
                job_posting_id=posting.id,
                **requirement_data.model_dump(),
            )
            for requirement_data in requirements_data
        ]
        db.add_all(requirements)
        db.flush()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise JobPostingBundleConstraintError() from exc
    except Exception:
        db.rollback()
        raise

    return posting, requirements
