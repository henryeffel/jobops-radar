import json
import logging
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db
from app.identity.profile_models import UserProfile
from app.integrations.llm_api import (
    LLMAnalysis,
    LLMAnalysisError,
    LLMRequirement,
    _decode_json_content,
    _validate_evidence_ids,
)
from app.job_analysis.fetcher import UnsafeJobUrlError, extract_visible_text, validate_public_url
from app.job_analysis import service as analysis_service
from app.job_analysis.structured_input import EvidenceSection, build_comparison_input
from app.main import app


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


def _headers(client: TestClient) -> dict[str, str]:
    credentials = {"email": "analysis@example.com", "password": "correct-horse-123"}
    assert client.post("/auth/register", json=credentials).status_code == 201
    token = client.post("/auth/login", json=credentials).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_html_extraction_omits_non_visible_content() -> None:
    title, text = extract_visible_text(
        "<html><head><title>Backend Job</title><style>.x{}</style></head>"
        "<body><h1>Python Developer</h1><script>secret()</script></body></html>"
    )
    assert title == "Backend Job"
    assert "Python Developer" in text
    assert "secret" not in text
    assert ".x" not in text


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "http://127.0.0.1/admin",
        "http://localhost/admin",
        "http://user:password@example.com/job",
    ],
)
def test_url_validation_blocks_non_public_targets(url: str) -> None:
    with pytest.raises(UnsafeJobUrlError):
        validate_public_url(url)


def test_analysis_requires_authentication(client: TestClient) -> None:
    response = client.post("/job-analyses", json={"content": "Python required"})
    assert response.status_code == 401


def test_analysis_requires_profile(client: TestClient) -> None:
    response = client.post(
        "/job-analyses",
        headers=_headers(client),
        json={"content": "Python required"},
    )
    assert response.status_code == 409


