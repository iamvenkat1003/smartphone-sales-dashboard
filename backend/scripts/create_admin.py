"""Interactively create the first/root administrator.

Run from backend/:  python scripts/create_admin.py
"""

from getpass import getpass
from pathlib import Path
import re
import sys

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models.models import Admin  # noqa: E402
from app.services.auth_service import hash_password, normalize_email  # noqa: E402


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def prompt_required(label: str) -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value
        print(f"{label} is required.")


def main() -> int:
    database = SessionLocal()
    try:
        if database.scalar(select(func.count()).select_from(Admin)) > 0:
            print("An admin already exists. Create additional admins in the admin panel.")
            return 1

        first_name = prompt_required("First name")
        last_name = prompt_required("Last name")
        email = normalize_email(prompt_required("Email"))
        if not EMAIL_PATTERN.match(email):
            print("Enter a valid email address.")
            return 1

        password = getpass("Password (minimum 8 characters): ")
        confirmation = getpass("Confirm password: ")
        if len(password) < 8 or len(password.encode("utf-8")) > 72:
            print("Password must be 8–72 bytes.")
            return 1
        if password != confirmation:
            print("Passwords do not match.")
            return 1

        admin = Admin(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hash_password(password),
            is_active=1,
            created_by=None,
        )
        database.add(admin)
        database.commit()
        print(f"Root admin created for {email}.")
        return 0
    except IntegrityError:
        database.rollback()
        print("An admin with that email already exists.")
        return 1
    finally:
        database.close()


if __name__ == "__main__":
    raise SystemExit(main())
