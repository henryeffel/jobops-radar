from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import JobPosting, JobRequirement
from app.schemas import JobPostingCreate, JobRequirementDraft
from app.services import (
    JobPostingBundleConstraintError,
    create_job_posting_with_requirements,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    engine.dispose()


def build_posting(external_id: str) -> JobPostingCreate:
    return JobPostingCreate(
        source="transaction-test",
        external_id=external_id,
        company_name="Example Company",
        title="Backend Developer",
        raw_payload={},
    )


def build_requirement(
    name: str,
    importance: int = 5,
) -> JobRequirementDraft:
    return JobRequirementDraft(
        requirement_type="skill",
        name=name,
        is_required=True,
        importance=importance,
        evidence=f"Evidence for {name}",
    )


def count_rows(db_session: Session, model: type) -> int:
    count = db_session.scalar(select(func.count()).select_from(model))
    assert count is not None
    return count


def invalid_requirement(name: str) -> JobRequirementDraft:
    return JobRequirementDraft.model_construct(
        requirement_type="skill",
        name=name,
        description=None,
        is_required=True,
        importance=99,
        evidence="Violates the database importance check",
        source="manual",
    )


def test_bundle_commits_posting_and_all_requirements(
    db_session: Session,
) -> None:
    posting, requirements = create_job_posting_with_requirements(
        db_session,
        build_posting("bundle-success"),
        [
            build_requirement("Python"),
            build_requirement("PostgreSQL", importance=4),
        ],
    )

    assert posting.id is not None
    assert [requirement.job_posting_id for requirement in requirements] == [
        posting.id,
        posting.id,
    ]
    assert count_rows(db_session, JobPosting) == 1
    assert count_rows(db_session, JobRequirement) == 2


def test_requirement_constraint_failure_rolls_back_entire_bundle(
    db_session: Session,
) -> None:
    with pytest.raises(JobPostingBundleConstraintError):
        create_job_posting_with_requirements(
            db_session,
            build_posting("bundle-rollback"),
            [
                build_requirement("Python"),
                invalid_requirement("Invalid importance"),
            ],
        )

    assert not db_session.in_transaction()
    assert count_rows(db_session, JobPosting) == 0
    assert count_rows(db_session, JobRequirement) == 0


def test_session_can_be_reused_after_bundle_rollback(
    db_session: Session,
) -> None:
    with pytest.raises(JobPostingBundleConstraintError):
        create_job_posting_with_requirements(
            db_session,
            build_posting("bundle-failed-first"),
            [invalid_requirement("Invalid importance")],
        )

    posting, requirements = create_job_posting_with_requirements(
        db_session,
        build_posting("bundle-success-after-rollback"),
        [build_requirement("Python")],
    )

    assert posting.id is not None
    assert len(requirements) == 1
    assert count_rows(db_session, JobPosting) == 1
    assert count_rows(db_session, JobRequirement) == 1


def test_unexpected_error_during_requirement_flush_rolls_back_all_rows(
    db_session: Session,
) -> None:
    flush_count = 0

    def fail_second_flush(*_args) -> None:
        nonlocal flush_count
        flush_count += 1
        if flush_count == 2:
            raise RuntimeError("simulated requirement persistence failure")

    event.listen(db_session, "before_flush", fail_second_flush)
    try:
        with pytest.raises(
            RuntimeError,
            match="simulated requirement persistence failure",
        ):
            create_job_posting_with_requirements(
                db_session,
                build_posting("bundle-unexpected-error"),
                [build_requirement("Python")],
            )
    finally:
        event.remove(db_session, "before_flush", fail_second_flush)

    assert not db_session.in_transaction()
    assert count_rows(db_session, JobPosting) == 0
    assert count_rows(db_session, JobRequirement) == 0


def test_duplicate_posting_constraint_is_converted_and_preserves_existing_data(
    db_session: Session,
) -> None:
    create_job_posting_with_requirements(
        db_session,
        build_posting("bundle-duplicate"),
        [build_requirement("Existing")],
    )

    with pytest.raises(
        JobPostingBundleConstraintError,
        match="database constraint",
    ):
        create_job_posting_with_requirements(
            db_session,
            build_posting("bundle-duplicate"),
            [build_requirement("Must not remain")],
        )

    assert count_rows(db_session, JobPosting) == 1
    assert count_rows(db_session, JobRequirement) == 1
