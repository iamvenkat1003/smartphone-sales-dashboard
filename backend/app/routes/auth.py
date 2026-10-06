from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Admin
from app.schemas.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminPublic,
)
from app.services.auth_service import (
    admin_to_public,
    authenticate_admin,
    create_access_token,
    get_current_admin,
)


router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
def login(payload: AdminLoginRequest, database: Session = Depends(get_db)):
    admin = authenticate_admin(database, payload.email, payload.password)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token = create_access_token(admin.admin_id)
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        ) from error
    return {
        "access_token": token,
        "token_type": "bearer",
        "admin": admin_to_public(admin),
    }


@router.get("/me", response_model=AdminPublic)
def current_admin(admin: Admin = Depends(get_current_admin)):
    return admin_to_public(admin)
