from collections.abc import Generator

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import JobPosting, JobRequirement
from app.schemas import JobRequirementCreate


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


def test_job_requirement_is_registered_in_metadata() -> None:
    table = Base.metadata.tables["job_requirements"]

    assert table is JobRequirement.__table__
    assert {column.name for column in table.columns} == {
        "id",
        "job_posting_id",
        "requirement_type",
        "name",
        "description",
        "is_required",
        "importance",
        "evidence",
        "source",
        "created_at",
        "updated_at",
    }


@pytest.mark.parametrize("importance", [0, 6])
def test_job_requirement_schema_rejects_invalid_importance(
    importance: int,
) -> None:
    with pytest.raises(ValidationError):
        JobRequirementCreate(
            job_posting_id=1,
            requirement_type="skill",
            name="FastAPI",
            is_required=True,
            importance=importance,
        )


def test_database_rejects_invalid_importance(
    db_session: Session,
) -> None:
    posting = JobPosting(
        source="manual",
        external_id="importance-check",
        company_name="Carrot",
        title="Identity Service Backend",
        raw_payload={},
    )
    db_session.add(posting)
    db_session.commit()

    db_session.add(
        JobRequirement(
            job_posting_id=posting.id,
            requirement_type="security",
            name="Security and privacy",
            is_required=True,
            importance=6,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()
