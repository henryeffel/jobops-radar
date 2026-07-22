import json
import logging
import re
from contextvars import ContextVar, Token
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 128
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
_request_id_context: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)
logger = logging.getLogger(__name__)


def resolve_request_id(candidate: str | None) -> str:
    if candidate is not None and _SAFE_REQUEST_ID.fullmatch(candidate):
        return candidate
    return str(uuid4())


def get_request_id() -> str | None:
    """Return the request ID while code is running in an HTTP request context."""
    return _request_id_context.get()


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
        request.state.request_id = request_id
        token: Token[str | None] = _request_id_context.set(request_id)
        started_at = perf_counter()
        status_code = 500

        try:
            try:
                response = await call_next(request)
            except Exception as exc:
                logger.error(
                    json.dumps(
                        {
                            "event": "http_request_failed",
                            "request_id": request_id,
                            "method": request.method,
                            "path": request.url.path,
                            "exception_type": type(exc).__name__,
                        },
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                    exc_info=(
                        RuntimeError,
                        RuntimeError("exception details redacted"),
                        exc.__traceback__,
                    ),
                )
                response = JSONResponse(
                    status_code=500,
                    content={"detail": "Internal Server Error"},
                )
            status_code = response.status_code
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            elapsed_ms = round((perf_counter() - started_at) * 1000, 3)
            logger.info(
                json.dumps(
                    {
                        "event": "http_request_completed",
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": status_code,
                        "elapsed_ms": elapsed_ms,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            _request_id_context.reset(token)
