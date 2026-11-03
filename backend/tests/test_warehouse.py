# ---------------------------------------------------------------
# Tests for warehouse listings (M5): drafts, photos, submitting.
# S3 is replaced with a fake, so no test touches the real bucket.
# ---------------------------------------------------------------
import secrets

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import photos
from app.db import get_engine
from app.models import City, StockType, StorageType, Unit, WarehousePhoto
from tests.conftest import OWNER_HEADERS, RENTER_HEADERS, make_user

STORED = {}  # S3 key -> {"size", "content_type"}; what the fake bucket holds
DELETED = []


@pytest.fixture(autouse=True)
def fake_s3(monkeypatch):
    STORED.clear()
    DELETED.clear()
    monkeypatch.setattr(photos, "upload_link", lambda key, ctype: f"https://s3.example/{key}")
    monkeypatch.setattr(photos, "view_link", lambda key: f"https://s3.example/view/{key}")
    monkeypatch.setattr(photos, "stored_object", lambda key: STORED.get(key))

    def remove(key):
        DELETED.append(key)
        STORED.pop(key, None)

    monkeypatch.setattr(photos, "delete_object", remove)


def first_id(model) -> str:
    with Session(get_engine()) as session:
        return str(session.scalar(select(model.id).limit(1)))


def listing_body(**changes) -> dict:
    body = {
        "name": "Vidisha godown 1",
        "address": "Near the mandi, Sironj Road",
        "city_id": first_id(City),
        "pincode": "464001",
        "capacity": 500,
        "unit_id": first_id(Unit),
        "storage_type_id": first_id(StorageType),
        "stock_type_ids": [first_id(StockType)],
        "price_per_unit_month": "12.50",
    }
    body.update(changes)
    return body


def create(client, headers=OWNER_HEADERS, **changes):
    return client.post("/api/warehouses", json=listing_body(**changes), headers=headers)


def add_photo(client, warehouse_id, content_type="image/jpeg", size=2_000_000):
    """Full photo flow: ask for a link, 'upload' the file, confirm it."""
    asked = client.post(
        f"/api/warehouses/{warehouse_id}/photos",
        json={"content_type": content_type},
        headers=OWNER_HEADERS,
    ).json()
    extension = photos.ALLOWED_TYPES[content_type]
    key = f"warehouses/{warehouse_id}/{asked['photo_id']}.{extension}"
    STORED[key] = {"size": size, "content_type": content_type}
    return client.post(
        f"/api/warehouses/{warehouse_id}/photos/{asked['photo_id']}/confirm", headers=OWNER_HEADERS
    )


# ---------- drafts ----------


def test_owner_creates_a_draft_listing(client):
    response = create(client)

    assert response.status_code == 201
    listing = response.json()
    assert listing["status"] == "DRAFT"
    assert listing["city_name"] and listing["unit_name"] and listing["storage_type_name"]
    assert "Add at least one photo" in listing["missing"]


def test_owner_sees_only_their_own_listings(client):
    created = create(client).json()

    mine = client.get("/api/warehouses", headers=OWNER_HEADERS).json()
    assert created["id"] in [row["id"] for row in mine]

    other = make_other_owner()
    assert client.get(f"/api/warehouses/{created['id']}", headers=other).status_code == 404


def make_other_owner() -> dict:
    email = f"o{secrets.token_hex(4)}@example.test"
    with Session(get_engine(), expire_on_commit=False) as session:
        user = make_user(session, email, "Other Owner", "OWNER")
        session.commit()
        from app.auth import create_session_token

        return {"Authorization": f"Bearer {create_session_token(user.id)}"}


def test_renters_cannot_create_listings(client):
    assert create(client, headers=RENTER_HEADERS).status_code == 403


def test_bad_pincode_and_unknown_city_are_rejected(client):
    assert create(client, pincode="46400").status_code == 422
    assert create(client, city_id="00000000-0000-0000-0000-000000000000").status_code == 422


def test_capacity_must_be_positive(client):
    assert create(client, capacity=0).status_code == 422


def test_owner_edits_a_draft(client):
    listing = create(client).json()
    response = client.put(
        f"/api/warehouses/{listing['id']}",
        json=listing_body(name="Renamed", price_per_unit_month="15"),
        headers=OWNER_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"


# ---------- photos ----------


def test_photo_is_confirmed_after_upload(client):
    listing = create(client).json()
    response = add_photo(client, listing["id"])

    assert response.status_code == 200
    photo = response.json()["photos"][0]
    assert photo["status"] == "UPLOADED"
    assert photo["view_url"].startswith("https://s3.example/view/")


def test_unconfirmed_upload_is_not_a_photo_yet(client):
    listing = create(client).json()
    asked = client.post(
        f"/api/warehouses/{listing['id']}/photos",
        json={"content_type": "image/png"},
        headers=OWNER_HEADERS,
    ).json()
    response = client.post(
        f"/api/warehouses/{listing['id']}/photos/{asked['photo_id']}/confirm", headers=OWNER_HEADERS
    )
    assert response.status_code == 409


def test_too_large_photo_is_removed(client):
    listing = create(client).json()
    response = add_photo(client, listing["id"], size=6 * 1024 * 1024)

    assert response.status_code == 422
    assert len(DELETED) == 1
    with Session(get_engine()) as session:
        assert (
            session.scalar(
                select(WarehousePhoto.id).where(WarehousePhoto.warehouse_id == listing["id"])
            )
            is None
        )


def test_only_image_types_are_accepted(client):
    listing = create(client).json()
    response = client.post(
        f"/api/warehouses/{listing['id']}/photos",
        json={"content_type": "application/pdf"},
        headers=OWNER_HEADERS,
    )
    assert response.status_code == 422


def test_photo_can_be_deleted_from_a_draft(client):
    listing = create(client).json()
    added = add_photo(client, listing["id"]).json()
    photo_id = added["photos"][0]["id"]

    response = client.delete(
        f"/api/warehouses/{listing['id']}/photos/{photo_id}", headers=OWNER_HEADERS
    )

    assert response.status_code == 200
    assert response.json()["photos"] == []
    assert len(DELETED) == 1


# ---------- submitting ----------


def test_incomplete_listing_cannot_be_submitted(client):
    listing = create(client, stock_type_ids=[]).json()
    response = client.post(f"/api/warehouses/{listing['id']}/submit", headers=OWNER_HEADERS)

    assert response.status_code == 422
    assert "stock type" in response.json()["detail"]
    assert "photo" in response.json()["detail"]


def test_complete_listing_goes_to_review_and_is_then_locked(client):
    listing = create(client).json()
    add_photo(client, listing["id"])

    submitted = client.post(f"/api/warehouses/{listing['id']}/submit", headers=OWNER_HEADERS)
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "PENDING_REVIEW"

    edit = client.put(
        f"/api/warehouses/{listing['id']}",
        json=listing_body(name="Too late"),
        headers=OWNER_HEADERS,
    )
    assert edit.status_code == 409
    assert (
        client.post(
            f"/api/warehouses/{listing['id']}/photos",
            json={"content_type": "image/png"},
            headers=OWNER_HEADERS,
        ).status_code
        == 409
    )
