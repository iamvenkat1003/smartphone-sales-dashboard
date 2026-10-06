from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import CORS_ORIGINS
from app.database import get_db
from app.routes.admin import router as admin_router
from app.routes.analytics import router as analytics_router
from app.routes.auth import router as auth_router
from app.routes.phones import router as phones_router
from app.schemas.schemas import ApiStatusResponse, HealthResponse


app = FastAPI(title="Smartphone Sales Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CORS_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "PUT"],
    allow_headers=["Accept", "Authorization", "Content-Type"],
)

app.include_router(
    analytics_router,
    prefix="/api/analytics",
    tags=["Analytics"],
)
app.include_router(
    phones_router,
    prefix="/api/phones",
    tags=["Phones"],
)
app.include_router(
    auth_router,
    prefix="/api/auth",
    tags=["Authentication"],
)
app.include_router(
    admin_router,
    prefix="/api/admin",
    tags=["Admin"],
)


@app.get("/", response_model=ApiStatusResponse)
def api_status():
    return {
        "name": "Smartphone Sales Dashboard API",
        "status": "running",
    }


@app.get("/health", response_model=HealthResponse)
def database_health(database: Session = Depends(get_db)):
    try:
        database.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        ) from error

    return {
        "status": "healthy",
        "database": "connected",
    }
