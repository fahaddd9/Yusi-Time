"""
seed_superadmin.py — Operator tool for Phase 1.5

Creates a Super Admin user account OR promotes an existing user to Super Admin.

Usage:
    # Create a new super admin:
    poetry run python seed_superadmin.py --email admin@yusitime.com --password "SecurePass123!"

    # Promote an existing user by email:
    poetry run python seed_superadmin.py --email user@example.com --promote-only

IMPORTANT:
    - This script is an operator-only tool. It is NEVER exposed via any API.
    - is_superadmin is only settable via direct DB access (MASTER_PROMPT §11).
    - Run from the backend/ directory with the .env file present.
    - Do NOT commit actual credentials to version control.
"""

import asyncio
import argparse
import sys
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Ensure app modules are importable
from app.core.config import get_settings
from app.core.security import hash_password
from app.core.database import Base
from app.models.user import User


async def seed(email: str, password: str | None, promote_only: bool) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        # Look up existing user by lowercase email
        result = await db.execute(
            select(User).where(func.lower(User.email) == email.lower())
        )
        existing: User | None = result.scalar_one_or_none()

        if existing:
            if existing.is_superadmin:
                print(f"[INFO] {email} is already a Super Admin. Nothing to do.")
                return
            existing.is_superadmin = True
            await db.commit()
            print(f"[OK] Promoted existing user '{email}' to Super Admin.")
            return

        # promote_only but user doesn't exist
        if promote_only:
            print(f"[ERROR] No user found with email '{email}'. Cannot promote-only.")
            sys.exit(1)

        if not password:
            print("[ERROR] --password is required when creating a new Super Admin.")
            sys.exit(1)

        # Create a brand-new Super Admin user
        sa_user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            full_name="Super Admin",
            is_active=True,
            is_superadmin=True,  # Direct set — this is the only sanctioned path
        )
        db.add(sa_user)
        await db.commit()
        print(f"[OK] Created Super Admin account for '{email}'.")
        print(f"     User ID: {sa_user.id}")
        print("[REMINDER] Store the password securely. It cannot be recovered.")

    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed or promote a Super Admin user.")
    parser.add_argument("--email", required=True, help="Email address for the Super Admin account.")
    parser.add_argument("--password", default=None, help="Password (required unless --promote-only).")
    parser.add_argument(
        "--promote-only",
        action="store_true",
        help="Only promote an existing user to Super Admin (do not create).",
    )
    args = parser.parse_args()
    asyncio.run(seed(args.email, args.password, args.promote_only))


if __name__ == "__main__":
    main()
