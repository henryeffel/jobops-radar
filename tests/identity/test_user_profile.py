from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.identity.profile_parser import parse_resume_markdown
from app.main import app


SAMPLE_RESUME = Path(__file__).parents[2] / "resume_sample.md"


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def _authorization(client: TestClient, email: str = "profile@example.com") -> dict[str, str]:
    password = "correct-horse-123"
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_parses_resume_sample_without_inventing_fields() -> None:
    parsed = parse_resume_markdown(SAMPLE_RESUME.read_text(encoding="utf-8"))

    assert parsed["summary"].startswith("Python을 중심으로")
    assert any("FastAPI" in skill for skill in parsed["skills"])
    assert parsed["projects"] == [
        "IEUM — RAG 기반 AI 회의 업무 자동화",
        "JobOps Radar — 채용공고 데이터 관리 및 분석 백엔드",
        "LEED Green Building Cost Predictor",
    ]
    assert parsed["education"] == ["George Brown College"]
    assert any("AZ-900" in item for item in parsed["certifications"])


def test_profile_requires_authentication(client: TestClient) -> None:
    assert client.get("/users/me/profile").status_code == 401
    assert client.put(
        "/users/me/profile", json={"resume_markdown": "## SUMMARY\nDeveloper"}
    ).status_code == 401


def test_profile_is_created_read_and_updated(client: TestClient) -> None:
    headers = _authorization(client)
    assert client.get("/users/me/profile", headers=headers).status_code == 404

    markdown = SAMPLE_RESUME.read_text(encoding="utf-8")
    created = client.put(
        "/users/me/profile",
        headers=headers,
        json={"resume_markdown": markdown},
    )
    assert created.status_code == 200
    assert created.json()["projects"][0].startswith("IEUM")
    assert created.json()["resume_markdown"] == markdown.strip()

    fetched = client.get("/users/me/profile", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["user_id"] == created.json()["user_id"]

    updated = client.put(
        "/users/me/profile",
        headers=headers,
        json={"resume_markdown": "## SUMMARY\nUpdated backend profile"},
    )
    assert updated.status_code == 200
    assert updated.json()["summary"] == "Updated backend profile"
    assert updated.json()["projects"] == []


def test_profiles_are_isolated_between_users(client: TestClient) -> None:
    first = _authorization(client, "first@example.com")
    second = _authorization(client, "second@example.com")
    client.put(
        "/users/me/profile",
        headers=first,
        json={"resume_markdown": "## SUMMARY\nFirst user"},
    )

    assert client.get("/users/me/profile", headers=second).status_code == 404


def test_profile_can_be_deleted_and_repeated_delete_returns_404(
    client: TestClient,
) -> None:
    headers = _authorization(client)
    client.put(
        "/users/me/profile",
        headers=headers,
        json={"resume_markdown": "## SUMMARY\nDelete me"},
    )

    assert client.delete("/users/me/profile", headers=headers).status_code == 204
    assert client.get("/users/me/profile", headers=headers).status_code == 404
    assert client.delete("/users/me/profile", headers=headers).status_code == 404
