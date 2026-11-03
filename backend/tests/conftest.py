# ---------------------------------------------------------------
# Shared test setup (pytest loads this file automatically).
#
# Database tests run against a REAL local PostgreSQL test database
# (bhandaran_test), rebuilt from the migrations once per test run.
# This also proves the migrations work.
#
#   Local: createdb bhandaran_test   (once)
#   CI:    a postgres service container provides it
# ---------------------------------------------------------------
import os

# Settings must be set BEFORE the app is imported (they are cached).
os.environ["DB_MODE"] = "local"
os.environ["LOCAL_DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://localhost:5432/bhandaran_test"
)
os.environ["ADMIN_API_KEY"] = "test-admin-key"

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db import get_engine  # noqa: E402
from app.main import app  # noqa: E402

ADMIN_HEADERS = {"X-Admin-Key": "test-admin-key"}


@pytest.fixture(scope="session")
def migrated_db() -> None:
    """Rebuild the test database from scratch: wipe it, then run all migrations."""
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


@pytest.fixture
def client(migrated_db) -> Iterator[TestClient]:
    """HTTP client for the app, backed by the migrated test database."""
    with TestClient(app) as test_client:
        yield test_client
