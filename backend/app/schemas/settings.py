# ---------------------------------------------------------------
# JSON shapes for the platform-settings API (M2).
# ---------------------------------------------------------------
from typing import Literal

from pydantic import BaseModel

# bool first: in JSON, true/false must stay booleans (not become 1/0).
Value = bool | int | str


class SettingValueIn(BaseModel):
    """Body of PUT: the new value, e.g. {"value": false} or {"value": 5}."""

    value: Value


class SettingOut(BaseModel):
    """One setting with its rules, default and platform-wide value."""

    key: str
    label: str
    description: str
    type: Literal["bool", "int", "choice"]
    choices: list[str]
    min: int | None
    max: int | None
    owner_can_override: bool
    default: Value
    value: Value  # what applies platform-wide
    source: Literal["platform", "default"]  # where `value` comes from


class EffectiveSettingOut(BaseModel):
    """The value that applies for one owner, and where it comes from."""

    key: str
    label: str
    value: Value
    source: Literal["owner", "platform", "default"]
