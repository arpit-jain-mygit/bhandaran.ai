# ---------------------------------------------------------------
# Tests for platform settings (M2): default -> platform -> owner.
# Each test resets what it changes, so tests don't affect each other.
# ---------------------------------------------------------------
import dataclasses
import uuid

import pytest

from app.platform_settings import SETTINGS
from tests.conftest import ADMIN_HEADERS, OWNER_HEADERS, RENTER_HEADERS, TEST_USERS

TIMEOUT = "renter_confirmation_timeout_days"
CONFIRM = "offline_booking_requires_renter_confirmation"
ON_TIMEOUT = "on_timeout_action"


def by_key(items: list[dict]) -> dict[str, dict]:
    return {item["key"]: item for item in items}


@pytest.fixture
def reset_platform(client):
    """Put platform values back to their defaults after a test."""
    yield
    for key in (TIMEOUT, CONFIRM, ON_TIMEOUT):
        client.delete(f"/api/settings/{key}", headers=ADMIN_HEADERS)


@pytest.fixture
def overridable(monkeypatch):
    """Booking rules are not owner-changeable; switch the flag on for override tests."""
    for key, setting in SETTINGS.items():
        monkeypatch.setitem(SETTINGS, key, dataclasses.replace(setting, owner_can_override=True))


# ---------- reading ----------


def test_lists_all_settings_with_defaults(client, reset_platform):
    settings = by_key(client.get("/api/settings").json())

    assert set(settings) == {
        CONFIRM,
        TIMEOUT,
        ON_TIMEOUT,
        "allow_stock_in_before_confirmation",
    }
    assert settings[TIMEOUT]["value"] == 3
    assert settings[TIMEOUT]["source"] == "default"
    assert settings[ON_TIMEOUT]["choices"] == ["AUTO_CONFIRM", "FLAG_UNVERIFIED"]


# ---------- platform values ----------


def test_admin_sets_and_resets_a_platform_value(client, reset_platform):
    changed = by_key(
        client.put(f"/api/settings/{TIMEOUT}", json={"value": 7}, headers=ADMIN_HEADERS).json()
    )
    assert (changed[TIMEOUT]["value"], changed[TIMEOUT]["source"]) == (7, "platform")

    reset = by_key(client.delete(f"/api/settings/{TIMEOUT}", headers=ADMIN_HEADERS).json())
    assert (reset[TIMEOUT]["value"], reset[TIMEOUT]["source"]) == (3, "default")


def test_changing_a_platform_value_needs_login(client):
    assert client.put(f"/api/settings/{TIMEOUT}", json={"value": 7}).status_code == 401


def test_owners_cannot_change_platform_values(client):
    response = client.put(f"/api/settings/{TIMEOUT}", json={"value": 7}, headers=OWNER_HEADERS)
    assert response.status_code == 403


@pytest.mark.parametrize(
    ("key", "value"),
    [
        (TIMEOUT, 0),  # below min 1
        (TIMEOUT, 31),  # above max 30
        (TIMEOUT, True),  # a boolean is not a number of days
        (TIMEOUT, "5"),  # text, not a number
        (CONFIRM, 1),  # a number is not true/false
        (ON_TIMEOUT, "LATER"),  # not one of the choices
    ],
)
def test_invalid_values_are_rejected(client, key, value):
    response = client.put(f"/api/settings/{key}", json={"value": value}, headers=ADMIN_HEADERS)
    assert response.status_code == 422


def test_unknown_setting_returns_404(client):
    response = client.put("/api/settings/fly_to_moon", json={"value": True}, headers=ADMIN_HEADERS)
    assert response.status_code == 404


# ---------- owner overrides ----------


