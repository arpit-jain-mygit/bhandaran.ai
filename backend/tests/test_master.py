# ---------------------------------------------------------------
# Tests for the master-data API (M1), against the real test DB.
# Each test uses unique codes/names so tests don't clash.
# ---------------------------------------------------------------
import uuid

import pytest

from tests.conftest import ADMIN_HEADERS


def unique_code(prefix: str = "T") -> str:
    """Random code like T_1A2B3C4D (fits the 20-character limit)."""
    return f"{prefix}_{uuid.uuid4().hex[:8].upper()}"


# ---------- reading ----------


@pytest.mark.parametrize(
    ("kind", "expected_code"),
    [("stock-types", "WHEAT"), ("storage-types", "COLD"), ("units", "BAG"), ("states", "MP")],
)
def test_seeded_lists_are_readable_without_admin_key(client, kind, expected_code):
    response = client.get(f"/api/master/{kind}")

    assert response.status_code == 200
    assert expected_code in [item["code"] for item in response.json()]


def test_unknown_list_returns_404(client):
    assert client.get("/api/master/planets").status_code == 404


def state_id(client, code: str) -> str:
    """Id of a seeded state by its code, e.g. "MP"."""
    states = client.get("/api/master/states").json()
    return next(state["id"] for state in states if state["code"] == code)


def district_id(client, state_code: str, name: str) -> str:
    """Id of a district by state code and district name."""
    params = {"state_id": state_id(client, state_code)}
    districts = client.get("/api/master/districts", params=params).json()
    return next(d["id"] for d in districts if d["name"] == name)


def test_cities_can_be_filtered_by_state(client):
    cities = client.get("/api/master/cities", params={"state_id": state_id(client, "MP")}).json()

    names = [city["name"] for city in cities]
    assert "Indore" in names
    assert "Mumbai" not in names  # Mumbai belongs to Maharashtra


def test_vidisha_district_has_sironj(client):
    vidisha = district_id(client, "MP", "Vidisha")

    towns = client.get("/api/master/cities", params={"district_id": vidisha}).json()

    assert "Sironj" in [town["name"] for town in towns]


def test_seeded_cities_were_moved_into_their_districts(client):
    mumbai_city = district_id(client, "MH", "Mumbai City")

    cities = client.get("/api/master/cities", params={"district_id": mumbai_city}).json()

    assert [city["name"] for city in cities] == ["Mumbai"]
    assert cities[0]["state_id"] == state_id(client, "MH")


# ---------- admin key ----------


def test_write_without_admin_key_is_rejected(client):
    response = client.post("/api/master/units", json={"code": unique_code(), "name": "Pallet"})
    assert response.status_code == 401


def test_write_with_wrong_admin_key_is_rejected(client):
    response = client.post(
        "/api/master/units",
        json={"code": unique_code(), "name": "Pallet"},
        headers={"X-Admin-Key": "wrong"},
    )
    assert response.status_code == 401


# ---------- create / update / disable ----------


def test_admin_can_add_an_item_and_code_is_uppercased(client):
    code = unique_code("t")
    response = client.post(
        "/api/master/stock-types",
        json={"code": code, "name": "  Groundnut  ", "sort_order": 5},
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["code"] == code.upper()
    assert body["name"] == "Groundnut"  # spaces trimmed
    assert body["is_active"] is True


def test_duplicate_code_returns_409(client):
    response = client.post(
        "/api/master/stock-types", json={"code": "WHEAT", "name": "Wheat 2"}, headers=ADMIN_HEADERS
    )
    assert response.status_code == 409


def test_invalid_code_returns_422(client):
    response = client.post(
        "/api/master/units", json={"code": "has space", "name": "X"}, headers=ADMIN_HEADERS
    )
    assert response.status_code == 422


def test_disabled_item_is_hidden_from_dropdown_list_but_kept(client):
    created = client.post(
        "/api/master/units", json={"code": unique_code(), "name": "Tonne"}, headers=ADMIN_HEADERS
    ).json()

    response = client.patch(
        f"/api/master/units/{created['id']}", json={"is_active": False}, headers=ADMIN_HEADERS
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    active_ids = [u["id"] for u in client.get("/api/master/units").json()]
    all_ids = [
        u["id"] for u in client.get("/api/master/units", params={"include_inactive": True}).json()
    ]
    assert created["id"] not in active_ids
    assert created["id"] in all_ids


def test_admin_can_rename_an_item(client):
    created = client.post(
        "/api/master/storage-types",
        json={"code": unique_code(), "name": "Warehouse shed"},
        headers=ADMIN_HEADERS,
    ).json()

    response = client.patch(
        f"/api/master/storage-types/{created['id']}",
        json={"name": "Covered shed"},
        headers=ADMIN_HEADERS,
    )

    assert response.json()["name"] == "Covered shed"
    assert response.json()["code"] == created["code"]  # code never changes


# ---------- districts ----------


def test_admin_can_add_district_and_duplicates_are_case_insensitive(client):
    goa = state_id(client, "GA")
    name = f"District {uuid.uuid4().hex[:6]}"

    first = client.post(
        "/api/master/districts", json={"state_id": goa, "name": name}, headers=ADMIN_HEADERS
    )
    again = client.post(
        "/api/master/districts",
        json={"state_id": goa, "name": name.upper()},
        headers=ADMIN_HEADERS,
    )

    assert first.status_code == 201
    assert first.json()["state_id"] == goa
    assert again.status_code == 409


def test_district_for_unknown_state_returns_404(client):
    response = client.post(
        "/api/master/districts",
        json={"state_id": str(uuid.uuid4()), "name": "Nowhere"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 404


# ---------- cities / towns ----------


def new_district(client, state_code: str = "GA") -> str:
    """Create a fresh district for a test and return its id."""
    response = client.post(
        "/api/master/districts",
        json={"state_id": state_id(client, state_code), "name": f"D {uuid.uuid4().hex[:6]}"},
        headers=ADMIN_HEADERS,
    )
    return response.json()["id"]


def test_admin_can_add_town_and_duplicates_are_case_insensitive(client):
    district = new_district(client)
    name = f"Town {uuid.uuid4().hex[:6]}"

    first = client.post(
        "/api/master/cities", json={"district_id": district, "name": name}, headers=ADMIN_HEADERS
    )
    again = client.post(
        "/api/master/cities",
        json={"district_id": district, "name": name.upper()},
        headers=ADMIN_HEADERS,
    )

    assert first.status_code == 201
    assert first.json()["district_id"] == district
    assert first.json()["state_id"] == state_id(client, "GA")
    assert again.status_code == 409


def test_same_town_name_is_allowed_in_two_districts(client):
    name = f"Rampur {uuid.uuid4().hex[:4]}"

    for district in (new_district(client), new_district(client)):
        response = client.post(
            "/api/master/cities",
            json={"district_id": district, "name": name},
            headers=ADMIN_HEADERS,
        )
        assert response.status_code == 201


def test_city_for_unknown_district_returns_404(client):
    response = client.post(
        "/api/master/cities",
        json={"district_id": str(uuid.uuid4()), "name": "Nowhere"},
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 404
