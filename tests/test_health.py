import logging

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_liveness_reports_alive() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_reports_ready_when_database_query_succeeds() -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_database_failure_only_affects_readiness(
    caplog,
) -> None:
    secret_details = "postgresql://private-user:private-password@internal-db"

    class UnavailableSession:
        def execute(self, _statement) -> None:
            raise OperationalError(secret_details, {}, Exception(secret_details))

    def unavailable_db():
        yield UnavailableSession()

    app.dependency_overrides[get_db] = unavailable_db
    try:
        with caplog.at_level(logging.WARNING, logger="app.api.routes_health"):
            readiness_response = client.get("/health/ready")
        liveness_response = client.get("/health/live")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert readiness_response.status_code == 503
    assert readiness_response.json() == {"status": "not_ready"}
    assert liveness_response.status_code == 200
    assert liveness_response.json() == {"status": "alive"}
    assert secret_details not in readiness_response.text
    assert secret_details not in caplog.text
    assert "Database readiness check failed" in caplog.text


def test_openapi_distinguishes_liveness_and_readiness() -> None:
    paths = app.openapi()["paths"]

    live_operation = paths["/health/live"]["get"]
    ready_operation = paths["/health/ready"]["get"]

    assert "process" in live_operation["summary"].lower()
    assert "database" in ready_operation["summary"].lower()
    assert "503" in ready_operation["responses"]


def test_app_metadata_uses_settings() -> None:
    assert app.title == "JobOps Radar"
    assert app.version == "0.1.0"


def test_frontend_development_origin_is_allowed() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://127.0.0.1:5173"
    )
