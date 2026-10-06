import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

DATABASE_PATH = BACKEND_DIR / "smartphone_sales.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "120"))

CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)
