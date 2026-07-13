from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def load_models() -> None:
    from app.models import JobPosting, JobRequirement
    from app.audit.models import AuditLog
    from app.identity.models import User

    _ = JobPosting, JobRequirement, User, AuditLog
