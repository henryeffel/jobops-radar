from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import create_db_engine, engine, get_db


def test_engine_uses_configured_database_url() -> None:
    assert engine.url == make_url(get_settings().database_url)


def test_get_db_yields_session() -> None:
    dependency = get_db()
    session = next(dependency)

    assert isinstance(session, Session)

    dependency.close()


def test_sqlite_engine_connects() -> None:
    sqlite_engine = create_db_engine("sqlite://")

    try:
        with sqlite_engine.connect() as connection:
            assert connection.scalar(text("SELECT 1")) == 1
    finally:
        sqlite_engine.dispose()
