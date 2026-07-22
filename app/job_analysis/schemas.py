from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JobAnalysisRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    source_url: str | None = Field(default=None, max_length=2048)
    content: str | None = Field(default=None, max_length=1_000_000)
    consent_to_external_llm: bool = False

    @model_validator(mode="after")
    def require_url_or_content(self):
        if not self.source_url and not self.content:
            raise ValueError("source_url or content is required")
        return self


class RequirementMatch(BaseModel):
    name: str
    requirement_type: str
    is_required: bool
    importance: int
    matched: bool
    evidence: str
    profile_evidence: str | None = None


class PreparationAction(BaseModel):
    skill: str
    priority: Literal["high", "medium"]
    reason: str
    action: str


class JobAnalysisResponse(BaseModel):
    source_url: str | None
    page_title: str | None
    input_method: Literal["url", "content"]
    analysis_method: Literal["llm", "deterministic"]
    fallback_reason: str | None
    extracted_text: str
    match_score: int
    requirements: list[RequirementMatch]
    matched_skills: list[str]
    missing_skills: list[str]
    action_plan: list[PreparationAction]
    warnings: list[str]
