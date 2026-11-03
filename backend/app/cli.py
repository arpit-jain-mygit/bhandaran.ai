# ---------------------------------------------------------------
# Command-line admin tools. Admins can't sign up through the app;
# they are created here (run from a laptop, against any database).
#
#   Local:  .venv/bin/python -m app.cli create-admin --email asha@example.com --name "Asha"
#   Dev:    DB_MODE=dsql DSQL_ENDPOINT=<endpoint> .venv/bin/python -m app.cli create-admin ...
#
# If the email already has an account, the ADMIN role is added to it.
# ---------------------------------------------------------------
import argparse
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import mask_email, normalize_email
from app.db import get_engine
from app.models import User, UserRole


def create_admin(email_raw: str, name: str | None) -> str:
    email = normalize_email(email_raw)
    with Session(get_engine()) as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, name=name)
            session.add(user)
        elif name and not user.name:
            user.name = name

        if "ADMIN" in user.role_names:
            return f"{mask_email(email)} is already an admin"
        user.roles.append(UserRole(role="ADMIN"))
        session.commit()
        return f"{mask_email(email)} is now an admin"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="bhandaran.ai admin")
    commands = parser.add_subparsers(dest="command", required=True)

    admin = commands.add_parser("create-admin", help="Create an admin, or make a user an admin")
    admin.add_argument("--email", required=True, help="Email address that will log in")
    admin.add_argument("--name", help="Display name (for new accounts)")

    args = parser.parse_args(argv)
    try:
        print(create_admin(args.email, args.name))
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
