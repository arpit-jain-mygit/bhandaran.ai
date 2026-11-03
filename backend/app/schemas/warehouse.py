# ---------------------------------------------------------------
# JSON shapes for warehouse listings (M5).
# ---------------------------------------------------------------
import uuid
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.schemas.auth import Name

Pincode = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{6}$")]
Address = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
Price = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


class WarehouseIn(BaseModel):
    name: Name
    address: Address
    city_id: uuid.UUID
    pincode: Pincode
    capacity: int = Field(gt=0, le=10_000_000)
    unit_id: uuid.UUID
    storage_type_id: uuid.UUID
    stock_type_ids: list[uuid.UUID] = Field(default_factory=list)
    price_per_unit_month: Price


class PhotoRequest(BaseModel):
    content_type: Literal["image/jpeg", "image/png", "image/webp"]


class PhotoUploadOut(BaseModel):
    photo_id: uuid.UUID
    upload_url: str  # PUT the file here with the same Content-Type
    content_type: str


class PhotoOut(BaseModel):
    id: uuid.UUID
    status: str
    view_url: str | None  # None until the upload is confirmed


class WarehouseOut(BaseModel):
    id: uuid.UUID
    name: str
    address: str
    city_id: uuid.UUID
    city_name: str | None
    pincode: str
    capacity: int
    unit_id: uuid.UUID
    unit_name: str | None
    storage_type_id: uuid.UUID
    storage_type_name: str | None
    stock_type_ids: list[uuid.UUID]
    price_per_unit_month: Decimal
    status: str
    photos: list[PhotoOut]
    # What's still missing before the owner can submit (empty when ready).
    missing: list[str]
    # Set when an admin sent the listing back, with the reason (M6).
    review_note: str | None = None
    # Filled in for admins only (M6 review screen).
    owner_name: str | None = None
    owner_email: str | None = None


class RejectIn(BaseModel):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
