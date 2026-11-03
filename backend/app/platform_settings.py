# ---------------------------------------------------------------
# Platform settings (M2): behaviour that can change without code.
#
# Three layers, highest wins:
#   1. OWNER override     - owner_setting table   (one owner only)
#   2. PLATFORM value     - platform_setting table (set by admin)
#   3. DEFAULT            - written below, in code
#
# The list of settings lives here in code (name, type, allowed
# values), so every setting is typed and validated. The database only
# stores values that differ from these defaults.
#
# M8 (bookings) copies the effective values onto each booking, so a
# later change never alters bookings that already exist.
# ---------------------------------------------------------------
import json
import uuid
from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OwnerSetting, PlatformSetting

SettingType = Literal["bool", "int", "choice"]
Source = Literal["owner", "platform", "default"]
SettingValue = bool | int | str


@dataclass(frozen=True)
class SettingDef:
    """Description of one setting."""

    key: str
    label: str
    description: str
    type: SettingType
    default: SettingValue
    choices: tuple[str, ...] = field(default_factory=tuple)  # for "choice"
    min: int | None = None  # for "int"
    max: int | None = None  # for "int"
    owner_can_override: bool = True


# ---------- The settings (add new ones here) ----------

SETTINGS: dict[str, SettingDef] = {
    s.key: s
    for s in [
        SettingDef(
            key="offline_booking_requires_renter_confirmation",
            label="Offline bookings need renter confirmation",
            description="When an owner enters a booking made in person or by phone, "
            "the renter must confirm it via a link before it is final.",
            type="bool",
            default=True,
            # Booking rules are platform-wide: owners can't change them.
            owner_can_override=False,
        ),
        SettingDef(
            key="renter_confirmation_timeout_days",
            label="Days to wait for renter confirmation",
            description="How long a renter has to confirm an offline booking.",
            type="int",
            default=3,
            min=1,
            max=30,
            # Booking rules are platform-wide: owners can't change them.
            owner_can_override=False,
        ),
        SettingDef(
            key="on_timeout_action",
            label="If the renter doesn't confirm in time",
            description="AUTO_CONFIRM: confirm the booking anyway. "
            "FLAG_UNVERIFIED: confirm it but mark it 'not verified by renter'.",
            type="choice",
            default="FLAG_UNVERIFIED",
            choices=("AUTO_CONFIRM", "FLAG_UNVERIFIED"),
            # Booking rules are platform-wide: owners can't change them.
            owner_can_override=False,
        ),
        SettingDef(
            key="allow_stock_in_before_confirmation",
            label="Allow stock IN before renter confirms",
            description="Lets the owner record bags coming in while the "
            "renter's confirmation is still pending.",
            type="bool",
            default=True,
            # Booking rules are platform-wide: owners can't change them.
            owner_can_override=False,
        ),
    ]
}


# ---------- Validation ----------


def validate_value(setting: SettingDef, value: SettingValue) -> SettingValue:
    """Check a value against the setting's rules; return it or raise ValueError."""
    if setting.type == "bool":
        if not isinstance(value, bool):
            raise ValueError("must be true or false")
        return value

    if setting.type == "int":
        # bool is a kind of int in Python, so reject it explicitly.
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("must be a whole number")
        if setting.min is not None and value < setting.min:
            raise ValueError(f"must be at least {setting.min}")
        if setting.max is not None and value > setting.max:
            raise ValueError(f"must be at most {setting.max}")
        return value

    # "choice"
    if not isinstance(value, str) or value not in setting.choices:
        raise ValueError(f"must be one of: {', '.join(setting.choices)}")
    return value


# Values are stored as JSON text ("true", "3", "\"AUTO_CONFIRM\"") so one
# text column can hold any type (JSONB support in DSQL is unverified).
def to_stored(value: SettingValue) -> str:
    return json.dumps(value)


def from_stored(setting: SettingDef, stored: str) -> SettingValue:
    """Read a stored value; fall back to the default if it is no longer valid."""
    try:
        return validate_value(setting, json.loads(stored))
    except (ValueError, json.JSONDecodeError):
        return setting.default


# ---------- Effective values ----------


@dataclass(frozen=True)
class Effective:
    value: SettingValue
    source: Source


def effective_settings(session: Session, owner_id: uuid.UUID | None = None) -> dict[str, Effective]:
    """
    The value that applies for each setting, and where it came from.
    owner_id=None gives the platform-wide values (no owner override).
    """
    platform = {row.key: row.value for row in session.scalars(select(PlatformSetting))}
    owner: dict[str, str] = {}
    if owner_id is not None:
        rows = session.scalars(select(OwnerSetting).where(OwnerSetting.owner_id == owner_id))
        owner = {row.key: row.value for row in rows}

    result: dict[str, Effective] = {}
    for key, setting in SETTINGS.items():
        if setting.owner_can_override and key in owner:
            result[key] = Effective(from_stored(setting, owner[key]), "owner")
        elif key in platform:
            result[key] = Effective(from_stored(setting, platform[key]), "platform")
        else:
            result[key] = Effective(setting.default, "default")
    return result
