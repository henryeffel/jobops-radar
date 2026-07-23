"""Add the measured job posting list index.

Revision ID: 7a4c92e81f6d
Revises: 2d1e7b45a9c3
Create Date: 2026-07-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "7a4c92e81f6d"
down_revision: str | None = "2d1e7b45a9c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


INDEX_NAME = "ix_job_postings_company_active_expiration_id"


def upgrade() -> None:
    op.create_index(
        INDEX_NAME,
        "job_postings",
        ["company_name", "is_active", "expiration_date", sa.text("id DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="job_postings")
