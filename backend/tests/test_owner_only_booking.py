# ---------------------------------------------------------------
# Tests for owner-only booking records: no renter email, so no
# account, no emails and no confirmation. Just a name and phone.
# ---------------------------------------------------------------

from tests.conftest import OWNER_HEADERS, RENTER_HEADERS
from tests.test_booking import book, godown
from tests.test_warehouse import fake_s3  # noqa: F401 (fixture)


def record(client, listing, **changes):
    return book(client, listing, renter_email="", **changes)


def test_owner_only_record_is_confirmed_and_has_no_renter_account(client, monkeypatch):
    sent = []
    monkeypatch.setattr("app.api.booking.send_email", lambda *a, **k: sent.append(a))
    listing = godown(client)

    response = record(client, listing, renter_name="Walk-in Ravi", renter_phone="98765 43210")

    assert response.status_code == 201
    body = response.json()
    # Confirmed at once; ACTIVE if the start date is already today.
    assert body["status"] in ("CONFIRMED", "ACTIVE")
    assert body["confirmed_at"] is not None
    assert body["renter_name"] == "Walk-in Ravi"
    assert body["renter_email"] is None
    assert body["renter_phone"] == "9876543210"
    assert sent == []  # nobody was emailed


def test_owner_only_record_appears_for_the_owner_not_a_renter(client):
    listing = godown(client)
    record(client, listing, renter_name="Only Owner Sees")

    owner_rows = client.get("/api/bookings/owner", headers=OWNER_HEADERS).json()
    assert any(row["renter_name"] == "Only Owner Sees" for row in owner_rows)
    renter_rows = client.get("/api/bookings/mine", headers=RENTER_HEADERS).json()
    assert not any(row["renter_name"] == "Only Owner Sees" for row in renter_rows)


def test_owner_only_record_needs_a_name(client):
    listing = godown(client)

    response = record(client, listing, renter_name="")

    assert response.status_code == 422
    assert "renter's name" in response.json()["detail"]


def test_owner_only_record_still_respects_space(client):
    listing = godown(client, capacity=100)
    record(client, listing, renter_name="First", quantity=80)

    response = record(client, listing, renter_name="Second", quantity=80)

    assert response.status_code == 409
    assert "free for those dates" in response.json()["detail"]


def test_bad_phone_is_rejected(client):
    listing = godown(client)

    response = record(client, listing, renter_name="Bad Phone", renter_phone="12345")

    assert response.status_code == 422
    assert "10-digit mobile" in response.json()["detail"]


def test_phone_is_optional(client):
    listing = godown(client)

    body = record(client, listing, renter_name="No Phone").json()

    assert body["renter_phone"] is None


def test_email_booking_still_creates_a_renter_and_needs_confirmation(client):
    listing = godown(client)

    body = book(client, listing).json()  # book() fills in an email

    assert body["status"] == "PENDING_RENTER_CONFIRMATION"
    assert body["renter_email"] is not None
    assert body["renter_phone"] is None
