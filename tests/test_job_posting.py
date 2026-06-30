from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import JobPosting


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


def test_job_posting_is_registered_in_metadata() -> None:
    table = Base.metadata.tables["job_postings"]

    assert table is JobPosting.__table__
    assert {column.name for column in table.columns} == {
        "id",
        "source",
        "external_id",
        "source_url",
        "company_name",
        "title",
        "location",
        "job_type",
        "experience_level",
        "education_level",
        "salary",
        "posting_date",
        "expiration_date",
        "is_active",
        "raw_payload",
        "created_at",
        "updated_at",
    }


def test_create_mock_job_posting(db_session: Session) -> None:
    posting = JobPosting(
        source="mock",
        external_id="mock-001",
        source_url="https://example.com/jobs/mock-001",
        company_name="Example Company",
        title="Python Backend Developer",
        location="Seoul",
        raw_payload={"provider": "mock", "skills": ["Python", "FastAPI"]},
    )

    db_session.add(posting)
    db_session.commit()
    db_session.refresh(posting)

    assert posting.id is not None
    assert posting.source == "mock"
    assert posting.is_active is True
    assert posting.raw_payload["skills"] == ["Python", "FastAPI"]
    assert posting.created_at is not None
    assert posting.updated_at is not None


def test_duplicate_source_and_external_id_is_rejected(
    db_session: Session,
) -> None:
    db_session.add(
        JobPosting(
            source="mock",
            external_id="duplicate-001",
            company_name="First Company",
            title="First Posting",
            raw_payload={},
        )
    )
    db_session.commit()

    db_session.add(
        JobPosting(
            source="mock",
            external_id="duplicate-001",
            company_name="Second Company",
            title="Duplicate Posting",
            raw_payload={},
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
