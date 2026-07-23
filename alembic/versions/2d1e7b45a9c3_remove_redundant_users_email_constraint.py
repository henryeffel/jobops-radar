"""Remove redundant users email unique constraint.

Revision ID: 2d1e7b45a9c3
Revises: c81d417f0b8a
Create Date: 2026-07-23
"""

from collections.abc import Sequence

from alembic import op


revision: str = "2d1e7b45a9c3"
down_revision: str | None = "c81d417f0b8a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The model's ``unique=True, index=True`` is represented by the existing
    # unique index. PostgreSQL additionally received an unnecessary unique
    # constraint from the original migration.
    if op.get_bind().dialect.name == "postgresql":
        op.drop_constraint("users_email_key", "users", type_="unique")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.create_unique_constraint("users_email_key", "users", ["email"])
