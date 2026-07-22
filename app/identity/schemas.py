from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfileUpsert(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    resume_markdown: str = Field(min_length=1, max_length=100_000)


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    resume_markdown: str
    summary: str | None
    skills: list[str]
    projects: list[str]
    education: list[str]
    certifications: list[str]
    created_at: datetime
    updated_at: datetime
