# ---------------------------------------------------------------
# Tests for admin review of listings (M6): approve, reject, resubmit.
# Reuses the listing helpers (and the fake S3) from test_warehouse.
# ---------------------------------------------------------------
from tests.conftest import ADMIN_HEADERS, OWNER_HEADERS
from tests.test_warehouse import add_photo, create, fake_s3  # noqa: F401 (fixture)

ADMIN = "/api/admin/warehouses"


def submitted_listing(client) -> dict:
    listing = create(client).json()
    add_photo(client, listing["id"])
    return client.post(f"/api/warehouses/{listing['id']}/submit", headers=OWNER_HEADERS).json()


def test_admin_sees_listings_waiting_for_review(client):
    listing = submitted_listing(client)

    rows = client.get(ADMIN, headers=ADMIN_HEADERS).json()
    row = next(r for r in rows if r["id"] == listing["id"])
    assert row["owner_name"] and row["owner_email"]
    assert row["photos"][0]["view_url"]


def test_admin_approves_a_listing(client):
    listing = submitted_listing(client)

    response = client.post(f"{ADMIN}/{listing['id']}/approve", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    approved = client.get(ADMIN, params={"status": "APPROVED"}, headers=ADMIN_HEADERS).json()
    assert listing["id"] in [r["id"] for r in approved]


def test_approved_listing_is_locked_for_the_owner(client):
    listing = submitted_listing(client)
    client.post(f"{ADMIN}/{listing['id']}/approve", headers=ADMIN_HEADERS)

    from tests.test_warehouse import listing_body

    edit = client.put(
        f"/api/warehouses/{listing['id']}", json=listing_body(), headers=OWNER_HEADERS
    )
    assert edit.status_code == 409


def test_rejected_listing_goes_back_to_draft_with_the_reason(client):
    listing = submitted_listing(client)

    response = client.post(
        f"{ADMIN}/{listing['id']}/reject",
        json={"reason": "Photos are too dark"},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    owner_view = client.get(f"/api/warehouses/{listing['id']}", headers=OWNER_HEADERS).json()
    assert (owner_view["status"], owner_view["review_note"]) == ("DRAFT", "Photos are too dark")


def test_resubmitting_clears_the_old_note(client):
    listing = submitted_listing(client)
    client.post(
        f"{ADMIN}/{listing['id']}/reject", json={"reason": "Add the pincode"}, headers=ADMIN_HEADERS
    )

    again = client.post(f"/api/warehouses/{listing['id']}/submit", headers=OWNER_HEADERS).json()

    assert (again["status"], again["review_note"]) == ("PENDING_REVIEW", None)


def test_reject_needs_a_reason(client):
    listing = submitted_listing(client)
    response = client.post(
        f"{ADMIN}/{listing['id']}/reject", json={"reason": " "}, headers=ADMIN_HEADERS
    )
    assert response.status_code == 422


def test_only_listings_waiting_for_review_can_be_decided(client):
    draft = create(client).json()
    assert client.post(f"{ADMIN}/{draft['id']}/approve", headers=ADMIN_HEADERS).status_code == 409


def test_owners_cannot_review(client):
    listing = submitted_listing(client)
    assert client.get(ADMIN, headers=OWNER_HEADERS).status_code == 403
    assert client.post(f"{ADMIN}/{listing['id']}/approve", headers=OWNER_HEADERS).status_code == 403
