from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    JSON,
    String,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobPosting(Base):
    __tablename__ = "job_postings"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "external_id",
            name="uq_job_postings_source_external_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    job_type: Mapped[str | None] = mapped_column(String(100))
    experience_level: Mapped[str | None] = mapped_column(String(255))
    education_level: Mapped[str | None] = mapped_column(String(255))
    salary: Mapped[str | None] = mapped_column(String(255))
    posting_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expiration_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
    )
    raw_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        server_default=func.now(),
        nullable=False,
    )
