import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql

from app.schemas import JobPostingSort
from app.services.job_postings import build_job_postings_statement
from scripts.postgres_query_plan import require_postgresql


def test_benchmark_rejects_sqlite() -> None:
    engine = create_engine("sqlite://")
    try:
        with pytest.raises(RuntimeError, match="requires PostgreSQL"):
            require_postgresql(engine)
    finally:
        engine.dispose()


def test_benchmark_uses_the_real_filtered_deadline_query() -> None:
    statement = build_job_postings_statement(
        company_name="Benchmark Company 01",
        is_active=True,
        sort=JobPostingSort.EXPIRATION_DATE,
        limit=20,
        offset=0,
    )
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "job_postings.company_name = 'Benchmark Company 01'" in sql
    assert "job_postings.is_active IS true" in sql
    assert "job_postings.expiration_date ASC NULLS LAST" in sql
    assert "job_postings.id DESC" in sql
    assert "LIMIT 20 OFFSET 0" in sql

