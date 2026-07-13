from sqlalchemy.orm import Session

from app.audit.models import AuditLog


def add_event(
    db: Session, event_type: str, actor_user_id: int | None, metadata: dict[str, str]
) -> AuditLog:
    event = AuditLog(
        event_type=event_type, actor_user_id=actor_user_id, metadata_=metadata
    )
    db.add(event)
    return event
