from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RequirementType = Literal[
    "skill",
    "experience",
    "security",
    "operations",
    "architecture",
    "culture",
    "language",
]


class JobRequirementCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    job_posting_id: int = Field(gt=0)
    requirement_type: RequirementType
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    is_required: bool
    importance: int = Field(ge=1, le=5)
    evidence: str | None = Field(default=None, max_length=2000)
    source: str = Field(default="manual", min_length=1, max_length=50)


class JobRequirementRead(JobRequirementCreate):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        from_attributes=True,
    )

    id: int
    created_at: datetime
    updated_at: datetime
