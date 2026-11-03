# ---------------------------------------------------------------
# Tests for profiles and renter invites (M4).
# ---------------------------------------------------------------
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import profile as profile_api
from app.db import get_engine
from app.models import City, User
from tests.conftest import OWNER_HEADERS, RENTER_HEADERS, TEST_USERS


def new_email() -> str:
    return f"p{secrets.token_hex(4)}@example.test"


def some_city_id() -> str:
    with Session(get_engine()) as session:
        return str(session.scalar(select(City.id).limit(1)))


def request_code(client, email: str) -> str:
    return client.post("/api/auth/otp", json={"email": email}).json()["dev_code"]


def invite(client, email: str, name: str = "Sunita"):
    return client.post(
        "/api/profile/renters", json={"email": email, "name": name}, headers=OWNER_HEADERS
    )


# ---------- my profile ----------


def test_owner_sets_name_city_and_gst(client):
    city = some_city_id()
    body = {"name": "Kesar Traders", "city_id": city, "gst_number": "23abcde1234f1Z5"}

    response = client.put("/api/profile/me", json=body, headers=OWNER_HEADERS)

    assert response.status_code == 200
    profile = response.json()
    assert (profile["name"], profile["city_id"], profile["gst_number"]) == (
        "Kesar Traders",
        city,
        "23ABCDE1234F1Z5",  # stored in upper case
    )
    assert profile["city_name"]


def test_blank_gst_means_none(client):
    response = client.put(
        "/api/profile/me", json={"name": "Ravi", "gst_number": "  "}, headers=OWNER_HEADERS
    )
    assert response.json()["gst_number"] is None


def test_invalid_gst_is_rejected(client):
    response = client.put(
        "/api/profile/me", json={"name": "Ravi", "gst_number": "12345"}, headers=OWNER_HEADERS
    )
    assert response.status_code == 422


def test_unknown_city_is_rejected(client):
    response = client.put(
        "/api/profile/me",
        json={"name": "Ravi", "city_id": "00000000-0000-0000-0000-000000000000"},
        headers=OWNER_HEADERS,
    )
    assert response.status_code == 422


def test_renter_can_edit_their_own_profile(client):
    response = client.put("/api/profile/me", json={"name": "Meena"}, headers=RENTER_HEADERS)
    assert response.status_code == 200
    assert response.json()["roles"] == ["RENTER"]


def test_profile_needs_login(client):
    assert client.get("/api/profile/me").status_code == 401


# ---------- owner invites a renter ----------


def test_owner_invites_a_renter_by_email(client):
    email = new_email()
    response = invite(client, f"  {email.upper()} ")

    assert response.status_code == 201
    renter = response.json()
    assert (renter["email"], renter["status"], renter["roles"]) == (email, "UNCLAIMED", ["RENTER"])
    with Session(get_engine()) as session:
        row = session.scalar(select(User).where(User.email == email))
        assert row.invited_by_id == TEST_USERS["owner"].id


def test_inviting_an_existing_email_is_a_conflict(client):
    email = new_email()
    assert invite(client, email).status_code == 201
    assert invite(client, email).status_code == 409


def test_only_owners_can_invite(client):
    response = client.post(
        "/api/profile/renters",
        json={"email": new_email(), "name": "Sunita"},
        headers=RENTER_HEADERS,
    )
    assert response.status_code == 403


def test_invite_needs_a_valid_email(client):
    assert invite(client, "not-an-email").status_code == 422


def test_invited_renter_claims_the_account_with_a_code(client):
    email = new_email()
    assert invite(client, email).status_code == 201

    code = request_code(client, email)
    result = client.post("/api/auth/verify", json={"email": email, "code": code}).json()

    assert result["status"] == "logged_in"
    assert result["user"]["roles"] == ["RENTER"]
    with Session(get_engine()) as session:
        assert session.scalar(select(User.status).where(User.email == email)) == "ACTIVE"


def test_invite_email_is_sent_in_email_mode(client, monkeypatch):
    sent = []
    settings = profile_api.get_settings()
    monkeypatch.setattr(settings, "otp_delivery", "email")
    monkeypatch.setattr(profile_api, "send_invitation", lambda to, owner: sent.append((to, owner)))

    email = new_email()
    assert invite(client, email).status_code == 201
    assert [to for to, _ in sent] == [email]
    assert sent[0][1]  # the owner's name is passed along


def test_failed_invite_email_creates_no_account(client, monkeypatch):
    settings = profile_api.get_settings()
    monkeypatch.setattr(settings, "otp_delivery", "email")

    def refuse(to, owner):
        raise RuntimeError("Email could not be sent")

    monkeypatch.setattr(profile_api, "send_invitation", refuse)

    email = new_email()
    assert invite(client, email).status_code == 503
    with Session(get_engine()) as session:
        assert session.scalar(select(User.id).where(User.email == email)) is None
