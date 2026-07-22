from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import JobPosting
from app.schemas import JobPostingCreate, JobPostingRead, JobPostingSort
from app.services import (
    DuplicateJobPostingError,
    create_job_posting,
    get_job_posting_by_identity,
    list_job_postings,
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


def seed_pagination_postings(
    db_session: Session,
    total: int = 4,
) -> None:
    timestamps = [
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 3, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
        datetime(2026, 1, 3, tzinfo=timezone.utc),
    ]
    timestamps.extend(
        datetime(2025, 1, 1, tzinfo=timezone.utc)
        for _ in range(max(0, total - len(timestamps)))
    )
    for index, created_at in enumerate(timestamps[:total], start=1):
        db_session.add(
            JobPosting(
                source="mock",
                external_id=f"page-{index}",
                company_name="Example Company",
                title=f"Posting {index}",
                raw_payload={},
                created_at=created_at,
            )
        )
    db_session.commit()


def seed_query_postings(db_session: Session) -> None:
    rows = [
        ("alpha-active", "Alpha", True, datetime(2026, 2, 10, tzinfo=timezone.utc)),
        ("alpha-inactive", "Alpha", False, datetime(2026, 2, 5, tzinfo=timezone.utc)),
        ("beta-active", "Beta", True, datetime(2026, 2, 1, tzinfo=timezone.utc)),
        ("alpha-no-deadline", "Alpha", True, None),
    ]
    for external_id, company_name, is_active, expiration_date in rows:
        db_session.add(
            JobPosting(
                source="mock",
                external_id=external_id,
                company_name=company_name,
                title=external_id,
                is_active=is_active,
                expiration_date=expiration_date,
                raw_payload={},
            )
        )
    db_session.commit()


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


def test_list_job_postings_uses_default_pagination(
    db_session: Session,
) -> None:
    seed_pagination_postings(db_session, total=21)

    postings = list_job_postings(db_session)

    assert len(postings) == 20


def test_list_job_postings_applies_limit(db_session: Session) -> None:
    seed_pagination_postings(db_session)

    postings = list_job_postings(db_session, limit=2)

    assert [posting.external_id for posting in postings] == [
        "page-4",
        "page-2",
    ]


def test_list_job_postings_applies_offset(db_session: Session) -> None:
    seed_pagination_postings(db_session)

    postings = list_job_postings(db_session, offset=2)

    assert [posting.external_id for posting in postings] == [
        "page-3",
        "page-1",
    ]


def test_list_job_postings_has_deterministic_order(
    db_session: Session,
) -> None:
    seed_pagination_postings(db_session)

    postings = list_job_postings(db_session)

    assert [posting.external_id for posting in postings] == [
        "page-4",
        "page-2",
        "page-3",
        "page-1",
    ]


def test_list_job_postings_combines_filters(db_session: Session) -> None:
    seed_query_postings(db_session)

    postings = list_job_postings(
        db_session,
        company_name="Alpha",
        is_active=True,
    )

    assert {posting.external_id for posting in postings} == {
        "alpha-active",
        "alpha-no-deadline",
    }


def test_list_job_postings_filters_inactive_before_pagination(
    db_session: Session,
) -> None:
    seed_query_postings(db_session)

    postings = list_job_postings(
        db_session,
        is_active=False,
        limit=1,
    )

    assert [posting.external_id for posting in postings] == [
        "alpha-inactive",
    ]


def test_list_job_postings_sorts_expiration_and_places_null_last(
    db_session: Session,
) -> None:
    seed_query_postings(db_session)

    postings = list_job_postings(
        db_session,
        sort=JobPostingSort.EXPIRATION_DATE,
    )

    assert [posting.external_id for posting in postings] == [
        "beta-active",
        "alpha-inactive",
        "alpha-active",
        "alpha-no-deadline",
    ]
