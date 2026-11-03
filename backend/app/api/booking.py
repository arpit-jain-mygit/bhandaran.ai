# ---------------------------------------------------------------
# Bookings (M8): owners record deals made in person or by phone.
#
#   POST /api/bookings                 [owner]  record an offline booking
#   GET  /api/bookings/owner           [owner]  bookings at my godowns
#   GET  /api/bookings/mine            [renter] my bookings
#   POST /api/bookings/{id}/confirm    [renter] confirm a pending booking
#
# The renter is found by email, or created as an unclaimed renter
# (like an invite, M4). Whether the renter must confirm, and what
# happens after the timeout, follows the booking rules (M2).
# ---------------------------------------------------------------
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.common import commit_or_409
from app.auth import normalize_email, require_owner, require_renter
from app.bookings import booked_quantity, is_retryable, settle, settle_all
from app.config import get_settings
from app.db import get_session
from app.email_sender import send_email
from app.mail_events import is_suppressed
from app.models import (
    Booking,
    City,
    StockType,
    Unit,
    User,
    UserRole,
    Warehouse,
    WarehouseStockType,
)
from app.platform_settings import effective_settings
from app.schemas.booking import BookingOut, OfflineBookingIn

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/bookings", tags=["bookings"])

DbSession = Annotated[Session, Depends(get_session)]
OwnerUser = Annotated[User, Depends(require_owner)]
RenterUser = Annotated[User, Depends(require_renter)]

MAX_ATTEMPTS = 3


# ---------- helpers ----------


def booking_out(session: Session, booking: Booking) -> BookingOut:
    warehouse = session.get(Warehouse, booking.warehouse_id)
    city = session.get(City, warehouse.city_id) if warehouse else None
    owner = session.get(User, booking.owner_id)
    renter = session.get(User, booking.renter_id)
    stock = session.get(StockType, booking.stock_type_id)
    unit = session.get(Unit, warehouse.unit_id) if warehouse else None
    return BookingOut(
        id=booking.id,
        warehouse_id=booking.warehouse_id,
        warehouse_name=warehouse.name if warehouse else "",
        city_name=city.name if city else None,
        owner_name=owner.name if owner else None,
        renter_name=renter.name if renter else None,
        renter_email=renter.email if renter else None,
        stock_type_name=stock.name if stock else None,
        unit_name=unit.name if unit else None,
        quantity=booking.quantity,
        start_date=booking.start_date,
        end_date=booking.end_date,
        rate_per_unit_month=booking.rate_per_unit_month,
        channel=booking.channel,
        status=booking.status,
        unverified=booking.unverified,
        confirmation_due_at=booking.confirmation_due_at,
        confirmed_at=booking.confirmed_at,
        created_at=booking.created_at,
    )


def unprocessable(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, message)


def check_request(session: Session, owner: User, body: OfflineBookingIn) -> tuple[Warehouse, str]:
    """Everything that can be checked before touching capacity."""
    warehouse = session.get(Warehouse, body.warehouse_id)
    if warehouse is None or warehouse.owner_id != owner.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Godown not found")
    if warehouse.status != "APPROVED":
        raise unprocessable("Only approved godowns can take bookings")
    accepted = session.scalar(
        select(WarehouseStockType.id).where(
            WarehouseStockType.warehouse_id == warehouse.id,
            WarehouseStockType.stock_type_id == body.stock_type_id,
        )
    )
    if accepted is None:
        raise unprocessable("This godown doesn't accept that stock type")
    if body.end_date < body.start_date:
        raise unprocessable("The end date must be on or after the start date")
    if body.end_date < datetime.now(UTC).date():
        raise unprocessable("The booking has already ended")
    if body.quantity > warehouse.capacity:
        raise unprocessable(f"This godown holds at most {warehouse.capacity}")
    try:
        email = normalize_email(body.renter_email)
    except ValueError as error:
        raise unprocessable(str(error)) from error
    if email == owner.email:
        raise unprocessable("You can't book space for yourself")
    return warehouse, email


def find_or_add_renter(session: Session, owner: User, email: str, name: str) -> tuple[User, bool]:
    """The renter with this email, or a new unclaimed one. Returns (renter, is_new)."""
    renter = session.scalar(select(User).where(User.email == email))
    if renter is None:
        if not name:
            raise unprocessable("New renter: enter their name too")
        renter = User(email=email, name=name, status="UNCLAIMED", invited_by_id=owner.id)
        renter.roles.append(UserRole(role="RENTER"))
        session.add(renter)
        session.flush()
        return renter, True
    if renter.status == "SUSPENDED":
        raise unprocessable("This renter's account is suspended")
    if "RENTER" not in renter.role_names:
        renter.roles.append(UserRole(role="RENTER"))
    return renter, False