def test_content_fallback_matches_profile_with_evidence(client: TestClient) -> None:
    headers = _headers(client)
    profile = """## SUMMARY
Python backend developer

## SKILLS
- **Backend:** Python, FastAPI, SQLAlchemy, REST API
- **Tools:** Git, Linux
"""
    assert client.put(
        "/users/me/profile",
        headers=headers,
        json={"resume_markdown": profile},
    ).status_code == 200

    response = client.post(
        "/job-analyses",
        headers=headers,
        json={
            "source_url": "https://jobs.example.com/backend-1",
            "content": """
                <html><head><title>Backend Engineer</title></head><body>
                <h1>Backend Engineer</h1>
                <p>필수 자격요건: Python, FastAPI, SQL 경험</p>
                <p>우대사항: Docker와 AWS 운영 경험</p>
                </body></html>
            """,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["input_method"] == "content"
    assert body["fallback_reason"] == "llm_mock_mode"
    assert body["page_title"] == "Backend Engineer"
    assert body["match_score"] == 71
    assert body["matched_skills"] == ["Python", "FastAPI", "SQL"]
    assert body["missing_skills"] == ["Docker", "AWS"]
    assert all(item["evidence"] for item in body["requirements"])
    assert [item["skill"] for item in body["action_plan"]] == ["Docker", "AWS"]
    assert all(item["priority"] == "medium" for item in body["action_plan"])


def test_analysis_reports_when_no_known_requirement_is_found(client: TestClient) -> None:
    headers = _headers(client)
    client.put(
        "/users/me/profile",
        headers=headers,
        json={"resume_markdown": "## SUMMARY\nBackend developer"},
    )
    response = client.post(
        "/job-analyses",
        headers=headers,
        json={"content": "좋은 동료를 찾습니다."},
    )
    assert response.status_code == 200
    assert response.json()["match_score"] == 0
    assert response.json()["warnings"]


def test_comparison_input_assigns_stable_evidence_ids() -> None:
    profile = UserProfile(
        user_id=1,
        resume_markdown="## SUMMARY\nPython developer\n\n## PROJECTS\nFastAPI service",
        summary="Python developer",
        skills=["Python", "FastAPI"],
        projects=["FastAPI service"],
        education=[],
        certifications=[],
    )
    comparison = build_comparison_input(
        "## Required\nPython experience\n\n## Preferred\nDocker experience",
        profile,
        10_000,
    )

    assert [item.evidence_id for item in comparison.job.sections] == [
        "job-001",
        "job-002",
    ]
    assert comparison.job.sections[0].heading == "Required"
    assert comparison.candidate.sections[0].evidence_id == "candidate-001"
    assert comparison.candidate.skills == ["Python", "FastAPI"]


@pytest.mark.parametrize(
    ("heading", "text", "expected"),
    [
        ("Required Qualifications", "Python experience", (True, 5)),
        ("우대사항", "Docker 경험", (False, 3)),
        ("Platform Requirements", "The design must be understood", (False, 2)),
    ],
)
def test_server_classifies_requirement_priority_without_substring_false_positives(
    heading: str,
    text: str,
    expected: tuple[bool, int],
) -> None:
    section = EvidenceSection(
        evidence_id="job-001",
        heading=heading,
        text=text,
    )

    assert analysis_service._classify_evidence_sections([section]) == expected


def test_llm_evidence_ids_must_exist_in_input() -> None:
    profile = UserProfile(
        user_id=1,
        resume_markdown="## SUMMARY\nPython developer",
        summary="Python developer",
        skills=["Python"],
        projects=[],
        education=[],
        certifications=[],
    )
    comparison = build_comparison_input("Python required", profile, 10_000)
    result = LLMAnalysis(
        requirements=[
            LLMRequirement(
                name="Python",
                requirement_type="skill",
                job_evidence_ids=["job-999"],
                profile_evidence_ids=["candidate-001"],
            )
        ]
    )

    with pytest.raises(LLMAnalysisError, match="unknown job evidence ID"):
        _validate_evidence_ids(result, comparison)


def test_llm_contract_normalizes_safe_json_variants() -> None:
    payload = _decode_json_content(
        """```json
{"requirements":[{"name":"Python","requirement_type":"skill","job_evidence_id":"job-001","profile_evidence_ids":null}]}
```"""
    )
    result = LLMAnalysis.model_validate(payload)

    assert result.requirements[0].job_evidence_ids == ["job-001"]
    assert result.requirements[0].profile_evidence_ids == []


def test_llm_contract_deduplicates_and_bounds_evidence_ids() -> None:
    result = LLMAnalysis.model_validate(
        {
            "requirements": [
                {
                    "name": "Python",
                    "requirement_type": "skill",
                    "job_evidence_ids": ["job-001"],
                    "profile_evidence_ids": [
                        "candidate-001",
                        "candidate-002",
                        "candidate-002",
                        "candidate-003",
                        "candidate-004",
                        "candidate-005",
                        "candidate-006",
                    ],
                }
            ]
        }
    )

    assert result.requirements[0].profile_evidence_ids == [
        "candidate-001",
        "candidate-002",
        "candidate-003",
        "candidate-004",
        "candidate-005",
    ]


def test_llm_analysis_is_scored_from_validated_structured_result(monkeypatch) -> None:
    profile = UserProfile(
        user_id=1,
        resume_markdown="Python backend developer",
        summary="Python backend developer",
        skills=["Python"],
        projects=[],
        education=[],
        certifications=[],
    )
    result = LLMAnalysis(
        requirements=[
            LLMRequirement(
                name="Python",
                requirement_type="skill",
                job_evidence_ids=["job-001"],
                profile_evidence_ids=["candidate-001"],
            ),
            LLMRequirement(
                name="Docker",
                requirement_type="operations",
                job_evidence_ids=["job-002"],
                profile_evidence_ids=[],
            ),
        ]
    )
    monkeypatch.setattr(analysis_service, "analyze_with_llm", lambda *args: result)

    analysis = analysis_service.analyze_job_text(
        "## Required\nPython experience\n\n## Preferred\nDocker experience",
        profile,
        Settings(_env_file=None, llm_mock_mode=False, llm_api_key="test-key"),
    )

    assert analysis["analysis_method"] == "llm"
    assert analysis["match_score"] == 62
    assert analysis["missing_skills"] == ["Docker"]


def test_llm_failure_uses_deterministic_fallback(monkeypatch, caplog) -> None:
    profile = UserProfile(
        user_id=1,
        resume_markdown="Python backend developer",
        summary="Python backend developer",
        skills=["Python"],
        projects=[],
        education=[],
        certifications=[],
    )

    def fail(*args):
        raise LLMAnalysisError("provider unavailable with secret detail")

    monkeypatch.setattr(analysis_service, "analyze_with_llm", fail)
    with caplog.at_level(logging.WARNING, logger="app.job_analysis.service"):
        analysis = analysis_service.analyze_job_text(
            "Python is required.",
            profile,
            Settings(_env_file=None, llm_mock_mode=False, llm_api_key="test-key"),
        )

    assert analysis["analysis_method"] == "deterministic"
    assert analysis["fallback_reason"] == "llm_error"
    assert analysis["match_score"] == 100
    assert "deterministic analysis was used" in analysis["warnings"][0]
    fallback_log = json.loads(caplog.records[-1].message)
    assert fallback_log == {
        "event": "llm_fallback",
        "reason": "llm_error",
        "request_id": None,
    }
    assert "secret detail" not in caplog.text


def test_external_llm_requires_explicit_consent() -> None:
    profile = UserProfile(
        user_id=1,
        resume_markdown="Python developer",
        summary="Python developer",
        skills=["Python"],
        projects=[],
        education=[],
        certifications=[],
    )
    analysis = analysis_service.analyze_job_text(
        "Python required",
        profile,
        Settings(_env_file=None, llm_mock_mode=False, llm_api_key="test-key"),
        allow_external_llm=False,
    )

    assert analysis["analysis_method"] == "deterministic"
    assert analysis["fallback_reason"] == "external_llm_consent_required"


def test_complete_mvp_journey_ends_with_deleted_profile(client: TestClient) -> None:
    headers = _headers(client)
    profile = client.put(
        "/users/me/profile",
        headers=headers,
        json={"resume_markdown": "## SUMMARY\nPython developer\n\n## SKILLS\n- Python"},
    )
    assert profile.status_code == 200

    analysis = client.post(
        "/job-analyses",
        headers=headers,
        json={
            "content": "## Required\nPython backend experience",
            "consent_to_external_llm": False,
        },
    )
    assert analysis.status_code == 200
    assert analysis.json()["analysis_method"] == "deterministic"
    assert analysis.json()["match_score"] == 100

    assert client.delete("/users/me/profile", headers=headers).status_code == 204
    assert client.get("/users/me/profile", headers=headers).status_code == 404
    unavailable = client.post(
        "/job-analyses",
        headers=headers,
        json={"content": "Python required"},
    )
    assert unavailable.status_code == 409
