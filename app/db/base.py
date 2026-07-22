from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def load_models() -> None:
    from app.models import JobPosting, JobRequirement
    from app.audit.models import AuditLog
    from app.identity.models import User
    from app.identity.profile_models import UserProfile

    _ = JobPosting, JobRequirement, User, UserProfile, AuditLog
