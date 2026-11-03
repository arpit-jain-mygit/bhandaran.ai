# ---------------------------------------------------------------
# Tests for the Lambda entry point's keep-warm ping.
# The database engine is faked: no AWS or Postgres needed.
# ---------------------------------------------------------------
from contextlib import contextmanager

from sqlalchemy.exc import OperationalError

from app import lambda_handler


class FakeConnection:
    def __init__(self, db_up: bool) -> None:
        self.db_up = db_up
        self.queries: list[str] = []

    def execute(self, statement):
        if not self.db_up:
            raise OperationalError("SELECT 1", {}, Exception("connection refused"))
        self.queries.append(str(statement))


class FakeEngine:
    def __init__(self, db_up: bool = True) -> None:
        self.connection = FakeConnection(db_up)

    @contextmanager
    def connect(self):
        yield self.connection


def test_warmup_event_pings_database(monkeypatch):
    engine = FakeEngine()
    monkeypatch.setattr(lambda_handler, "get_engine", lambda: engine)

    result = lambda_handler.handler({"warmup": True}, None)

    assert result == {"warm": True}
    assert engine.connection.queries == ["SELECT 1"]


def test_warmup_reports_failure_without_raising(monkeypatch):
    monkeypatch.setattr(lambda_handler, "get_engine", lambda: FakeEngine(db_up=False))

    assert lambda_handler.handler({"warmup": True}, None) == {"warm": False}


def test_http_events_go_to_the_web_app(monkeypatch):
    calls = []
    monkeypatch.setattr(lambda_handler, "asgi_handler", lambda e, c: calls.append(e) or "ok")
    event = {"rawPath": "/api/health"}

    assert lambda_handler.handler(event, None) == "ok"
    assert calls == [event]
