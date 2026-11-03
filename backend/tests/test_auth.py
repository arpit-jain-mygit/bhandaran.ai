# ---------------------------------------------------------------
# Tests for email-OTP login (M3): codes, limits, sign-up, sessions.
# Each test uses its own random email address so limits don't clash.
# ---------------------------------------------------------------
import secrets
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import auth
from app.api import auth as auth_api
from app.cli import create_admin
from app.db import get_engine
from app.models import OtpChallenge, User


def new_email() -> str:
    """Random, unique test address, e.g. u3f9a1c2@example.test."""
    return f"u{secrets.token_hex(4)}@example.test"


def request_code(client, email: str) -> str:
    response = client.post("/api/auth/otp", json={"email": email})
    assert response.status_code == 202
    return response.json()["dev_code"]


def wrong(code: str) -> str:
    """A 6-digit code guaranteed to differ from `code`."""
    return f"{(int(code) + 1) % 1_000_000:06d}"


def sign_up(client, email: str, role: str = "OWNER", name: str = "Ravi"):
    code = request_code(client, email)
    verified = client.post("/api/auth/verify", json={"email": email, "code": code}).json()
    return client.post(
        "/api/auth/signup",
        json={"signup_token": verified["signup_token"], "name": name, "role": role},
    )


# ---------- email addresses ----------


@pytest.mark.parametrize(
    "raw", ["asha@example.com", "  Asha@Example.COM  ", "a.b+c@sub.example.in"]
)
def test_common_email_formats_are_accepted(raw):
    assert auth.normalize_email(raw) == raw.strip().lower()


@pytest.mark.parametrize("raw", ["", "asha", "asha@", "@example.com", "a b@example.com", "x@y"])
def test_invalid_emails_are_rejected(raw):
    with pytest.raises(ValueError):
        auth.normalize_email(raw)


def test_email_is_masked_in_logs():
    assert auth.mask_email("asha@example.com") == "as***@example.com"


# ---------- sign-up and login ----------


def test_new_email_signs_up_and_is_logged_in_by_cookie(client):
    email = new_email()
    response = sign_up(client, email, role="RENTER", name="Sunita")
    assert response.status_code == 201
    assert "bh_session" in response.cookies

    me = client.get("/api/auth/me").json()
    assert (me["name"], me["email"]) == ("Sunita", email)
    assert me["roles"] == ["RENTER"]


def test_existing_user_logs_in_directly(client):
    email = new_email()
    sign_up(client, email)
    client.post("/api/auth/logout")

    code = request_code(client, email)
    result = client.post("/api/auth/verify", json={"email": email, "code": code}).json()
    assert result["status"] == "logged_in"
    assert result["user"]["email"] == email


def test_email_case_does_not_create_a_second_account(client):
    email = new_email()
    sign_up(client, email)
    client.post("/api/auth/logout")

    code = request_code(client, email.upper())
    result = client.post("/api/auth/verify", json={"email": email, "code": code}).json()
    assert result["status"] == "logged_in"


def test_nobody_can_sign_up_as_admin(client):
    email = new_email()
    code = request_code(client, email)
    token = client.post("/api/auth/verify", json={"email": email, "code": code}).json()[
        "signup_token"
    ]
    response = client.post(
        "/api/auth/signup", json={"signup_token": token, "name": "Eve", "role": "ADMIN"}
    )
    assert response.status_code == 422


def test_signup_token_cannot_create_a_second_account(client):
    email = new_email()
    code = request_code(client, email)
    token = client.post("/api/auth/verify", json={"email": email, "code": code}).json()[
        "signup_token"
    ]
    body = {"signup_token": token, "name": "Ravi", "role": "OWNER"}
    assert client.post("/api/auth/signup", json=body).status_code == 201
    assert client.post("/api/auth/signup", json=body).status_code == 409

    with Session(get_engine()) as session:
        count = len(session.scalars(select(User).where(User.email == email)).all())
    assert count == 1


