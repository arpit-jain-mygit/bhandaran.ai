# ---------------------------------------------------------------
# Command-line account tools (CRUD for admins, owners and renters).
# Run from a laptop, against any database. Owners and renters can
# also sign up in the app; these commands are for admins and for
# setting up or cleaning up accounts by hand.
#
#   Local:  .venv/bin/python -m app.cli create-admin --email asha@example.com --name "Asha"
#   Dev:    DB_MODE=dsql DSQL_ENDPOINT=<endpoint> .venv/bin/python -m app.cli create-admin ...
#
#   Create   create-admin | create-owner | create-renter   --email ... [--name ...]
#            (an existing account gets the role added; nothing else changes)
#   Read     list-admins | list-owners | list-renters
#   Update   update-account --email ... --role ADMIN|OWNER|RENTER
#            [--name ...] [--status ACTIVE|SUSPENDED]
#   Delete   delete-admin | delete-owner | delete-renter  --email ... [--yes]
#            (preview by default; --yes deletes, with the same cascade as the
#             delete test data page: godowns, bookings, photos, codes, settings)
# ---------------------------------------------------------------
import argparse
import sys

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import cleanup
from app.auth import mask_email, normalize_email
from app.config import get_settings
from app.db import get_engine
from app.models import User, UserRole

ROLE_NAMES = {"ADMIN": "an admin", "OWNER": "an owner", "RENTER": "a renter"}
ROLE_PLURALS = {"ADMIN": "admins", "OWNER": "owners", "RENTER": "renters"}
UPDATABLE_STATUSES = ("ACTIVE", "SUSPENDED")  # UNCLAIMED is set by the app only


def grant_role(email_raw: str, name: str | None, role: str) -> str:
    """Create the account if needed, then add the role if it's missing."""
    email = normalize_email(email_raw)
    with Session(get_engine()) as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, name=name)
            session.add(user)
        elif name and not user.name:
            user.name = name

        if role in user.role_names:
            return f"{mask_email(email)} is already {ROLE_NAMES[role]}"
        user.roles.append(UserRole(role=role))
        session.commit()
        return f"{mask_email(email)} is now {ROLE_NAMES[role]}"


def create_admin(email_raw: str, name: str | None) -> str:
    return grant_role(email_raw, name, "ADMIN")


def list_accounts(role: str) -> list[str]:
    """One line per account with this role, oldest first."""
    with Session(get_engine()) as session:
        users = session.scalars(
            select(User).join(UserRole).where(UserRole.role == role).order_by(User.created_at)
        ).all()
        return [
            f"{user.email}  name={user.name or '-'}  status={user.status}  "
            f"created={user.created_at:%Y-%m-%d}  roles={','.join(user.role_names)}"
            for user in users
        ] or [f"No {ROLE_PLURALS[role]} yet."]


def update_account(email_raw: str, role: str, name: str | None, status: str | None) -> list[str]:
    """Change the name and/or status of an account that has this role."""
    if name is None and status is None:
        raise ValueError("Give --name and/or --status to change")
    if status is not None and status not in UPDATABLE_STATUSES:
        raise ValueError(f"Status must be one of {', '.join(UPDATABLE_STATUSES)}")

    email = normalize_email(email_raw)
    with Session(get_engine()) as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is None or role not in user.role_names:
            raise ValueError(f"{mask_email(email)} is not {ROLE_NAMES[role]}")
        if status == "SUSPENDED" and role == "ADMIN" and user.status == "ACTIVE":
            active_others = session.scalar(
                select(func.count(func.distinct(User.id)))
                .join(UserRole)
                .where(UserRole.role == "ADMIN", User.status == "ACTIVE", User.id != user.id)
            )
            if active_others == 0:
                raise ValueError("Refusing: this is the only active admin left")

        changes = []
        if name is not None:
            user.name = name
            changes.append(f"name={name}")
        if status is not None:
            user.status = status
            changes.append(f"status={status}")
        session.commit()
    return [f"Updated {mask_email(email)}: {', '.join(changes)}"]


def admin_removal_summary(chosen: cleanup.Plan) -> list[str]:
    return [
        f"Accounts: {', '.join(chosen.accounts) or 'none'}",
        f"Godowns: {len(chosen.warehouse_ids)}",
        f"Bookings: {chosen.bookings}",
        f"Photos: {len(chosen.photo_keys)} (files are removed from storage too)",
        f"Login codes: {chosen.login_codes}",
        f"Owner settings: {chosen.owner_settings}",
        f"Renters released from this owner: {chosen.invitees_released}",
    ]


