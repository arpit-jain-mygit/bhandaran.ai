# ---------------------------------------------------------------
# JSON shapes for bookings (M8).
# ---------------------------------------------------------------
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Price = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
OptionalName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]


class OfflineBookingIn(BaseModel):
    """What an owner enters for a deal made in person or by phone."""

    warehouse_id: uuid.UUID
    renter_email: str
    # Needed only when the renter has no account yet.
    renter_name: OptionalName = ""
    stock_type_id: uuid.UUID
    quantity: int = Field(gt=0, le=10_000_000)
    start_date: date
    end_date: date
    rate_per_unit_month: Price


class BookingOut(BaseModel):
    id: uuid.UUID
    warehouse_id: uuid.UUID
    warehouse_name: str
    city_name: str | None
    owner_name: str | None
    renter_name: str | None
    renter_email: str | None
    stock_type_name: str | None
    unit_name: str | None
    quantity: int
    start_date: date
    end_date: date
    rate_per_unit_month: Decimal
    channel: str
    status: str
    unverified: bool
    confirmation_due_at: datetime | None
    confirmed_at: datetime | None
    created_at: datetime
