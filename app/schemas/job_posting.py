from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class JobPostingCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    source: str = Field(min_length=1, max_length=50)
    external_id: str = Field(min_length=1, max_length=255)
    source_url: str | None = Field(default=None, max_length=2048)
    company_name: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=500)
    location: str | None = Field(default=None, max_length=255)
    job_type: str | None = Field(default=None, max_length=100)
    experience_level: str | None = Field(default=None, max_length=255)
    education_level: str | None = Field(default=None, max_length=255)
    salary: str | None = Field(default=None, max_length=255)
    posting_date: datetime | None = None
    expiration_date: datetime | None = None
    is_active: bool = True
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class JobPostingRead(JobPostingCreate):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        from_attributes=True,
    )

    id: int
    created_at: datetime
    updated_at: datetime
