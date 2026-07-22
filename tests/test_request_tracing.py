import json
import logging
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.request_tracing import RequestTracingMiddleware
from app.main import app


client = TestClient(app)


def _completion_record(caplog):
    records = [
        record
        for record in caplog.records
        if record.name == "app.core.request_tracing"
    ]
    assert len(records) == 1
    return json.loads(records[0].message)


def test_safe_external_request_id_is_returned_and_logged(caplog) -> None:
    request_id = "jobops.test_123-abc"

    with caplog.at_level(logging.INFO, logger="app.core.request_tracing"):
        response = client.get(
            "/health/live",
            headers={"X-Request-ID": request_id},
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
    assert _completion_record(caplog) == {
        "elapsed_ms": _completion_record(caplog)["elapsed_ms"],
        "event": "http_request_completed",
        "method": "GET",
        "path": "/health/live",
        "request_id": request_id,
        "status_code": 200,
    }
    assert isinstance(_completion_record(caplog)["elapsed_ms"], float)
    assert _completion_record(caplog)["elapsed_ms"] >= 0


def test_missing_request_id_is_generated_as_uuid(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="app.core.request_tracing"):
        response = client.get("/health/live")

    generated_id = response.headers["X-Request-ID"]
    assert str(UUID(generated_id)) == generated_id
    assert _completion_record(caplog)["request_id"] == generated_id


def test_unsafe_request_id_is_replaced() -> None:
    unsafe_id = "contains spaces and secrets"

    response = client.get(
        "/health/live",
        headers={"X-Request-ID": unsafe_id},
    )

    generated_id = response.headers["X-Request-ID"]
    assert generated_id != unsafe_id
    assert str(UUID(generated_id)) == generated_id


def test_request_id_length_boundary() -> None:
    maximum_length_id = "a" * 128
    accepted_response = client.get(
        "/health/live",
        headers={"X-Request-ID": maximum_length_id},
    )
    replaced_response = client.get(
        "/health/live",
        headers={"X-Request-ID": "a" * 129},
    )

    assert accepted_response.headers["X-Request-ID"] == maximum_length_id
    assert replaced_response.headers["X-Request-ID"] != "a" * 129
    assert str(UUID(replaced_response.headers["X-Request-ID"])) == (
        replaced_response.headers["X-Request-ID"]
    )


def test_request_log_excludes_query_string_and_sensitive_value(caplog) -> None:
    sensitive_value = "secret-token-value"

    with caplog.at_level(logging.INFO, logger="app.core.request_tracing"):
        response = client.get(
            f"/health/live?access_token={sensitive_value}",
            headers={"Authorization": f"Bearer {sensitive_value}"},
        )

    assert response.status_code == 200
    record = _completion_record(caplog)
    assert record["path"] == "/health/live"
    assert sensitive_value not in caplog.text
    assert "access_token" not in caplog.text


def test_cors_exposes_request_id_header() -> None:
    response = client.get(
        "/health/live",
        headers={
            "Origin": "http://127.0.0.1:5173",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-expose-headers"] == "X-Request-ID"
    assert "X-Request-ID" in response.headers


def test_unhandled_error_returns_request_id_and_redacted_failure_log(
    caplog,
) -> None:
    secret_detail = "database-password-must-not-be-logged"
    failing_app = FastAPI()
    failing_app.add_middleware(RequestTracingMiddleware)

    @failing_app.get("/failure")
    def fail() -> None:
        raise RuntimeError(secret_detail)

    failing_client = TestClient(failing_app, raise_server_exceptions=False)
    with caplog.at_level(logging.INFO, logger="app.core.request_tracing"):
        response = failing_client.get(
            "/failure",
            headers={"X-Request-ID": "failure-test-123"},
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert response.headers["X-Request-ID"] == "failure-test-123"
    assert secret_detail not in caplog.text
    assert "exception details redacted" in caplog.text

    messages = [record.message for record in caplog.records]
    failure_event = json.loads(
        next(message for message in messages if "http_request_failed" in message)
    )
    completion_event = json.loads(
        next(message for message in messages if "http_request_completed" in message)
    )
    assert failure_event == {
        "event": "http_request_failed",
        "exception_type": "RuntimeError",
        "method": "GET",
        "path": "/failure",
        "request_id": "failure-test-123",
    }
    assert completion_event["request_id"] == "failure-test-123"
    assert completion_event["status_code"] == 500