def test_logout_ends_the_session(client):
    sign_up(client, new_email())
    assert client.get("/api/auth/me").status_code == 200

    assert client.post("/api/auth/logout").status_code == 204
    client.cookies.clear()
    assert client.get("/api/auth/me").status_code == 401


# ---------- code rules ----------


def test_wrong_code_is_rejected(client):
    email = new_email()
    code = request_code(client, email)
    response = client.post("/api/auth/verify", json={"email": email, "code": wrong(code)})
    assert response.status_code == 400


def test_code_stops_working_after_five_wrong_guesses(client):
    email = new_email()
    code = request_code(client, email)
    for _ in range(5):
        client.post("/api/auth/verify", json={"email": email, "code": wrong(code)})

    response = client.post("/api/auth/verify", json={"email": email, "code": code})
    assert response.status_code == 429


def test_code_can_be_used_only_once(client):
    email = new_email()
    code = request_code(client, email)
    client.post("/api/auth/verify", json={"email": email, "code": code})

    again = client.post("/api/auth/verify", json={"email": email, "code": code})
    assert again.status_code == 400


def test_expired_code_is_rejected(client):
    email = new_email()
    code = request_code(client, email)
    with Session(get_engine()) as session:
        session.execute(
            update(OtpChallenge)
            .where(OtpChallenge.email == email)
            .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
        session.commit()

    response = client.post("/api/auth/verify", json={"email": email, "code": code})
    assert response.status_code == 400


def test_at_most_five_codes_per_hour(client):
    email = new_email()
    for _ in range(5):
        request_code(client, email)
    response = client.post("/api/auth/otp", json={"email": email})
    assert response.status_code == 429


def test_code_is_never_returned_outside_local_mode(monkeypatch):
    settings = auth_api.get_settings()
    monkeypatch.setattr(settings, "db_mode", "dsql")
    assert auth_api.deliver_code("asha@example.com", "123456") is None


def test_email_mode_sends_the_code_and_never_returns_it(monkeypatch):
    sent = []
    settings = auth_api.get_settings()
    monkeypatch.setattr(settings, "otp_delivery", "email")
    monkeypatch.setattr(
        auth_api, "send_login_code", lambda to, code, minutes: sent.append((to, code, minutes))
    )

    assert auth_api.deliver_code("asha@example.com", "123456") is None
    assert sent == [("asha@example.com", "123456", 5)]


def test_email_failure_returns_503_and_stores_no_code(client, monkeypatch):
    settings = auth_api.get_settings()
    monkeypatch.setattr(settings, "otp_delivery", "email")

    def refuse(to, code, minutes):
        raise RuntimeError("Email could not be sent")

    monkeypatch.setattr(auth_api, "send_login_code", refuse)
    email = new_email()
    response = client.post("/api/auth/otp", json={"email": email})
    assert response.status_code == 503

    with Session(get_engine()) as session:
        stored = session.scalars(select(OtpChallenge).where(OtpChallenge.email == email)).all()
    assert stored == []


# ---------- sessions ----------


def test_tampered_token_is_rejected(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert response.status_code == 401


def test_signup_token_cannot_be_used_as_a_session(client):
    email = new_email()
    code = request_code(client, email)
    token = client.post("/api/auth/verify", json={"email": email, "code": code}).json()[
        "signup_token"
    ]
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_suspended_user_is_logged_out_immediately(client):
    email = new_email()
    sign_up(client, email)
    assert client.get("/api/auth/me").status_code == 200

    with Session(get_engine()) as session:
        session.execute(update(User).where(User.email == email).values(status="SUSPENDED"))
        session.commit()

    assert client.get("/api/auth/me").status_code == 401


# ---------- admin command ----------


def test_create_admin_command_adds_the_admin_role(client):
    email = new_email()
    sign_up(client, email, role="OWNER")

    message = create_admin(email, None)

    assert "now an admin" in message
    assert sorted(client.get("/api/auth/me").json()["roles"]) == ["ADMIN", "OWNER"]
    assert "already an admin" in create_admin(email, None)
