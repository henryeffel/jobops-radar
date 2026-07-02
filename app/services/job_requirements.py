from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import JobPosting, JobRequirement
from app.schemas import JobRequirementCreate


class JobPostingNotFoundError(ValueError):
    def __init__(self, job_posting_id: int) -> None:
        self.job_posting_id = job_posting_id
        super().__init__(f"Job posting not found: id={job_posting_id}")


def create_job_requirement(
    db: Session,
    data: JobRequirementCreate,
) -> JobRequirement:
    if db.get(JobPosting, data.job_posting_id) is None:
        raise JobPostingNotFoundError(data.job_posting_id)

    requirement = JobRequirement(**data.model_dump())
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


def list_job_requirements_for_posting(
    db: Session,
    job_posting_id: int,
) -> list[JobRequirement]:
    statement = (
        select(JobRequirement)
        .where(JobRequirement.job_posting_id == job_posting_id)
        .order_by(JobRequirement.id.asc())
    )
    return list(db.scalars(statement).all())


def get_job_requirement_by_id(
    db: Session,
    job_requirement_id: int,
) -> JobRequirement | None:
    return db.get(JobRequirement, job_requirement_id)
