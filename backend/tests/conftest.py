# ---------------------------------------------------------------
# Shared test setup (pytest loads this file automatically).
#
# Database tests run against a REAL local PostgreSQL test database
# (bhandaran_test), rebuilt from the migrations once per test run.
# This also proves the migrations work.
#
#   Local: createdb bhandaran_test   (once)
#   CI:    a postgres service container provides it
#
# Logged-in requests: three test users (admin, owner, renter) are
# created once; tests send their tokens with ADMIN_HEADERS,
# OWNER_HEADERS and RENTER_HEADERS.
# ---------------------------------------------------------------
import os

# Settings must be set BEFORE the app is imported (they are cached).
os.environ["DB_MODE"] = "local"
os.environ["LOCAL_DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://localhost:5432/bhandaran_test"
)
os.environ["APP_SECRET_KEY"] = "test-secret-key-not-for-real-use-0123456789"
os.environ["OTP_DELIVERY"] = "response"  # login tests read the code from the reply
os.environ["COOKIE_SECURE"] = "false"  # TestClient talks plain http

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.auth import create_session_token  # noqa: E402
from app.db import get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, UserRole  # noqa: E402

# Filled in by migrated_db (dicts, so tests can import them up front).
ADMIN_HEADERS: dict[str, str] = {}
OWNER_HEADERS: dict[str, str] = {}
RENTER_HEADERS: dict[str, str] = {}
TEST_USERS: dict[str, User] = {}


def make_user(session: Session, phone: str, name: str, *roles: str) -> User:
    user = User(phone=phone, name=name)
    for role in roles:
        user.roles.append(UserRole(role=role))
    session.add(user)
    session.flush()  # assigns user.id
    return user


@pytest.fixture(scope="session")
def migrated_db() -> None:
    """Rebuild the test database from scratch, then create the test users."""
    # Safety: this wipes the database, so refuse anything not named *_test.
    database_name = get_engine().url.database or ""
    if not database_name.endswith("_test"):
        pytest.exit(f"Refusing to wipe '{database_name}': test DB name must end with _test")

    # Drop everything left by earlier runs.
    with get_engine().begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    config = Config(str(Path(__file__).parent.parent / "alembic.ini"))
    command.upgrade(config, "head")

    # One user per role, logged in via Bearer tokens.
    with Session(get_engine(), expire_on_commit=False) as session:
        users = {
            "admin": make_user(session, "+919000000001", "Test Admin", "ADMIN"),
            "owner": make_user(session, "+919000000002", "Test Owner", "OWNER"),
            "renter": make_user(session, "+919000000003", "Test Renter", "RENTER"),
        }
        session.commit()
    TEST_USERS.update(users)
    for headers, user in (
        (ADMIN_HEADERS, users["admin"]),
        (OWNER_HEADERS, users["owner"]),
        (RENTER_HEADERS, users["renter"]),
    ):
        headers["Authorization"] = f"Bearer {create_session_token(user.id)}"


@pytest.fixture
def client(migrated_db) -> Iterator[TestClient]:
    """HTTP client for the app, backed by the migrated test database."""
    with TestClient(app) as test_client:
        yield test_client
