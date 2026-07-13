from sqlalchemy.orm import Session

from app.audit.repository import add_event

USER_REGISTERED = "USER_REGISTERED"
LOGIN_SUCCESS = "LOGIN_SUCCESS"
LOGIN_FAILURE = "LOGIN_FAILURE"


def record_security_event(
    db: Session, event_type: str, actor_user_id: int | None = None
) -> None:
    # Deliberately excludes credentials, tokens, and raw request data.
    add_event(db, event_type, actor_user_id, metadata={})
