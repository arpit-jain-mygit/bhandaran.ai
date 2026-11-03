# ---------------------------------------------------------------
# Tests for phone-OTP login (M3): codes, limits, sign-up, sessions.
# Each test uses its own random phone number so limits don't clash.
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


def new_phone() -> str:
    """Random valid Indian mobile, e.g. 9812345678."""
    return f"98{secrets.randbelow(10**8):08d}"


def request_code(client, phone: str) -> str:
    response = client.post("/api/auth/otp", json={"phone": phone})
    assert response.status_code == 202
    return response.json()["dev_code"]


def wrong(code: str) -> str:
    """A 6-digit code guaranteed to differ from `code`."""
    return f"{(int(code) + 1) % 1_000_000:06d}"


def sign_up(client, phone: str, role: str = "OWNER", name: str = "Ravi"):
    code = request_code(client, phone)
    verified = client.post("/api/auth/verify", json={"phone": phone, "code": code}).json()
    return client.post(
        "/api/auth/signup",
        json={"signup_token": verified["signup_token"], "name": name, "role": role},
    )


# ---------- phone numbers ----------


@pytest.mark.parametrize(
    "raw", ["9826012345", "+91 98260 12345", "+91-9826012345", "09826012345", "919826012345"]
)
def test_common_phone_formats_are_accepted(raw):
    assert auth.normalize_phone(raw) == "+919826012345"


@pytest.mark.parametrize("raw", ["12345", "5826012345", "98260123456", "abcdefghij", ""])
def test_invalid_phones_are_rejected(raw):
    with pytest.raises(ValueError):
        auth.normalize_phone(raw)


def test_phone_is_masked_in_logs():
    assert auth.mask_phone("+919826012345") == "+91******2345"


# ---------- sign-up and login ----------


def test_new_phone_signs_up_and_is_logged_in_by_cookie(client):
    phone = new_phone()
    response = sign_up(client, phone, role="RENTER", name="Sunita")

    assert response.status_code == 201
    assert response.json()["roles"] == ["RENTER"]
    assert "bh_session" in response.cookies

    # The cookie alone identifies the user from now on.
    me = client.get("/api/auth/me").json()
    assert (me["name"], me["phone"]) == ("Sunita", f"+91{phone}")


def test_existing_user_logs_in_directly(client):
    phone = new_phone()
    sign_up(client, phone)
    client.cookies.clear()

    code = request_code(client, phone)
    result = client.post("/api/auth/verify", json={"phone": phone, "code": code}).json()

    assert result["status"] == "logged_in"
    assert result["user"]["roles"] == ["OWNER"]


def test_nobody_can_sign_up_as_admin(client):
    phone = new_phone()
    code = request_code(client, phone)
    token = client.post("/api/auth/verify", json={"phone": phone, "code": code}).json()[
        "signup_token"
    ]

    response = client.post(
        "/api/auth/signup", json={"signup_token": token, "name": "Eve", "role": "ADMIN"}
    )
    assert response.status_code == 422


def test_signup_token_cannot_create_a_second_account(client):
    phone = new_phone()
    code = request_code(client, phone)
    token = client.post("/api/auth/verify", json={"phone": phone, "code": code}).json()[
        "signup_token"
    ]
    body = {"signup_token": token, "name": "Ravi", "role": "OWNER"}

    first = client.post("/api/auth/signup", json=body)
    second = client.post("/api/auth/signup", json=body)  # replayed token

    assert (first.status_code, second.status_code) == (201, 409)
    with Session(get_engine()) as session:
        count = len(session.scalars(select(User).where(User.phone == f"+91{phone}")).all())
    assert count == 1


def test_logout_ends_the_session(client):
    sign_up(client, new_phone())
    assert client.get("/api/auth/me").status_code == 200

    client.post("/api/auth/logout")

    assert client.get("/api/auth/me").status_code == 401


# ---------- code rules ----------


def test_wrong_code_is_rejected(client):
    phone = new_phone()
    code = request_code(client, phone)

    response = client.post("/api/auth/verify", json={"phone": phone, "code": wrong(code)})

    assert response.status_code == 400


def test_code_stops_working_after_five_wrong_guesses(client):
    phone = new_phone()
    code = request_code(client, phone)
    for _ in range(5):
        client.post("/api/auth/verify", json={"phone": phone, "code": wrong(code)})

    # Even the right code is refused now.
    response = client.post("/api/auth/verify", json={"phone": phone, "code": code})
    assert response.status_code == 429


def test_code_can_be_used_only_once(client):
    phone = new_phone()
    code = request_code(client, phone)
    client.post("/api/auth/verify", json={"phone": phone, "code": code})

    again = client.post("/api/auth/verify", json={"phone": phone, "code": code})
    assert again.status_code == 400


def test_expired_code_is_rejected(client):
    phone = new_phone()
    code = request_code(client, phone)
    with Session(get_engine()) as session:
        session.execute(
            update(OtpChallenge)
            .where(OtpChallenge.phone == f"+91{phone}")
            .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
        session.commit()

    response = client.post("/api/auth/verify", json={"phone": phone, "code": code})
    assert response.status_code == 400


def test_at_most_five_codes_per_hour(client):
    phone = new_phone()
    for _ in range(5):
        request_code(client, phone)

    response = client.post("/api/auth/otp", json={"phone": phone})
    assert response.status_code == 429


def test_code_is_never_returned_outside_local_mode(monkeypatch):
    settings = auth_api.get_settings()
    monkeypatch.setattr(settings, "db_mode", "dsql")
    assert auth_api.deliver_code("+919826012345", "123456") is None


# ---------- sessions ----------


def test_tampered_token_is_rejected(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert response.status_code == 401


def test_signup_token_cannot_be_used_as_a_session(client):
    token = auth.create_signup_token("+919826012345")
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_suspended_user_is_logged_out_immediately(client):
    phone = new_phone()
    sign_up(client, phone)
    assert client.get("/api/auth/me").status_code == 200

    with Session(get_engine()) as session:
        session.execute(update(User).where(User.phone == f"+91{phone}").values(status="SUSPENDED"))
        session.commit()

    assert client.get("/api/auth/me").status_code == 401


# ---------- admin command ----------


def test_create_admin_command_adds_the_admin_role(client):
    phone = new_phone()
    sign_up(client, phone, role="OWNER")

    message = create_admin(phone, None)

    assert "now an admin" in message
    assert sorted(client.get("/api/auth/me").json()["roles"]) == ["ADMIN", "OWNER"]
    assert "already an admin" in create_admin(phone, None)
