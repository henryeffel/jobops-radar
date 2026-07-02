"""create job requirements table

Revision ID: 6f3b6c2d8a91
Revises: faf99527d991
Create Date: 2026-07-02 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "6f3b6c2d8a91"
down_revision: str | Sequence[str] | None = "faf99527d991"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the migration."""
    op.create_table(
        "job_requirements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_posting_id", sa.Integer(), nullable=False),
        sa.Column("requirement_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("importance", sa.Integer(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column(
            "source",
            sa.String(length=50),
            server_default="manual",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "importance >= 1 AND importance <= 5",
            name="ck_job_requirements_importance_range",
        ),
        sa.ForeignKeyConstraint(
            ["job_posting_id"],
            ["job_postings.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_job_requirements_job_posting_id"),
        "job_requirements",
        ["job_posting_id"],
        unique=False,
    )


def downgrade() -> None:
    """Revert the migration."""
    op.drop_index(
        op.f("ix_job_requirements_job_posting_id"),
        table_name="job_requirements",
    )
    op.drop_table("job_requirements")