def delete_account(email_raw: str, role: str, confirmed: bool) -> list[str]:
    """
    Remove an account that has the given role, and everything that
    belongs to it (same rules as the delete test data page). Without
    confirmed=True nothing is deleted: the lines returned are the preview.
    """
    email = normalize_email(email_raw)
    with Session(get_engine()) as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is None or role not in user.role_names:
            raise ValueError(f"{mask_email(email)} is not {ROLE_NAMES[role]}")
        if role == "ADMIN":
            other_admins = session.scalar(
                select(func.count(func.distinct(UserRole.user_id))).where(
                    UserRole.role == "ADMIN", UserRole.user_id != user.id
                )
            )
            if other_admins == 0:
                raise ValueError("Refusing: this is the only admin left. Create another first.")

        chosen = cleanup.plan(session, protected_email=None, raw_emails=[email], warehouse_ids=[])
        lines = admin_removal_summary(chosen)
        others = [name for name in user.role_names if name != role]
        if others:
            lines.append(f"Note: this account also has {', '.join(others)}. It is deleted whole.")
        if not confirmed:
            return [*lines, "Nothing deleted. Run again with --yes to delete."]
        if chosen.photo_keys and not get_settings().photo_bucket:
            # Without the bucket name the photo files could not be removed,
            # so refuse before the photo rows are deleted.
            raise ValueError(
                f"Set PHOTO_BUCKET to the photos bucket to remove {len(chosen.photo_keys)} "
                "photo file(s) too, then run again"
            )

        photo_keys = cleanup.remove(session, chosen)
        session.commit()
    failed = cleanup.delete_photo_files(photo_keys)
    if failed:
        lines.append(f"Warning: {failed} photo file(s) could not be removed from storage.")
    return [*lines, "Deleted."]


def delete_admin(email_raw: str, confirmed: bool) -> list[str]:
    return delete_account(email_raw, "ADMIN", confirmed)


def delete_owner(email_raw: str, confirmed: bool) -> list[str]:
    return delete_account(email_raw, "OWNER", confirmed)


def delete_renter(email_raw: str, confirmed: bool) -> list[str]:
    return delete_account(email_raw, "RENTER", confirmed)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="bhandaran.ai accounts")
    commands = parser.add_subparsers(dest="command", required=True)

    for role, label in (("ADMIN", "admin"), ("OWNER", "owner"), ("RENTER", "renter")):
        create = commands.add_parser(f"create-{label}", help=f"Create {ROLE_NAMES[role]} account")
        create.add_argument("--email", required=True, help="Email address that will log in")
        create.add_argument("--name", help="Display name (for new accounts)")

        commands.add_parser(f"list-{label}s", help=f"Show every {label} account")

        remove = commands.add_parser(f"delete-{label}", help=f"Remove {ROLE_NAMES[role]} and data")
        remove.add_argument("--email", required=True, help=f"{label.title()} email to remove")
        remove.add_argument("--yes", action="store_true", help="Actually delete (default: preview)")

    update = commands.add_parser("update-account", help="Change an account's name or status")
    update.add_argument("--email", required=True, help="Account email address")
    update.add_argument("--role", required=True, choices=["ADMIN", "OWNER", "RENTER"])
    update.add_argument("--name", help="New display name")
    update.add_argument("--status", choices=UPDATABLE_STATUSES, help="SUSPENDED blocks login")
    return parser


def run(args: argparse.Namespace) -> list[str]:
    command = args.command
    if command.startswith("create-"):
        role = {"admin": "ADMIN", "owner": "OWNER", "renter": "RENTER"}[command.split("-")[1]]
        return [grant_role(args.email, args.name, role)]
    if command.startswith("list-"):
        role = {"admins": "ADMIN", "owners": "OWNER", "renters": "RENTER"}[command.split("-")[1]]
        return list_accounts(role)
    if command == "update-account":
        return update_account(args.email, args.role, args.name, args.status)
    role = command.split("-")[1].upper()
    delete = {"ADMIN": delete_admin, "OWNER": delete_owner, "RENTER": delete_renter}[role]
    return delete(args.email, confirmed=args.yes)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        for line in run(args):
            print(line)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
