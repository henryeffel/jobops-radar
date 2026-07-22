from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.identity.dependencies import get_current_user
from app.identity.models import User
from app.identity.profile_service import get_profile
from app.job_analysis.fetcher import JobContentFetchError
from app.job_analysis.schemas import JobAnalysisRequest, JobAnalysisResponse
from app.job_analysis.service import analyze_job

router = APIRouter(prefix="/job-analyses", tags=["job-analysis"])


@router.post("", response_model=JobAnalysisResponse)
def create_job_analysis(
    data: JobAnalysisRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    profile = get_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=409, detail="Create a user profile before analyzing a job")
    try:
        return analyze_job(
            profile,
            data.source_url,
            data.content,
            allow_external_llm=data.consent_to_external_llm,
        )
    except JobContentFetchError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
