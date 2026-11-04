# ---------------------------------------------------------------
# Bookings (M8): space a renter takes in a godown for some dates.
#
# Status:
#   PENDING_RENTER_CONFIRMATION  owner recorded it; the renter must confirm
#   CONFIRMED                    agreed (by the renter, or by the timeout rule)
#   ACTIVE                       confirmed and the start date has arrived
# "unverified" is set when the timeout rule confirmed it without the renter.
# ---------------------------------------------------------------
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UuidPkMixin

BOOKING_STATUSES = ("PENDING_RENTER_CONFIRMATION", "CONFIRMED", "ACTIVE")
BOOKING_CHANNELS = ("OFFLINE", "ONLINE")


class Booking(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "booking"
    __table_args__ = (
        CheckConstraint(f"status IN {BOOKING_STATUSES}", name="ck_booking_status"),
        CheckConstraint(f"channel IN {BOOKING_CHANNELS}", name="ck_booking_channel"),
        CheckConstraint("quantity > 0", name="ck_booking_quantity_positive"),
        CheckConstraint("end_date >= start_date", name="ck_booking_dates"),
        CheckConstraint("rate_per_unit_month >= 0", name="ck_booking_rate_not_negative"),
        Index("ix_booking_warehouse_dates", "warehouse_id", "start_date"),
        Index("ix_booking_renter_created", "renter_id", "created_at"),
        Index("ix_booking_owner_created", "owner_id", "created_at"),
    )

    warehouse_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    # Empty for an owner-only record (no renter account): see renter_name.
    renter_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    renter_name: Mapped[str | None] = mapped_column(String(100))
    renter_phone: Mapped[str | None] = mapped_column(String(16))
    stock_type_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    # In the godown's unit (e.g. bags).
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    rate_per_unit_month: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    channel: Mapped[str] = mapped_column(String(10), nullable=False, server_default="OFFLINE")
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    unverified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    confirmation_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
