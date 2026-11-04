# ---------------------------------------------------------------
# Tests for deleting test data (admin only): preview, delete, and
# the rules (confirm word, own account, unknown items, photos).
# Each test makes its own accounts, so their emails are unique.
# ---------------------------------------------------------------
import datetime
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_session_token
from app.db import get_engine
from app.models import Booking, OwnerSetting, User, Warehouse, WarehousePhoto
from tests.conftest import ADMIN_HEADERS, OWNER_HEADERS, RENTER_HEADERS, make_user
from tests.test_warehouse import DELETED, STORED, add_photo, create, fake_s3  # noqa: F401

BASE = "/api/admin/test-data"


def headers_for(user_id) -> dict:
    return {"Authorization": f"Bearer {create_session_token(user_id)}"}


def user_exists(email: str) -> bool:
    with Session(get_engine()) as session:
        return session.scalar(select(User.id).where(User.email == email)) is not None


@pytest.fixture
def seeded(client):
    """An owner with a godown (photo + booking), a renter, and an invitee."""
    tag = uuid.uuid4().hex[:8]
    emails = {
        "owner": f"owner-{tag}@example.test",
        "renter": f"renter-{tag}@example.test",
        "invitee": f"invitee-{tag}@example.test",
    }
    with Session(get_engine(), expire_on_commit=False) as session:
        owner = make_user(session, emails["owner"], "Cleanup Owner", "OWNER")
        renter = make_user(session, emails["renter"], "Cleanup Renter", "RENTER")
        invitee = make_user(session, emails["invitee"], "Invitee", "RENTER")
        invitee.invited_by_id = owner.id
        session.add(OwnerSetting(owner_id=owner.id, key="BOOKING_RULE", value="true"))
        session.commit()
        owner_id, renter_id = owner.id, renter.id

    godown = create(client, headers=headers_for(owner_id)).json()
    add_photo(client, godown["id"], headers=headers_for(owner_id))
    with Session(get_engine()) as session:
        session.add(
            Booking(
                warehouse_id=uuid.UUID(godown["id"]),
                owner_id=owner_id,
                renter_id=renter_id,
                stock_type_id=uuid.UUID(godown["stock_type_ids"][0]),
                quantity=1,
                start_date=datetime.date(2030, 1, 1),
                end_date=datetime.date(2030, 2, 1),
                rate_per_unit_month=Decimal("10"),
                status="CONFIRMED",
            )
        )
        session.commit()
    return {"emails": emails, "godown": godown}


def test_preview_lists_what_would_go_and_deletes_nothing(client, seeded):
    response = client.post(
        f"{BASE}/preview", json={"emails": [seeded["emails"]["owner"]]}, headers=ADMIN_HEADERS
    )

    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] is False
    assert body["warehouses"] == 1
    assert body["bookings"] == 1
    assert body["photos"] == 1
    assert body["owner_settings"] == 1
    assert body["invitees_released"] == 1
    assert user_exists(seeded["emails"]["owner"])


def test_delete_needs_the_word_delete(client, seeded):
    response = client.post(
        f"{BASE}/delete",
        json={"emails": [seeded["emails"]["owner"]], "confirm": "yes"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 422
    assert user_exists(seeded["emails"]["owner"])


def test_delete_removes_the_owner_godowns_bookings_and_photos(client, seeded):
    godown_id = seeded["godown"]["id"]
    photo_key = next(iter(STORED))  # the only photo stored in this test
    DELETED.clear()

    response = client.post(
        f"{BASE}/delete",
        json={"emails": [seeded["emails"]["owner"]], "confirm": "DELETE"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] is True
    assert body["photo_files_left"] == 0
    assert DELETED == [photo_key]
    assert not user_exists(seeded["emails"]["owner"])
    with Session(get_engine()) as session:
        assert session.get(Warehouse, uuid.UUID(godown_id)) is None
        assert session.scalar(select(Booking.id).where(Booking.warehouse_id == godown_id)) is None
        photo_rows = select(WarehousePhoto.id).where(WarehousePhoto.warehouse_id == godown_id)
        assert session.scalar(photo_rows) is None
    invitee = seeded["emails"]["invitee"]
    assert user_exists(invitee)  # kept, but no longer linked to the owner
    with Session(get_engine()) as session:
        assert session.scalar(select(User).where(User.email == invitee)).invited_by_id is None


def test_renter_is_removed_with_their_bookings(client, seeded):
    response = client.post(
        f"{BASE}/delete",
        json={"emails": [seeded["emails"]["renter"]], "confirm": "DELETE"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert not user_exists(seeded["emails"]["renter"])
    assert user_exists(seeded["emails"]["owner"])
    assert client.get("/api/warehouses", headers=headers_for_owner(seeded)).status_code == 200


def headers_for_owner(seeded) -> dict:
    with Session(get_engine()) as session:
        owner = session.scalar(select(User).where(User.email == seeded["emails"]["owner"]))
        return headers_for(owner.id)


def test_delete_one_godown_keeps_its_owner(client, seeded):
    godown_id = seeded["godown"]["id"]

    response = client.post(
        f"{BASE}/delete",
        json={"warehouse_ids": [godown_id], "confirm": "DELETE"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert user_exists(seeded["emails"]["owner"])
    gone = client.get(f"/api/warehouses/{godown_id}", headers=headers_for_owner(seeded))
    assert gone.status_code == 404


def test_unknown_emails_are_reported_not_errors(client):
    response = client.post(
        f"{BASE}/preview", json={"emails": ["nobody@example.test"]}, headers=ADMIN_HEADERS
    )

    assert response.status_code == 200
    assert response.json()["missing_emails"] == ["nobody@example.test"]


def test_delete_with_nothing_found_is_404(client):
    response = client.post(
        f"{BASE}/delete",
        json={"emails": ["nobody@example.test"], "confirm": "DELETE"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 404


def test_admin_cannot_delete_their_own_account(client):
    response = client.post(
        f"{BASE}/delete",
        json={"emails": ["admin@example.test"], "confirm": "DELETE"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 422
    assert "own account" in response.json()["detail"]


@pytest.mark.parametrize("headers", [OWNER_HEADERS, RENTER_HEADERS, {}])
def test_only_admins_can_use_it(client, headers):
    response = client.post(f"{BASE}/preview", json={"emails": ["x@example.test"]}, headers=headers)

    assert response.status_code in (401, 403)


def test_empty_request_is_rejected(client):
    response = client.post(f"{BASE}/preview", json={}, headers=ADMIN_HEADERS)

    assert response.status_code == 422
