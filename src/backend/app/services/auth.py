import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.backend.app.core.security import create_access_token, get_user_by_email, hash_password, verify_password
from src.backend.app.models import User
from src.backend.app.schemas.auth import MemberRegister, TokenResponse, UserRead


def create_member(db: Session, payload: MemberRegister) -> User:
    email = payload.email.lower() if payload.email else None
    if email and get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered.",
        )

    user = User(
        name=payload.name,
        age=payload.age,
        email=email,
        password_hash=hash_password(payload.password),
        role="member",
        preferred_time_slots=json.dumps(payload.preferred_time_slots),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )
    return user


def issue_token(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(subject=str(user.id), role=user.role),
        role=user.role,
    )


def serialize_user(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        name=user.name,
        age=user.age,
        email=user.email,
        role=user.role,
        preferred_time_slots=parse_preferred_time_slots(user.preferred_time_slots),
        is_active=user.is_active,
    )


def parse_preferred_time_slots(value: str | None) -> list[int]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, int)]


def seed_admin_user(db: Session, email: str, password: str) -> None:
    normalized_email = email.lower()
    existing = get_user_by_email(db, normalized_email)
    if existing:
        return
    db.add(
        User(
            name="Local Admin",
            email=normalized_email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
    )

