from fastapi import FastAPI

from app.api.routes_job_postings import router as job_postings_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(job_postings_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
