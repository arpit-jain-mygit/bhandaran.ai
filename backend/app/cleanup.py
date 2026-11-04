# ---------------------------------------------------------------
# Deleting test data (admin only).
#
# Removes chosen accounts and godowns together with everything that
# belongs to them: bookings, stock types, photos (also in S3), login
# codes, owner settings and mail suppression entries.
#
#   plan()   - works out what would be removed (reads only)
#   remove() - removes it in one database transaction
#
# Rules:
#   - the admin asking can't delete their own account
#   - an email or godown ID that doesn't exist is reported, not an error
#   - an owner's godowns go with the owner; invitees they invited stay
#     (their link to the inviting owner is cleared)
# ---------------------------------------------------------------
import logging
import uuid
from dataclasses import dataclass, field

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app import photos
from app.auth import mask_email, normalize_email
from app.models import (
    Booking,
    EmailSuppression,
    OtpChallenge,
    OwnerSetting,
    User,
    UserRole,
    Warehouse,
    WarehousePhoto,
    WarehouseStockType,
)

log = logging.getLogger(__name__)


@dataclass
class Plan:
    user_ids: list[uuid.UUID] = field(default_factory=list)
    accounts: list[str] = field(default_factory=list)  # masked, for display
    emails: list[str] = field(default_factory=list)  # normalized, found in DB
    missing_emails: list[str] = field(default_factory=list)
    warehouse_ids: list[uuid.UUID] = field(default_factory=list)
    missing_warehouse_ids: list[uuid.UUID] = field(default_factory=list)
    bookings: int = 0
    photo_keys: list[str] = field(default_factory=list)
    login_codes: int = 0
    owner_settings: int = 0
    suppressed_emails: int = 0
    invitees_released: int = 0


def plan(
    session: Session,
    *,
    protected_email: str | None,
    raw_emails: list[str],
    warehouse_ids: list[uuid.UUID],
) -> Plan:
    """Work out what would be removed. Reads the database only."""
    if not raw_emails and not warehouse_ids:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Give an email or a godown ID")

    try:
        emails = sorted({normalize_email(raw) for raw in raw_emails})
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    if protected_email in emails:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "You can't delete your own account"
        )

    result = Plan()
    users = list(session.scalars(select(User).where(User.email.in_(emails))))
    result.user_ids = [user.id for user in users]
    result.accounts = [mask_email(user.email) for user in users]
    result.emails = [user.email for user in users]
    result.missing_emails = [e for e in emails if e not in result.emails]

    owned = select(Warehouse.id).where(Warehouse.owner_id.in_(result.user_ids))
    found = set(session.scalars(select(Warehouse.id).where(Warehouse.id.in_(warehouse_ids))))
    owned_ids = set(session.scalars(owned))
    result.warehouse_ids = sorted(owned_ids | found)
    result.missing_warehouse_ids = [w for w in warehouse_ids if w not in found]

    result.bookings = session.scalar(
        select(func.count())
        .select_from(Booking)
        .where(booking_match(result.user_ids, result.warehouse_ids))
    )
    result.photo_keys = list(
        session.scalars(
            select(WarehousePhoto.s3_key).where(
                WarehousePhoto.warehouse_id.in_(result.warehouse_ids)
            )
        )
    )
    result.login_codes = session.scalar(
        select(func.count()).select_from(OtpChallenge).where(OtpChallenge.email.in_(emails))
    )
    result.owner_settings = session.scalar(
        select(func.count())
        .select_from(OwnerSetting)
        .where(OwnerSetting.owner_id.in_(result.user_ids))
    )
    result.suppressed_emails = session.scalar(
        select(func.count()).select_from(EmailSuppression).where(EmailSuppression.email.in_(emails))
    )
    result.invitees_released = session.scalar(
        select(func.count())
        .select_from(User)
        .where(User.invited_by_id.in_(result.user_ids), User.id.notin_(result.user_ids))
    )
    return result


def booking_match(user_ids: list[uuid.UUID], warehouse_ids: list[uuid.UUID]):
    """Bookings that touch a removed godown, owner or renter."""
    return or_(
        Booking.warehouse_id.in_(warehouse_ids),
        Booking.owner_id.in_(user_ids),
        Booking.renter_id.in_(user_ids),
    )


def remove(session: Session, chosen: Plan) -> list[str]:
    """
    Delete the planned rows in one transaction (the caller commits).
    Children go before parents, because the database checks foreign keys.
    Returns the S3 photo keys to delete after the commit.
    """
    session.execute(delete(Booking).where(booking_match(chosen.user_ids, chosen.warehouse_ids)))
    session.execute(
        delete(WarehousePhoto).where(WarehousePhoto.warehouse_id.in_(chosen.warehouse_ids))
    )
    session.execute(
        delete(WarehouseStockType).where(WarehouseStockType.warehouse_id.in_(chosen.warehouse_ids))
    )
    session.execute(delete(Warehouse).where(Warehouse.id.in_(chosen.warehouse_ids)))
    session.execute(delete(OwnerSetting).where(OwnerSetting.owner_id.in_(chosen.user_ids)))
    session.execute(delete(OtpChallenge).where(OtpChallenge.email.in_(chosen.emails)))
    session.execute(delete(EmailSuppression).where(EmailSuppression.email.in_(chosen.emails)))
    session.execute(
        update(User).where(User.invited_by_id.in_(chosen.user_ids)).values(invited_by_id=None)
    )
    session.execute(delete(UserRole).where(UserRole.user_id.in_(chosen.user_ids)))
    session.execute(delete(User).where(User.id.in_(chosen.user_ids)))
    return chosen.photo_keys


def delete_photo_files(keys: list[str]) -> int:
    """Remove photo files from S3 after the rows are gone. Returns how many failed."""
    failed = 0
    for key in keys:
        try:
            photos.delete_object(key)
        except Exception:  # best effort: the rows are already gone
            log.warning("Could not delete photo file %s", key, exc_info=True)
            failed += 1
    return failed