def test_owner_override_wins_over_platform_and_default(client, reset_platform, overridable):
    owner = uuid.uuid4()
    client.put(f"/api/settings/{TIMEOUT}", json={"value": 5}, headers=ADMIN_HEADERS)

    # Owner changes one setting...
    response = client.put(
        f"/api/settings/owners/{owner}/{CONFIRM}", json={"value": False}, headers=ADMIN_HEADERS
    )
    effective = by_key(response.json())

    # ...that one comes from the owner, the others fall through.
    assert (effective[CONFIRM]["value"], effective[CONFIRM]["source"]) == (False, "owner")
    assert (effective[TIMEOUT]["value"], effective[TIMEOUT]["source"]) == (5, "platform")
    assert (effective[ON_TIMEOUT]["value"], effective[ON_TIMEOUT]["source"]) == (
        "FLAG_UNVERIFIED",
        "default",
    )


def test_one_owners_override_does_not_affect_another(client, overridable):
    first, second = uuid.uuid4(), uuid.uuid4()
    client.put(f"/api/settings/owners/{first}/{TIMEOUT}", json={"value": 10}, headers=ADMIN_HEADERS)

    others = by_key(client.get(f"/api/settings/owners/{second}", headers=ADMIN_HEADERS).json())
    assert others[TIMEOUT]["source"] == "default"


def test_removing_an_owner_override_falls_back(client, overridable):
    owner = uuid.uuid4()
    url = f"/api/settings/owners/{owner}/{ON_TIMEOUT}"
    client.put(url, json={"value": "AUTO_CONFIRM"}, headers=ADMIN_HEADERS)

    effective = by_key(client.delete(url, headers=ADMIN_HEADERS).json())

    assert (effective[ON_TIMEOUT]["value"], effective[ON_TIMEOUT]["source"]) == (
        "FLAG_UNVERIFIED",
        "default",
    )


def test_changing_an_owner_value_twice_keeps_one_row(client, overridable):
    owner = uuid.uuid4()
    url = f"/api/settings/owners/{owner}/{TIMEOUT}"
    client.put(url, json={"value": 4}, headers=ADMIN_HEADERS)

    effective = by_key(client.put(url, json={"value": 9}, headers=ADMIN_HEADERS).json())

    assert effective[TIMEOUT]["value"] == 9


def test_owners_cannot_change_booking_rules(client):
    # Booking rules are set for everyone by admins, so owners are refused.
    url = f"/api/settings/me/{TIMEOUT}"
    assert client.put(url, json={"value": 12}, headers=OWNER_HEADERS).status_code == 403

    owner_id = TEST_USERS["owner"].id
    admin_url = f"/api/settings/owners/{owner_id}/{TIMEOUT}"
    assert client.put(admin_url, json={"value": 12}, headers=ADMIN_HEADERS).status_code == 403


def test_owners_see_booking_rules_from_the_platform(client, reset_platform):
    client.put(f"/api/settings/{TIMEOUT}", json={"value": 5}, headers=ADMIN_HEADERS)

    mine = by_key(client.get("/api/settings/me", headers=OWNER_HEADERS).json())
    assert (mine[TIMEOUT]["value"], mine[TIMEOUT]["source"]) == (5, "platform")


# ---------- the logged-in owner's own values ----------


def test_owner_sets_and_removes_their_own_value(client, overridable):
    url = f"/api/settings/me/{TIMEOUT}"

    mine = by_key(client.put(url, json={"value": 12}, headers=OWNER_HEADERS).json())
    assert (mine[TIMEOUT]["value"], mine[TIMEOUT]["source"]) == (12, "owner")

    # The admin sees the same value for this owner.
    owner_id = TEST_USERS["owner"].id
    seen = by_key(client.get(f"/api/settings/owners/{owner_id}", headers=ADMIN_HEADERS).json())
    assert seen[TIMEOUT]["value"] == 12

    back = by_key(client.delete(url, headers=OWNER_HEADERS).json())
    assert back[TIMEOUT]["source"] == "default"


def test_renters_and_visitors_have_no_owner_settings(client):
    assert client.get("/api/settings/me", headers=RENTER_HEADERS).status_code == 403
    assert client.get("/api/settings/me").status_code == 401


def test_only_admins_see_other_owners_settings(client):
    owner_id = TEST_USERS["owner"].id
    response = client.get(f"/api/settings/owners/{owner_id}", headers=OWNER_HEADERS)
    assert response.status_code == 403
