# ---------------------------------------------------------------
# Tests for the command line tools (app/cli.py): delete-admin.
# Each test makes its own accounts, so their emails are unique.
# ---------------------------------------------------------------
import uuid
from types import SimpleNamespace

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import cleanup, cli
from app.db import get_engine
from app.models import User, UserRole
from tests.conftest import make_user


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.test"


def account_exists(email: str) -> bool:
    with Session(get_engine()) as session:
        return session.scalar(select(User.id).where(User.email == email)) is not None


def test_delete_admin_preview_deletes_nothing(capsys):
    target = unique_email("gone-admin")
    with Session(get_engine()) as session:
        make_user(session, target, "Old Admin", "ADMIN")
        session.commit()

    code = cli.main(["delete-admin", "--email", target])

    assert code == 0
    output = capsys.readouterr().out
    assert "Nothing deleted" in output
    assert account_exists(target)


def test_delete_admin_with_yes_removes_the_account(capsys):
    target = unique_email("gone-admin")
    with Session(get_engine()) as session:
        make_user(session, target, "Old Admin", "ADMIN")
        session.commit()

    code = cli.main(["delete-admin", "--email", target, "--yes"])

    assert code == 0
    assert "Deleted." in capsys.readouterr().out
    assert not account_exists(target)


def test_delete_admin_refuses_someone_who_is_not_an_admin(capsys):
    target = unique_email("just-renter")
    with Session(get_engine()) as session:
        make_user(session, target, "Renter", "RENTER")
        session.commit()

    code = cli.main(["delete-admin", "--email", target, "--yes"])

    assert code == 1
    assert "is not an admin" in capsys.readouterr().err
    assert account_exists(target)


def test_delete_admin_refuses_the_last_admin(capsys):
    target = unique_email("last-admin")
    with Session(get_engine()) as session:
        make_user(session, target, "Last Admin", "ADMIN")
        # Pretend every other admin is gone, then put them back.
        others = select(UserRole).join(User).where(UserRole.role == "ADMIN", User.email != target)
        saved = [(row.user_id, row.role) for row in session.scalars(others)]
        session.execute(
            delete(UserRole).where(UserRole.id.in_([r.id for r in session.scalars(others)]))
        )
        session.commit()
    try:
        code = cli.main(["delete-admin", "--email", target, "--yes"])

        assert code == 1
        assert "only admin left" in capsys.readouterr().err
        assert account_exists(target)
    finally:
        with Session(get_engine()) as session:
            for user_id, role in saved:
                session.add(UserRole(user_id=user_id, role=role))
            session.commit()


def test_list_admins_shows_each_admin_once(capsys):
    email = unique_email("listed-admin")
    with Session(get_engine()) as session:
        make_user(session, email, "Listed Admin", "ADMIN", "OWNER")
        session.commit()

    assert cli.main(["list-admins"]) == 0

    lines = capsys.readouterr().out.splitlines()
    matching = [line for line in lines if line.startswith(email)]
    assert len(matching) == 1
    assert "name=Listed Admin" in matching[0]
    assert "roles=ADMIN,OWNER" in matching[0]


def test_delete_owner_removes_the_owner_account(capsys):
    target = unique_email("gone-owner")
    with Session(get_engine()) as session:
        make_user(session, target, "Old Owner", "OWNER")
        session.commit()

    assert cli.main(["delete-owner", "--email", target]) == 0
    assert "Nothing deleted" in capsys.readouterr().out
    assert account_exists(target)

    assert cli.main(["delete-owner", "--email", target, "--yes"]) == 0
    assert "Deleted." in capsys.readouterr().out
    assert not account_exists(target)


def test_delete_renter_refuses_an_owner(capsys):
    target = unique_email("not-a-renter")
    with Session(get_engine()) as session:
        make_user(session, target, "Owner", "OWNER")
        session.commit()

    code = cli.main(["delete-renter", "--email", target, "--yes"])

    assert code == 1
    assert "is not a renter" in capsys.readouterr().err
    assert account_exists(target)


def test_delete_renter_with_yes_removes_the_renter(capsys):
    target = unique_email("gone-renter")
    with Session(get_engine()) as session:
        make_user(session, target, "Old Renter", "RENTER")
        session.commit()

    assert cli.main(["delete-renter", "--email", target, "--yes"]) == 0
    assert "Deleted." in capsys.readouterr().out
    assert not account_exists(target)


def test_delete_owner_warns_when_the_account_has_other_roles(capsys):
    target = unique_email("owner-and-renter")
    with Session(get_engine()) as session:
        make_user(session, target, "Both", "OWNER", "RENTER")
        session.commit()

    cli.main(["delete-owner", "--email", target])

    assert "also has RENTER. It is deleted whole." in capsys.readouterr().out


def test_create_owner_adds_the_role_and_is_safe_to_repeat(capsys):
    email = unique_email("new-owner")

    assert cli.main(["create-owner", "--email", email, "--name", "New Owner"]) == 0
    assert cli.main(["create-owner", "--email", email]) == 0

    lines = capsys.readouterr().out.splitlines()
    assert "is now an owner" in lines[0]
    assert "is already an owner" in lines[1]


def test_list_renters_shows_the_renter(capsys):
    email = unique_email("listed-renter")
    with Session(get_engine()) as session:
        make_user(session, email, "Listed Renter", "RENTER")
        session.commit()

    assert cli.main(["list-renters"]) == 0

    assert any(line.startswith(email) for line in capsys.readouterr().out.splitlines())


def test_update_account_changes_name_and_suspends(capsys):
    email = unique_email("to-suspend")
    with Session(get_engine()) as session:
        make_user(session, email, "Before", "RENTER")
        session.commit()

    code = cli.main(
        [
            "update-account",
            "--email",
            email,
            "--role",
            "RENTER",
            "--name",
            "After",
            "--status",
            "SUSPENDED",
        ]
    )

    assert code == 0
    assert "status=SUSPENDED" in capsys.readouterr().out
    with Session(get_engine()) as session:
        user = session.scalar(select(User).where(User.email == email))
        assert user.name == "After" and user.status == "SUSPENDED"


def test_update_account_needs_something_to_change(capsys):
    email = unique_email("nothing-to-change")
    with Session(get_engine()) as session:
        make_user(session, email, "Renter", "RENTER")
        session.commit()

    code = cli.main(["update-account", "--email", email, "--role", "RENTER"])

    assert code == 1
    assert "Give --name and/or --status" in capsys.readouterr().err


def test_delete_refuses_when_photo_files_cannot_be_removed(capsys, monkeypatch):
    target = unique_email("has-photos")
    with Session(get_engine()) as session:
        make_user(session, target, "Has Photos", "RENTER")
        session.commit()
    chosen = cleanup.Plan(accounts=["ha***@example.test"], photo_keys=["warehouses/x/y.jpg"])
    monkeypatch.setattr(cleanup, "plan", lambda *args, **kwargs: chosen)
    monkeypatch.setattr(cli, "get_settings", lambda: SimpleNamespace(photo_bucket=""))

    code = cli.main(["delete-renter", "--email", target, "--yes"])

    assert code == 1
    assert "Set PHOTO_BUCKET" in capsys.readouterr().err
    assert account_exists(target)
