# ---------------------------------------------------------------
# Booking rules (M8): how much space is taken, and the time-based
# status changes.
#
# Space: every booking in BOOKING_STATUSES holds its quantity for its
# dates (a pending booking holds space too, so it can't be double-sold).
#
# Time rules are applied when bookings are read ("settled"), so no
# scheduler is needed:
#   PENDING_RENTER_CONFIRMATION past its due time -> CONFIRMED
#       (with unverified=True when the rule is FLAG_UNVERIFIED)
#   CONFIRMED whose start date has arrived -> ACTIVE
# ---------------------------------------------------------------
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.models import Booking, Warehouse
from app.models.booking import BOOKING_STATUSES
from app.platform_settings import effective_settings

# DSQL / PostgreSQL "try again" codes for concurrent writes.
RETRYABLE_SQLSTATES = {"40001", "OC000", "OC001"}


def is_retryable(error: OperationalError) -> bool:
    return getattr(error.orig, "sqlstate", None) in RETRYABLE_SQLSTATES


def booked_quantity(session: Session, warehouse_id: Any, start: date, end: date) -> int:
    """Space held by bookings that overlap start..end (inclusive)."""
    total = session.scalar(
        select(func.coalesce(func.sum(Booking.quantity), 0)).where(
            Booking.warehouse_id == warehouse_id,
            Booking.status.in_(BOOKING_STATUSES),
            Booking.start_date <= end,
            Booking.end_date >= start,
        )
    )
    return int(total or 0)


def booked_today_sql(today: date) -> ColumnElement:
    """Same as booked_quantity for today, as SQL usable inside a godown query."""
    return (
        select(func.coalesce(func.sum(Booking.quantity), 0))
        .where(
            Booking.warehouse_id == Warehouse.id,
            Booking.status.in_(BOOKING_STATUSES),
            Booking.start_date <= today,
            Booking.end_date >= today,
        )
        .correlate(Warehouse)
        .scalar_subquery()
    )


def free_today(session: Session, warehouse: Warehouse) -> int:
    today = datetime.now(UTC).date()
    return max(warehouse.capacity - booked_quantity(session, warehouse.id, today, today), 0)


def settle(booking: Booking, timeout_action: str, now: datetime) -> bool:
    """Apply the time rules to one booking. Returns True if it changed."""
    changed = False
    if (
        booking.status == "PENDING_RENTER_CONFIRMATION"
        and booking.confirmation_due_at is not None
        and now >= booking.confirmation_due_at
    ):
        booking.status = "CONFIRMED"
        booking.confirmed_at = now
        booking.unverified = timeout_action == "FLAG_UNVERIFIED"
        changed = True
    if booking.status == "CONFIRMED" and booking.start_date <= now.date():
        booking.status = "ACTIVE"
        changed = True
    return changed


def settle_all(session: Session, bookings: list[Booking]) -> None:
    """Settle a list of bookings and save any changes (best effort)."""
    if not bookings:
        return
    action = str(effective_settings(session)["on_timeout_action"].value)
    now = datetime.now(UTC)
    if any([settle(b, action, now) for b in bookings]):
        try:
            session.commit()
        except OperationalError:
            # Someone else settled them at the same time; the next read will.
            session.rollback()
