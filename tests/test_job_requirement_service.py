from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import JobPosting
from app.schemas import JobRequirementCreate, JobRequirementRead
from app.services import (
    JobPostingNotFoundError,
    create_job_requirement,
    get_job_requirement_by_id,
    list_job_requirements_for_posting,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


def create_posting(db_session: Session, external_id: str) -> JobPosting:
    posting = JobPosting(
        source="manual",
        external_id=external_id,
        company_name="Carrot",
        title="Identity Service Backend",
        raw_payload={},
    )
    db_session.add(posting)
    db_session.commit()
    db_session.refresh(posting)
    return posting


def build_requirement(
    job_posting_id: int,
    name: str = "OIDC",
    requirement_type: str = "architecture",
) -> JobRequirementCreate:
    return JobRequirementCreate(
        job_posting_id=job_posting_id,
        requirement_type=requirement_type,
        name=name,
        description=f"Structured requirement for {name}",
        is_required=True,
        importance=5,
        evidence=f"The posting identifies {name} as a relevant capability.",
    )


def test_create_requirement_for_existing_posting(
    db_session: Session,
) -> None:
    posting = create_posting(db_session, "carrot-create")

    requirement = create_job_requirement(
        db_session,
        build_requirement(posting.id),
    )
    response = JobRequirementRead.model_validate(requirement)

    assert requirement.id is not None
    assert response.job_posting_id == posting.id
    assert response.name == "OIDC"
    assert response.source == "manual"


def test_list_requirements_for_posting(db_session: Session) -> None:
    posting = create_posting(db_session, "carrot-list")
    create_job_requirement(
        db_session,
        build_requirement(posting.id, "OIDC"),
    )
    create_job_requirement(
        db_session,
        build_requirement(
            posting.id,
            "Security/privacy",
            "security",
        ),
    )

    requirements = list_job_requirements_for_posting(
        db_session,
        posting.id,
    )

    assert [requirement.name for requirement in requirements] == [
        "OIDC",
        "Security/privacy",
    ]


def test_store_carrot_identity_requirement_types(
    db_session: Session,
) -> None:
    posting = create_posting(db_session, "carrot-case-study")
    case_study_data = [
        ("OIDC", "architecture"),
        ("Security/privacy", "security"),
        ("High availability", "operations"),
        ("B2B account modeling", "architecture"),
        ("Authentication UX", "skill"),
        ("AI-assisted workflow culture", "culture"),
    ]

    for name, requirement_type in case_study_data:
        create_job_requirement(
            db_session,
            build_requirement(posting.id, name, requirement_type),
        )

    requirements = list_job_requirements_for_posting(
        db_session,
        posting.id,
    )

    assert [requirement.name for requirement in requirements] == [
        name for name, _ in case_study_data
    ]
    assert {requirement.requirement_type for requirement in requirements} == {
        "architecture",
        "security",
        "operations",
        "skill",
        "culture",
    }


def test_requirement_is_linked_to_correct_posting(
    db_session: Session,
) -> None:
    target = create_posting(db_session, "carrot-target")
    other = create_posting(db_session, "carrot-other")

    created = create_job_requirement(
        db_session,
        build_requirement(target.id),
    )

    assert created.job_posting.id == target.id
    assert list_job_requirements_for_posting(
        db_session,
        target.id,
    ) == [created]
    assert list_job_requirements_for_posting(
        db_session,
        other.id,
    ) == []


def test_create_requirement_rejects_missing_posting(
    db_session: Session,
) -> None:
    with pytest.raises(JobPostingNotFoundError):
        create_job_requirement(
            db_session,
            build_requirement(999999),
        )


def test_get_job_requirement_by_id(db_session: Session) -> None:
    posting = create_posting(db_session, "carrot-get")
    created = create_job_requirement(
        db_session,
        build_requirement(posting.id),
    )

    found = get_job_requirement_by_id(db_session, created.id)

    assert found is not None
    assert found.id == created.id
