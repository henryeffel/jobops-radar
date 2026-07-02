from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.job_posting import JobPosting


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class JobRequirement(Base):
    __tablename__ = "job_requirements"
    __table_args__ = (
        CheckConstraint(
            "importance >= 1 AND importance <= 5",
            name="ck_job_requirements_importance_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id"),
        index=True,
        nullable=False,
    )
    requirement_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(
        String(50),
        default="manual",
        server_default="manual",
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
    job_posting: Mapped["JobPosting"] = relationship(
        back_populates="requirements",
    )
