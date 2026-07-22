from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.identity.dependencies import get_current_user
from app.identity.models import User
from app.identity.profile_service import delete_profile, get_profile, upsert_profile
from app.identity.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserProfileResponse,
    UserProfileUpsert,
    UserResponse,
)
from app.identity.security import create_access_token
from app.identity.service import DuplicateEmailError, InvalidCredentialsError, authenticate, register
from app.identity.verification_guard import VerificationCapacityError

router = APIRouter(tags=["identity"])


@router.post("/auth/register", response_model=UserResponse, status_code=201)
def register_user(data: RegisterRequest, db: Annotated[Session, Depends(get_db)]):
    try:
        return register(db, data.email, data.password)
    except DuplicateEmailError:
        raise HTTPException(status_code=409, detail="Email is already registered") from None


@router.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    try:
        user = authenticate(db, data.email, data.password)
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid email or password") from None
    except VerificationCapacityError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily busy",
        ) from None
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/users/me", response_model=UserResponse)
def current_user(user: Annotated[User, Depends(get_current_user)]):
    return user


@router.put("/users/me/profile", response_model=UserProfileResponse)
def update_current_user_profile(
    data: UserProfileUpsert,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return upsert_profile(db, user.id, data.resume_markdown)


@router.get("/users/me/profile", response_model=UserProfileResponse)
def read_current_user_profile(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    profile = get_profile(db, user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    return profile


@router.delete("/users/me/profile", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user_profile(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    if not delete_profile(db, user.id):
        raise HTTPException(status_code=404, detail="User profile not found")
