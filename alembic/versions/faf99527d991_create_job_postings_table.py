"""create job postings table

Revision ID: faf99527d991
Revises: 
Create Date: 2026-06-30 16:37:35.969309

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "faf99527d991"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the migration."""
    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("job_type", sa.String(length=100), nullable=True),
        sa.Column("experience_level", sa.String(length=255), nullable=True),
        sa.Column("education_level", sa.String(length=255), nullable=True),
        sa.Column("salary", sa.String(length=255), nullable=True),
        sa.Column(
            "posting_date",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "expiration_date",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source",
            "external_id",
            name="uq_job_postings_source_external_id",
        ),
    )


def downgrade() -> None:
    """Revert the migration."""
    op.drop_table("job_postings")
