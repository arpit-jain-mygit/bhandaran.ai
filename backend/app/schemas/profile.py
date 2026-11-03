# ---------------------------------------------------------------
# JSON shapes for profiles and renter invites (M4).
# ---------------------------------------------------------------
import uuid

from pydantic import BaseModel

from app.schemas.auth import Name


class ProfileIn(BaseModel):
    name: Name
    city_id: uuid.UUID | None = None
    # Empty or missing means "no GST number"; api/profile.py checks the format.
    gst_number: str | None = None


class ProfileOut(BaseModel):
    id: uuid.UUID
    email: str | None
    name: str | None
    status: str
    city_id: uuid.UUID | None
    city_name: str | None
    gst_number: str | None
    roles: list[str]


class InviteRenter(BaseModel):
    email: str
    name: Name