def tell_renter(booking: BookingOut, needs_confirmation: bool, is_new: bool) -> None:
    """Email the renter about the booking (best effort: a failure is only logged)."""
    settings = get_settings()
    lines = [
        f"{booking.owner_name or 'A godown owner'} recorded a booking for you on bhandaran.ai:",
        f"{booking.quantity} {booking.unit_name} of {booking.stock_type_name} at "
        f"{booking.warehouse_name} ({booking.city_name}),",
        f"from {booking.start_date:%d %b %Y} to {booking.end_date:%d %b %Y}, "
        f"at Rs {booking.rate_per_unit_month} per {booking.unit_name} per month.",
        "",
    ]
    if needs_confirmation:
        due = booking.confirmation_due_at
        lines.append(
            "Please log in to bhandaran.ai with this email address and confirm it under "
            f"My bookings{f' by {due:%d %b %Y}' if due else ''}."
        )
    else:
        lines.append("You can see it under My bookings when you log in to bhandaran.ai.")
    if is_new:
        lines.append("An account has been set up for you; logging in with this email claims it.")
    if settings.otp_delivery != "email" or not booking.renter_email:
        logger.info("Booking notice not emailed (delivery mode %s)", settings.otp_delivery)
        return
    try:
        send_email(booking.renter_email, "A booking for you on bhandaran.ai", "\n".join(lines))
    except RuntimeError:
        logger.warning("Booking notice could not be emailed")


# ---------- owner ----------


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def record_offline_booking(body: OfflineBookingIn, owner: OwnerUser, session: DbSession):
    warehouse, email = check_request(session, owner, body)
    rules = effective_settings(session, owner.id)
    needs_confirmation = bool(rules["offline_booking_requires_renter_confirmation"].value)
    timeout_days = int(rules["renter_confirmation_timeout_days"].value)
    timeout_action = str(rules["on_timeout_action"].value)
    warehouse_id = warehouse.id

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            # Lock the godown row: two bookings for the same godown can't both
            # pass the space check (on DSQL, the second gets a conflict instead).
            locked = session.scalar(
                select(Warehouse).where(Warehouse.id == warehouse_id).with_for_update()
            )
            taken = booked_quantity(session, warehouse_id, body.start_date, body.end_date)
            free = locked.capacity - taken
            if body.quantity > free:
                session.rollback()
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"Only {max(free, 0)} free for those dates",
                )

            renter, is_new = find_or_add_renter(session, owner, email, body.renter_name)
            if is_suppressed(session, email) and is_new:
                session.rollback()
                raise unprocessable(
                    "This address can't receive our emails. Please use another address."
                )

            now = datetime.now(UTC)
            booking = Booking(
                warehouse_id=warehouse_id,
                owner_id=owner.id,
                renter_id=renter.id,
                stock_type_id=body.stock_type_id,
                quantity=body.quantity,
                start_date=body.start_date,
                end_date=body.end_date,
                rate_per_unit_month=body.rate_per_unit_month,
                channel="OFFLINE",
                status="PENDING_RENTER_CONFIRMATION" if needs_confirmation else "CONFIRMED",
                confirmation_due_at=now + timedelta(days=timeout_days)
                if needs_confirmation
                else None,
                confirmed_at=None if needs_confirmation else now,
            )
            settle(booking, timeout_action, now)  # CONFIRMED + already started -> ACTIVE
            # Touch the godown so concurrent bookings conflict on DSQL.
            locked.updated_at = now
            session.add(booking)
            session.commit()
            break
        except OperationalError as error:
            session.rollback()
            if is_retryable(error) and attempt < MAX_ATTEMPTS:
                logger.info("Booking conflict, retrying (attempt %s)", attempt)
                continue
            if is_retryable(error):
                raise HTTPException(
                    status.HTTP_409_CONFLICT, "The godown is busy right now, please try again"
                ) from error
            raise

    session.refresh(booking)
    out = booking_out(session, booking)
    tell_renter(out, needs_confirmation, is_new)
    return out


@router.get("/owner", response_model=list[BookingOut])
def owner_bookings(owner: OwnerUser, session: DbSession):
    rows = list(
        session.scalars(
            select(Booking).where(Booking.owner_id == owner.id).order_by(Booking.created_at.desc())
        )
    )
    settle_all(session, rows)
    return [booking_out(session, row) for row in rows]


# ---------- renter ----------


@router.get("/mine", response_model=list[BookingOut])
def my_bookings(renter: RenterUser, session: DbSession):
    rows = list(
        session.scalars(
            select(Booking)
            .where(Booking.renter_id == renter.id)
            .order_by(Booking.created_at.desc())
        )
    )
    settle_all(session, rows)
    return [booking_out(session, row) for row in rows]


@router.post("/{booking_id}/confirm", response_model=BookingOut)
def confirm(booking_id: uuid.UUID, renter: RenterUser, session: DbSession):
    booking = session.get(Booking, booking_id)
    if booking is None or booking.renter_id != renter.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Booking not found")
    settle_all(session, [booking])
    if booking.status != "PENDING_RENTER_CONFIRMATION":
        raise HTTPException(status.HTTP_409_CONFLICT, "This booking doesn't need confirming")
    now = datetime.now(UTC)
    booking.status = "CONFIRMED"
    booking.confirmed_at = now
    booking.unverified = False
    settle(booking, "AUTO_CONFIRM", now)  # already started -> ACTIVE
    commit_or_409(session, "Please try again")
    session.refresh(booking)
    return booking_out(session, booking)
