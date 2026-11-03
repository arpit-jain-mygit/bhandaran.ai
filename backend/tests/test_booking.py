# ---------------------------------------------------------------
# Tests for offline bookings (M8): renter lookup, space, the
# confirmation rules, time rules and concurrent-write retries.
# ---------------------------------------------------------------
import secrets
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api import booking as booking_api
from app.db import get_engine
from app.models import Booking, StockType, User
from tests.conftest import ADMIN_HEADERS, OWNER_HEADERS, RENTER_HEADERS, TEST_USERS, make_user
from tests.test_search import approved, new_pincode
from tests.test_warehouse import create, fake_s3  # noqa: F401 (fixture)

CONFIRM_RULE = "offline_booking_requires_renter_confirmation"
TIMEOUT_RULE = "on_timeout_action"


def today():
    return datetime.now(UTC).date()


def new_email() -> str:
    return f"r{secrets.token_hex(4)}@example.test"


@pytest.fixture
def rules(client):
    """Set booking rules for one test, then put them back."""
    changed = []

    def set_rule(key, value):
        client.put(f"/api/settings/{key}", json={"value": value}, headers=ADMIN_HEADERS)
        changed.append(key)

    yield set_rule
    for key in changed:
        client.delete(f"/api/settings/{key}", headers=ADMIN_HEADERS)


def godown(client, capacity=500) -> dict:
    return approved(client, pincode=new_pincode(), capacity=capacity)


def book(client, listing, headers=OWNER_HEADERS, **changes):
    body = {
        "warehouse_id": listing["id"],
        "renter_email": new_email(),
        "renter_name": "Sunita",
        "stock_type_id": listing["stock_type_ids"][0],
        "quantity": 100,
        "start_date": str(today()),
        "end_date": str(today() + timedelta(days=60)),
        "rate_per_unit_month": "10",
    }
    body.update(changes)
    return client.post("/api/bookings", json=body, headers=headers)


def free_space(client, listing) -> int:
    return client.get(f"/api/search/warehouses/{listing['id']}").json()["available_capacity"]


# ---------- recording a booking ----------


def test_owner_books_for_a_new_renter(client):
    email = new_email()
    response = book(client, godown(client), renter_email=email)

    assert response.status_code == 201
    booking = response.json()
    assert booking["status"] == "PENDING_RENTER_CONFIRMATION"
    assert booking["channel"] == "OFFLINE"
    assert booking["confirmation_due_at"]
    with Session(get_engine()) as session:
        renter = session.scalar(select(User).where(User.email == email))
        assert (renter.status, renter.role_names) == ("UNCLAIMED", ["RENTER"])


def test_booking_reduces_free_space(client):
    listing = godown(client, capacity=500)
    book(client, listing, quantity=200)
    assert free_space(client, listing) == 300


def test_overbooking_is_refused(client):
    listing = godown(client, capacity=500)
    book(client, listing, quantity=400)

    response = book(client, listing, quantity=200)
    assert response.status_code == 409
    assert "Only 100 free" in response.json()["detail"]


def test_bookings_on_different_dates_dont_clash(client):
    listing = godown(client, capacity=500)
    later = today() + timedelta(days=100)
    assert book(client, listing, quantity=500).status_code == 201
    response = book(
        client,
        listing,
        quantity=500,
        start_date=str(later),
        end_date=str(later + timedelta(days=30)),
    )
    assert response.status_code == 201


def test_existing_owner_also_becomes_a_renter(client):
    email = new_email()
    with Session(get_engine()) as session:
        make_user(session, email, "Other Owner", "OWNER")
        session.commit()

    assert book(client, godown(client), renter_email=email, renter_name="").status_code == 201
    with Session(get_engine()) as session:
        roles = session.scalar(select(User).where(User.email == email)).role_names
    assert roles == ["OWNER", "RENTER"]


# ---------- what is refused ----------


def test_new_renter_needs_a_name(client):
    assert book(client, godown(client), renter_name="").status_code == 422


def test_owner_cannot_book_for_themself(client):
    owner_email = TEST_USERS["owner"].email
    assert book(client, godown(client), renter_email=owner_email).status_code == 422


def test_only_approved_godowns_take_bookings(client):
    draft = create(client).json()
    assert book(client, draft).status_code == 422


