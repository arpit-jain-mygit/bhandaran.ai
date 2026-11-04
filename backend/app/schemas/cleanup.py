# ---------------------------------------------------------------
# JSON shapes for deleting test data (admin only).
# ---------------------------------------------------------------
import uuid
from typing import Literal

from pydantic import BaseModel, Field

MAX_ITEMS = 50


class CleanupIn(BaseModel):
    # Accounts to remove, by login email (e.g. "owner@example.test").
    emails: list[str] = Field(default_factory=list, max_length=MAX_ITEMS)
    # Godowns to remove on their own (their owner's account is kept).
    warehouse_ids: list[uuid.UUID] = Field(default_factory=list, max_length=MAX_ITEMS)


class CleanupDeleteIn(CleanupIn):
    # Must be typed exactly, so nothing is deleted by a stray click.
    confirm: Literal["DELETE"]


class CleanupOut(BaseModel):
    # What was (or would be) removed.
    accounts: list[str]  # masked emails, e.g. "ow***@example.test"
    missing_emails: list[str]
    warehouses: int
    missing_warehouse_ids: list[uuid.UUID]
    bookings: int
    photos: int
    login_codes: int
    owner_settings: int
    suppressed_emails: int
    invitees_released: int  # renters this owner invited; they stay, unlinked
    deleted: bool
    # Photos whose files could not be removed from storage (DB rows are gone).
    photo_files_left: int = 0
