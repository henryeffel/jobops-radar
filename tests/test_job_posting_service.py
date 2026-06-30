from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import JobPosting
from app.schemas import JobPostingCreate, JobPostingRead
from app.services import (
    DuplicateJobPostingError,
    create_job_posting,
    get_job_posting_by_identity,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


def build_mock_posting(external_id: str = "mock-service-001") -> JobPostingCreate:
    return JobPostingCreate(
        source="mock",
        external_id=external_id,
        source_url=f"https://example.com/jobs/{external_id}",
        company_name="Example Company",
        title="Backend Developer",
        location="Seoul",
        raw_payload={"provider": "mock"},
    )


def test_create_job_posting_through_service(db_session: Session) -> None:
    posting = create_job_posting(db_session, build_mock_posting())
    response = JobPostingRead.model_validate(posting)

    assert posting.id is not None
    assert response.source == "mock"
    assert response.external_id == "mock-service-001"
    assert response.raw_payload == {"provider": "mock"}


def test_get_job_posting_by_identity(db_session: Session) -> None:
    created = create_job_posting(
        db_session,
        build_mock_posting("mock-service-lookup"),
    )

    found = get_job_posting_by_identity(
        db_session,
        source="mock",
        external_id="mock-service-lookup",
    )

    assert found is not None
    assert found.id == created.id
    assert found.title == "Backend Developer"


def test_duplicate_input_does_not_create_second_row(
    db_session: Session,
) -> None:
    data = build_mock_posting("mock-service-duplicate")
    original = create_job_posting(db_session, data)

    with pytest.raises(DuplicateJobPostingError):
        create_job_posting(db_session, data)

    count = db_session.scalar(
        select(func.count()).select_from(JobPosting)
    )
    found = get_job_posting_by_identity(
        db_session,
        source=data.source,
        external_id=data.external_id,
    )

    assert count == 1
    assert found is not None
    assert found.id == original.id
