from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import LOGIN_FAILURE, LOGIN_SUCCESS, USER_REGISTERED, record_security_event
from app.core.config import get_settings
from app.identity import repository
from app.identity.models import User
from app.identity.security import hash_password, verify_password
from app.identity.verification_guard import PasswordVerificationGuard


class DuplicateEmailError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


_settings = get_settings()
password_verification_guard = PasswordVerificationGuard(
    max_concurrency=_settings.auth_verify_max_concurrency,
    wait_timeout_seconds=_settings.auth_verify_wait_timeout_seconds,
)


def register(db: Session, email: str, password: str) -> User:
    normalized_email = email.strip().lower()
    if repository.get_by_email(db, normalized_email):
        raise DuplicateEmailError
    try:
        user = repository.add(db, normalized_email, hash_password(password))
        db.flush()
        record_security_event(db, USER_REGISTERED, user.id)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateEmailError from exc


def authenticate(db: Session, email: str, password: str) -> User:
    user = repository.get_by_email(db, email.strip().lower())
    password_is_valid = (
        user is not None
        and user.is_active
        and password_verification_guard.run(
            lambda: verify_password(password, user.password_hash)
        )
    )
    if not password_is_valid:
        record_security_event(db, LOGIN_FAILURE, user.id if user else None)
        db.commit()
        raise InvalidCredentialsError
    record_security_event(db, LOGIN_SUCCESS, user.id)
    db.commit()
    return user
