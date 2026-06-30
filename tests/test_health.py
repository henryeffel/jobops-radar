from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_metadata_uses_settings() -> None:
    assert app.title == "JobOps Radar"
    assert app.version == "0.1.0"
