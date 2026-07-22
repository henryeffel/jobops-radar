from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_job_postings import router as job_postings_router
from app.core.config import get_settings
from app.core.request_tracing import RequestTracingMiddleware
from app.identity.router import router as identity_router
from app.job_analysis.router import router as job_analysis_router

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestTracingMiddleware)
app.include_router(job_postings_router)
app.include_router(identity_router)
app.include_router(job_analysis_router)
app.include_router(health_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Retain the original lightweight health endpoint for compatibility."""
    return {"status": "ok"}
