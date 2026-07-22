from sqlalchemy.orm import Session

from app.identity.profile_models import UserProfile
from app.identity.profile_parser import parse_resume_markdown


def get_profile(db: Session, user_id: int) -> UserProfile | None:
    return db.get(UserProfile, user_id)


def upsert_profile(db: Session, user_id: int, resume_markdown: str) -> UserProfile:
    parsed = parse_resume_markdown(resume_markdown)
    profile = get_profile(db, user_id)
    if profile is None:
        profile = UserProfile(user_id=user_id, resume_markdown=resume_markdown, **parsed)
        db.add(profile)
    else:
        profile.resume_markdown = resume_markdown
        for field, value in parsed.items():
            setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


def delete_profile(db: Session, user_id: int) -> bool:
    profile = get_profile(db, user_id)
    if profile is None:
        return False
    db.delete(profile)
    db.commit()
    return True
