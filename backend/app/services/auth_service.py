"""Password hashing, JWT creation, and reusable admin authentication."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import JWT_ACCESS_TOKEN_MINUTES, JWT_ALGORITHM, JWT_SECRET
from app.database import get_db
from app.models.models import Admin


bearer_scheme = HTTPBearer(auto_error=False)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode(
        "utf-8"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _jwt_secret() -> str:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured")
    return JWT_SECRET


def create_access_token(
    admin_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    expires = now + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=JWT_ACCESS_TOKEN_MINUTES)
    )
    return jwt.encode(
        {"sub": str(admin_id), "iat": now, "exp": expires},
        _jwt_secret(),
        algorithm=JWT_ALGORITHM,
    )


def authenticate_admin(database: Session, email: str, password: str) -> Admin | None:
    admin = database.scalar(
        select(Admin).where(Admin.email == normalize_email(email))
    )
    if admin is None or not verify_password(password, admin.password_hash):
        return None
    if admin.is_active != 1:
        return None
    return admin


def admin_to_public(admin: Admin, created_by_name: str | None = None) -> dict:
    return {
        "admin_id": admin.admin_id,
        "first_name": admin.first_name,
        "last_name": admin.last_name,
        "email": admin.email,
        "is_active": admin.is_active,
        "created_by": admin.created_by,
        "created_by_name": created_by_name,
        "created_at": admin.created_at,
    }


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    database: Session = Depends(get_db),
) -> Admin:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            _jwt_secret(),
            algorithms=[JWT_ALGORITHM],
        )
        admin_id = int(payload.get("sub", ""))
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        ) from error
    except (ExpiredSignatureError, InvalidTokenError, TypeError, ValueError):
        raise unauthorized

    admin = database.get(Admin, admin_id)
    if admin is None or admin.is_active != 1:
        raise unauthorized
    return admin
