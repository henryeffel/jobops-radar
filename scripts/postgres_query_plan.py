import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import Engine, create_engine, delete, func, insert, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import JobPosting
from app.schemas import JobPostingSort
from app.services.job_postings import build_job_postings_statement

BENCHMARK_SOURCE = "postgres-query-plan-benchmark"
DEFAULT_COMPANY = "Benchmark Company 01"


def require_postgresql(engine: Engine) -> None:
    if engine.dialect.name != "postgresql":
        raise RuntimeError(
            "This benchmark requires PostgreSQL; SQLite results are not accepted."
        )


def seed_benchmark_rows(
    engine: Engine,
    row_count: int,
    batch_size: int = 1_000,
) -> None:
    require_postgresql(engine)
    now = datetime.now(timezone.utc)

    with Session(engine) as session, session.begin():
        existing = session.scalar(
            select(func.count())
            .select_from(JobPosting)
            .where(JobPosting.source == BENCHMARK_SOURCE)
        )
        if existing:
            raise RuntimeError(
                f"Benchmark rows already exist: {existing}. Run cleanup first."
            )

        for batch_start in range(0, row_count, batch_size):
            batch_end = min(batch_start + batch_size, row_count)
            rows = []
            for index in range(batch_start, batch_end):
                expiration_date = (
                    None
                    if index % 10 == 0
                    else now + timedelta(days=index % 180)
                )
                rows.append(
                    {
                        "source": BENCHMARK_SOURCE,
                        "external_id": f"benchmark-{index:08d}",
                        "source_url": None,
                        "company_name": f"Benchmark Company {index % 20:02d}",
                        "title": f"Benchmark Backend Posting {index}",
                        "location": "Seoul",
                        "job_type": "full-time",
                        "experience_level": None,
                        "education_level": None,
                        "salary": None,
                        "posting_date": now - timedelta(days=index % 90),
                        "expiration_date": expiration_date,
                        "is_active": index % 5 != 0,
                        "raw_payload": {"benchmark": True},
                        "created_at": now - timedelta(seconds=index),
                        "updated_at": now,
                    }
                )
            session.execute(insert(JobPosting), rows)


def cleanup_benchmark_rows(engine: Engine) -> int:
    require_postgresql(engine)
    with Session(engine) as session, session.begin():
        result = session.execute(
            delete(JobPosting).where(JobPosting.source == BENCHMARK_SOURCE)
        )
        return int(result.rowcount or 0)


def explain_query(
    engine: Engine,
    company_name: str,
    is_active: bool,
    limit: int,
    offset: int,
) -> object:
    require_postgresql(engine)
    statement = build_job_postings_statement(
        company_name=company_name,
        is_active=is_active,
        sort=JobPostingSort.EXPIRATION_DATE,
        limit=limit,
        offset=offset,
    )
    compiled = statement.compile(
        dialect=engine.dialect,
        compile_kwargs={"literal_binds": True},
    )
    explain_statement = text(
        "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + str(compiled)
    )
    with engine.connect() as connection:
        plan = connection.execute(explain_statement).scalar_one()
    if isinstance(plan, str):
        return json.loads(plan)
    return plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed and measure the real JobPosting query on PostgreSQL."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed")
    seed_parser.add_argument("--rows", type=int, default=50_000)

    explain_parser = subparsers.add_parser("explain")
    explain_parser.add_argument("--company", default=DEFAULT_COMPANY)
    explain_parser.add_argument(
        "--inactive",
        action="store_true",
        help="Measure inactive postings instead of active postings.",
    )
    explain_parser.add_argument("--limit", type=int, default=20)
    explain_parser.add_argument("--offset", type=int, default=0)
    explain_parser.add_argument("--output", type=Path)

    subparsers.add_parser("cleanup")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    engine = create_engine(get_settings().database_url, pool_pre_ping=True)
    try:
        try:
            if args.command == "seed":
                if args.rows < 1:
                    raise ValueError("--rows must be at least 1")
                seed_benchmark_rows(engine, args.rows)
                print(json.dumps({"event": "benchmark_seeded", "rows": args.rows}))
            elif args.command == "cleanup":
                deleted = cleanup_benchmark_rows(engine)
                print(json.dumps({"event": "benchmark_cleaned", "rows": deleted}))
            else:
                if not 1 <= args.limit <= 100:
                    raise ValueError("--limit must be between 1 and 100")
                if args.offset < 0:
                    raise ValueError("--offset must not be negative")
                plan = explain_query(
                    engine,
                    company_name=args.company,
                    is_active=not args.inactive,
                    limit=args.limit,
                    offset=args.offset,
                )
                rendered = json.dumps(
                    plan,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
                if args.output:
                    args.output.write_text(rendered + "\n", encoding="utf-8")
                else:
                    print(rendered)
        except (RuntimeError, ValueError) as exc:
            parser.error(str(exc))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
