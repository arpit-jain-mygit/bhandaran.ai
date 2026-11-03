# ---------------------------------------------------------------
# Tests for bounce and complaint handling (SES -> SNS -> Lambda).
# ---------------------------------------------------------------
import json
import secrets

from sqlalchemy.orm import Session

from app import email_sender
from app.config import get_settings
from app.db import get_engine
from app.lambda_handler import handler
from app.mail_events import addresses_to_suppress
from app.models import EmailSuppression
from tests.conftest import OWNER_HEADERS


def new_email() -> str:
    return f"b{secrets.token_hex(4)}@example.test"


def sns_event(message: dict) -> dict:
    """The shape AWS Lambda gets when SNS delivers a message."""
    return {
        "Records": [
            {"EventSource": "aws:sns", "Sns": {"Message": json.dumps(message)}},
        ]
    }


def bounce(email: str, kind: str = "Permanent") -> dict:
    return {
        "notificationType": "Bounce",
        "bounce": {"bounceType": kind, "bouncedRecipients": [{"emailAddress": email}]},
    }


def complaint(email: str) -> dict:
    return {
        "notificationType": "Complaint",
        "complaint": {"complainedRecipients": [{"emailAddress": email}]},
    }


def suppressed(email: str) -> bool:
    with Session(get_engine()) as session:
        return session.get(EmailSuppression, email) is not None


def test_permanent_bounce_is_suppressed():
    assert addresses_to_suppress(bounce("x@example.com")) == [("x@example.com", "BOUNCE")]


def test_temporary_bounce_is_not_suppressed():
    assert addresses_to_suppress(bounce("x@example.com", kind="Transient")) == []


def test_complaint_is_suppressed():
    assert addresses_to_suppress(complaint("x@example.com")) == [("x@example.com", "COMPLAINT")]


def test_configuration_set_reports_use_event_type():
    # The format SES sends for a configuration set (what the API uses).
    message = {
        "eventType": "Bounce",
        "bounce": {
            "bounceType": "Permanent",
            "bouncedRecipients": [{"emailAddress": "x@example.com"}],
        },
    }
    assert addresses_to_suppress(message) == [("x@example.com", "BOUNCE")]


def test_delivery_reports_are_ignored():
    assert addresses_to_suppress({"notificationType": "Delivery"}) == []


def test_lambda_records_a_bounce_and_stops_login_codes(client):
    email = new_email()
    result = handler(sns_event(bounce(email.upper())), None)

    assert result == {"suppressed": 1}
    assert suppressed(email)
    response = client.post("/api/auth/otp", json={"email": email})
    assert response.status_code == 422
    assert "another address" in response.json()["detail"]


def test_repeated_reports_are_stored_once(client):
    email = new_email()
    handler(sns_event(complaint(email)), None)
    assert handler(sns_event(complaint(email)), None) == {"suppressed": 0}


def test_invites_to_suppressed_addresses_are_refused(client):
    email = new_email()
    handler(sns_event(bounce(email)), None)

    response = client.post(
        "/api/profile/renters", json={"email": email, "name": "Sunita"}, headers=OWNER_HEADERS
    )
    assert response.status_code == 422


def test_sends_use_the_configuration_set(monkeypatch):
    sent = []

    class FakeSes:
        def send_email(self, **kwargs):
            sent.append(kwargs)

    monkeypatch.setattr(email_sender.boto3, "client", lambda *a, **k: FakeSes())
    settings = get_settings()
    monkeypatch.setattr(settings, "mail_configuration_set", "bhandaran-dev-mail")

    email_sender.send_email("x@example.com", "Hi", "Body")
    assert sent[0]["ConfigurationSetName"] == "bhandaran-dev-mail"


def test_sends_without_a_configuration_set_leave_it_out(monkeypatch):
    sent = []

    class FakeSes:
        def send_email(self, **kwargs):
            sent.append(kwargs)

    monkeypatch.setattr(email_sender.boto3, "client", lambda *a, **k: FakeSes())
    monkeypatch.setattr(get_settings(), "mail_configuration_set", "")

    email_sender.send_email("x@example.com", "Hi", "Body")
    assert "ConfigurationSetName" not in sent[0]
