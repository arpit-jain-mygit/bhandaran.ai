# ---------------------------------------------------------------
# Tests for GET /api/health.
# The real database is replaced by a fake session, so these tests
# run anywhere (CI included) without PostgreSQL or AWS.
# ---------------------------------------------------------------
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_session
from app.main import app


class FakeSession:
    """Stands in for a SQLAlchemy Session; can pretend the DB is down."""

    def __init__(self, db_up: bool) -> None:
        self.db_up = db_up

    def execute(self, _statement):
        if not self.db_up:
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))
        return None


def client_with(db_up: bool) -> TestClient:
    """Build a test client whose database is up or down."""

    def fake_session() -> Iterator[FakeSession]:
        yield FakeSession(db_up)

    app.dependency_overrides[get_session] = fake_session
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_overrides() -> Iterator[None]:
    """Remove fakes after each test so tests don't affect each other."""
    yield
    app.dependency_overrides.clear()


def test_health_ok_when_database_reachable() -> None:
    response = client_with(db_up=True).get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"
    assert body["version"]


def test_health_degraded_when_database_down() -> None:
    response = client_with(db_up=False).get("/api/health")

    # The API itself still answers (200) but reports the DB problem.
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"] == "unreachable"
