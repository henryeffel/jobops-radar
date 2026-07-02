from collections.abc import Generator
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import JobPosting


@pytest.fixture
def api_context() -> Generator[tuple[TestClient, Engine], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    test_session_factory = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    def override_get_db() -> Generator[Session, None, None]:
        with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client, engine

    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


def build_payload(external_id: str = "mock-route-001") -> dict[str, object]:
    return {
        "source": "mock",
        "external_id": external_id,
        "source_url": f"https://example.com/jobs/{external_id}",
        "company_name": "Example Company",
        "title": "Python Backend Developer",
        "location": "Seoul",
        "raw_payload": {"provider": "mock"},
    }


def seed_pagination_postings(engine: Engine, total: int = 4) -> None:
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
    with Session(engine) as session:
        for index, created_at in enumerate(timestamps[:total], start=1):
            session.add(
                JobPosting(
                    source="mock",
                    external_id=f"page-{index}",
                    company_name="Example Company",
                    title=f"Posting {index}",
                    raw_payload={},
                    created_at=created_at,
                )
            )
        session.commit()


def test_create_job_posting_route(
    api_context: tuple[TestClient, Engine],
) -> None:
    client, _ = api_context

    response = client.post("/job-postings", json=build_payload())

    assert response.status_code == 201
    assert response.json()["id"] > 0
    assert response.json()["source"] == "mock"
    assert response.json()["external_id"] == "mock-route-001"


def test_get_job_posting_by_id(
    api_context: tuple[TestClient, Engine],
) -> None:
    client, _ = api_context
    created = client.post(
        "/job-postings",
        json=build_payload("mock-route-by-id"),
    ).json()

    response = client.get(f"/job-postings/{created['id']}")

    assert response.status_code == 200
    assert response.json()["external_id"] == "mock-route-by-id"


def test_get_job_posting_by_source_identity(
    api_context: tuple[TestClient, Engine],
) -> None:
    client, _ = api_context
    client.post(
        "/job-postings",
        json=build_payload("mock-route-by-source"),
    )

    response = client.get(
        "/job-postings/by-source/mock/mock-route-by-source"
    )

    assert response.status_code == 200
    assert response.json()["company_name"] == "Example Company"


def test_duplicate_create_returns_existing_without_second_row(
    api_context: tuple[TestClient, Engine],
) -> None:
    client, engine = api_context
    payload = build_payload("mock-route-duplicate")

    first = client.post("/job-postings", json=payload)
    second = client.post("/job-postings", json=payload)

    with Session(engine) as session:
        count = session.scalar(
            select(func.count()).select_from(JobPosting)
        )

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert count == 1


def test_missing_job_posting_returns_404(
    api_context: tuple[TestClient, Engine],
) -> None:
    client, _ = api_context

    by_id = client.get("/job-postings/999999")
    by_source = client.get(
        "/job-postings/by-source/mock/does-not-exist"
    )

    assert by_id.status_code == 404
    assert by_source.status_code == 404


def test_list_job_postings_route(
    api_context: tuple[TestClient, Engine],
) -> None:
    client, engine = api_context
    seed_pagination_postings(engine, total=21)

    response = client.get("/job-postings")

    assert response.status_code == 200
    assert len(response.json()) == 20


def test_list_job_postings_route_applies_limit(
    api_context: tuple[TestClient, Engine],
) -> None:
    client, engine = api_context
    seed_pagination_postings(engine)

    response = client.get("/job-postings", params={"limit": 2})

    assert response.status_code == 200
    assert [item["external_id"] for item in response.json()] == [
        "page-4",
        "page-2",
    ]


def test_list_job_postings_route_applies_offset(
    api_context: tuple[TestClient, Engine],
) -> None:
    client, engine = api_context
    seed_pagination_postings(engine)

    response = client.get("/job-postings", params={"offset": 2})

    assert response.status_code == 200
    assert [item["external_id"] for item in response.json()] == [
        "page-3",
        "page-1",
    ]


def test_list_job_postings_route_has_deterministic_order(
    api_context: tuple[TestClient, Engine],
) -> None:
    client, engine = api_context
    seed_pagination_postings(engine)

    response = client.get("/job-postings")

    assert [item["external_id"] for item in response.json()] == [
        "page-4",
        "page-2",
        "page-3",
        "page-1",
    ]


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("limit", 0),
        ("limit", 101),
        ("offset", -1),
    ],
)
def test_list_job_postings_route_rejects_invalid_pagination(
    api_context: tuple[TestClient, Engine],
    parameter: str,
    value: int,
) -> None:
    client, _ = api_context

    response = client.get("/job-postings", params={parameter: value})

    assert response.status_code == 422


def test_openapi_contains_job_posting_routes() -> None:
    paths = app.openapi()["paths"]

    assert "/job-postings" in paths
    assert "get" in paths["/job-postings"]
    assert "/job-postings/{job_posting_id}" in paths
    assert "/job-postings/by-source/{source}/{external_id}" in paths
