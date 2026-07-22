import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/live",
    summary="Check whether the application process is alive",
    description=(
        "Returns success while the FastAPI process can serve requests. "
        "It does not check database or external provider availability."
    ),
)
def liveness() -> dict[str, str]:
    return {"status": "alive"}


@router.get(
    "/ready",
    response_model=None,
    summary=(
        "Check whether the application is ready to serve database-backed requests"
    ),
    description=(
        "Executes a minimal database query. Returns 503 without internal "
        "connection details when the database is unavailable."
    ),
    responses={
        503: {
            "description": "The database readiness check failed.",
            "content": {
                "application/json": {
                    "example": {"status": "not_ready"},
                }
            },
        }
    },
)
def readiness(
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str] | JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        logger.warning("Database readiness check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready"},
        )

    return {"status": "ready"}
