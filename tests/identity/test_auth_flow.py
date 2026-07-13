from collections.abc import Generator
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.audit.models import AuditLog
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.identity.models import User
from app.identity.security import create_access_token
from app.main import app

# Keep cryptographic tests independent from a developer's local .env value.
get_settings().jwt_secret_key = "test-only-secret-with-at-least-32-bytes"


@pytest.fixture
def context() -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, factory
    app.dependency_overrides.clear()
    engine.dispose()


def register(client: TestClient, email: str = "dev@example.com", password: str = "correct-horse-123"):
    return client.post("/auth/register", json={"email": email, "password": password})


def test_register_normalizes_email_and_never_stores_plaintext(context):
    client, factory = context
    response = register(client, "Dev@Example.COM")
    assert response.status_code == 201
    assert response.json()["email"] == "dev@example.com"
    with factory() as db:
        user = db.scalar(select(User))
        assert user is not None
        assert user.password_hash != "correct-horse-123"
        assert "correct-horse-123" not in user.password_hash


def test_duplicate_email_is_rejected(context):
    client, _ = context
    assert register(client).status_code == 201
    assert register(client).status_code == 409


def test_login_and_current_user(context):
    client, _ = context
    register(client)
    login = client.post("/auth/login", json={"email": "dev@example.com", "password": "correct-horse-123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "dev@example.com"


@pytest.mark.parametrize("email,password", [("dev@example.com", "wrong"), ("missing@example.com", "wrong")])
def test_invalid_credentials_use_same_response(context, email, password):
    client, _ = context
    register(client)
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_tampered_and_expired_tokens_are_rejected(context):
    client, _ = context
    user_id = register(client).json()["id"]
    valid = create_access_token(user_id)
    expired = create_access_token(user_id, datetime.now(timezone.utc) - timedelta(hours=2))
    for token in (valid + "tampered", expired):
        response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401


def test_security_events_contain_no_credentials_or_tokens(context):
    client, factory = context
    register(client)
    success = client.post("/auth/login", json={"email": "dev@example.com", "password": "correct-horse-123"})
    client.post("/auth/login", json={"email": "dev@example.com", "password": "secret-wrong"})
    with factory() as db:
        events = list(db.scalars(select(AuditLog).order_by(AuditLog.id)))
        assert [event.event_type for event in events] == ["USER_REGISTERED", "LOGIN_SUCCESS", "LOGIN_FAILURE"]
        serialized = repr([(event.metadata_, event.actor_user_id) for event in events])
        assert "correct-horse-123" not in serialized
        assert "secret-wrong" not in serialized
        assert success.json()["access_token"] not in serialized
