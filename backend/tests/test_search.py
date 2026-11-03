# ---------------------------------------------------------------
# Tests for search (M7). Each test uses its own random pincode so
# listings made by other tests don't show up in its results.
# ---------------------------------------------------------------
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import City, District, StockType, StorageType
from tests.conftest import ADMIN_HEADERS, OWNER_HEADERS
from tests.test_warehouse import add_photo, create, fake_s3  # noqa: F401 (fixture)

SEARCH = "/api/search/warehouses"


def new_pincode() -> str:
    return str(100000 + secrets.randbelow(900000))


def ids(model, count: int) -> list[str]:
    with Session(get_engine()) as session:
        return [str(i) for i in session.scalars(select(model.id).order_by(model.name).limit(count))]


def approved(client, **changes) -> dict:
    """A listing taken all the way to APPROVED."""
    listing = create(client, **changes).json()
    add_photo(client, listing["id"])
    client.post(f"/api/warehouses/{listing['id']}/submit", headers=OWNER_HEADERS)
    client.post(f"/api/admin/warehouses/{listing['id']}/approve", headers=ADMIN_HEADERS)
    return listing


def found(client, **params) -> list[str]:
    response = client.get(SEARCH, params=params)
    assert response.status_code == 200
    return [row["id"] for row in response.json()]


def test_only_approved_listings_are_found(client):
    pin = new_pincode()
    live = approved(client, pincode=pin)
    draft = create(client, pincode=pin).json()
    waiting = create(client, pincode=pin).json()
    add_photo(client, waiting["id"])
    client.post(f"/api/warehouses/{waiting['id']}/submit", headers=OWNER_HEADERS)

    assert found(client, pincode=pin) == [live["id"]]
    assert draft["id"] not in found(client, pincode=pin)


def test_search_needs_no_login_and_hides_the_owner(client):
    pin = new_pincode()
    approved(client, pincode=pin)
    row = client.get(SEARCH, params={"pincode": pin}).json()[0]

    assert "owner_email" not in row and "owner_name" not in row
    assert row["available_capacity"] == 500
    assert row["photo_url"]
    assert row["city_name"] and row["district_name"] and row["state_name"]


def test_search_by_city_district_and_state(client):
    pin = new_pincode()
    listing = approved(client, pincode=pin)
    with Session(get_engine()) as session:
        city = session.get(City, listing["city_id"])
        district = session.get(District, city.district_id)
        place = {
            "city_id": str(city.id),
            "district_id": str(district.id),
            "state_id": str(district.state_id),
        }

    for key, value in place.items():
        assert found(client, pincode=pin, **{key: value}) == [listing["id"]]


def test_filters_by_storage_and_stock_type(client):
    pin = new_pincode()
    dry, cold = ids(StorageType, 2)
    first_stock, second_stock = ids(StockType, 2)
    a = approved(client, pincode=pin, storage_type_id=dry, stock_type_ids=[first_stock])
    b = approved(client, pincode=pin, storage_type_id=cold, stock_type_ids=[second_stock])

    assert found(client, pincode=pin, storage_type_id=dry) == [a["id"]]
    assert found(client, pincode=pin, stock_type_id=second_stock) == [b["id"]]


def test_filters_by_price_and_capacity_cheapest_first(client):
    pin = new_pincode()
    cheap = approved(client, pincode=pin, price_per_unit_month="8", capacity=100)
    dear = approved(client, pincode=pin, price_per_unit_month="20", capacity=900)

    assert found(client, pincode=pin) == [cheap["id"], dear["id"]]
    assert found(client, pincode=pin, max_price="10") == [cheap["id"]]
    assert found(client, pincode=pin, min_capacity=500) == [dear["id"]]


def test_bad_pincode_is_rejected(client):
    assert client.get(SEARCH, params={"pincode": "12"}).status_code == 422


def test_detail_shows_an_approved_godown(client):
    listing = approved(client, pincode=new_pincode())
    response = client.get(f"{SEARCH}/{listing['id']}")

    assert response.status_code == 200
    detail = response.json()
    assert detail["address"] and len(detail["photo_urls"]) == 1
    assert "owner_email" not in detail


def test_detail_hides_listings_that_are_not_approved(client):
    draft = create(client, pincode=new_pincode()).json()
    assert client.get(f"{SEARCH}/{draft['id']}").status_code == 404