def test_stock_type_must_be_accepted(client):
    listing = godown(client)
    with Session(get_engine()) as session:
        others = session.scalars(
            select(StockType.id).where(StockType.id.not_in(listing["stock_type_ids"]))
        ).all()
    assert book(client, listing, stock_type_id=str(others[0])).status_code == 422


def test_dates_must_make_sense(client):
    listing = godown(client)
    backwards = book(
        client, listing, start_date=str(today()), end_date=str(today() - timedelta(days=1))
    )
    assert backwards.status_code == 422


def test_renters_cannot_record_bookings(client):
    assert book(client, godown(client), headers=RENTER_HEADERS).status_code == 403


# ---------- confirmation rules ----------


def test_without_confirmation_a_booking_starting_today_is_active(client, rules):
    rules(CONFIRM_RULE, False)
    booking = book(client, godown(client)).json()
    assert booking["status"] == "ACTIVE"
    assert booking["confirmation_due_at"] is None


def test_without_confirmation_a_future_booking_is_confirmed(client, rules):
    rules(CONFIRM_RULE, False)
    start = today() + timedelta(days=10)
    booking = book(
        client, godown(client), start_date=str(start), end_date=str(start + timedelta(days=30))
    ).json()
    assert booking["status"] == "CONFIRMED"


def test_renter_confirms_their_booking(client):
    renter_email = TEST_USERS["renter"].email
    booking = book(client, godown(client), renter_email=renter_email).json()

    mine = client.get("/api/bookings/mine", headers=RENTER_HEADERS).json()
    assert booking["id"] in [b["id"] for b in mine]

    confirmed = client.post(f"/api/bookings/{booking['id']}/confirm", headers=RENTER_HEADERS)
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "ACTIVE"  # starts today
    assert confirmed.json()["unverified"] is False

    again = client.post(f"/api/bookings/{booking['id']}/confirm", headers=RENTER_HEADERS)
    assert again.status_code == 409


def test_other_people_cannot_confirm(client):
    booking = book(client, godown(client)).json()  # for a different, new renter
    response = client.post(f"/api/bookings/{booking['id']}/confirm", headers=RENTER_HEADERS)
    assert response.status_code == 404


def expire(booking_id: str) -> None:
    with Session(get_engine()) as session:
        session.execute(
            update(Booking)
            .where(Booking.id == booking_id)
            .values(confirmation_due_at=datetime.now(UTC) - timedelta(minutes=1))
        )
        session.commit()


def test_timeout_confirms_and_flags_it_unverified(client):
    booking = book(client, godown(client)).json()
    expire(booking["id"])

    rows = client.get("/api/bookings/owner", headers=OWNER_HEADERS).json()
    row = next(b for b in rows if b["id"] == booking["id"])
    assert (row["status"], row["unverified"]) == ("ACTIVE", True)


def test_timeout_can_auto_confirm_without_a_flag(client, rules):
    rules(TIMEOUT_RULE, "AUTO_CONFIRM")
    booking = book(client, godown(client)).json()
    expire(booking["id"])

    rows = client.get("/api/bookings/owner", headers=OWNER_HEADERS).json()
    row = next(b for b in rows if b["id"] == booking["id"])
    assert (row["status"], row["unverified"]) == ("ACTIVE", False)


# ---------- concurrent writes ----------


class RetryableError:
    sqlstate = "OC000"  # DSQL optimistic-concurrency conflict


def test_booking_is_retried_after_a_write_conflict(client, monkeypatch):
    listing = godown(client)
    real = booking_api.booked_quantity
    calls = []

    def flaky(*args, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise OperationalError("SELECT ...", {}, RetryableError())
        return real(*args, **kwargs)

    monkeypatch.setattr(booking_api, "booked_quantity", flaky)

    assert book(client, listing).status_code == 201
    assert len(calls) == 2


def test_repeated_conflicts_give_a_try_again_message(client, monkeypatch):
    listing = godown(client)

    def always(*args, **kwargs):
        raise OperationalError("SELECT ...", {}, RetryableError())

    monkeypatch.setattr(booking_api, "booked_quantity", always)

    response = book(client, listing)
    assert response.status_code == 409
    assert "try again" in response.json()["detail"]
