from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def load_models() -> None:
    from app.models import JobPosting

    _ = JobPosting
