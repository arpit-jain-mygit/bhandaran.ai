# ---------------------------------------------------------------
# Profiles (M4): every user edits their own name, city and GST number.
# Owners can invite a renter by email; the renter claims the account
# by logging in with a code sent to that email.
#
#   GET  /api/profile/me           my profile
#   PUT  /api/profile/me           change my profile
#   POST /api/profile/renters      [owner] invite a renter by email
# ---------------------------------------------------------------
import re
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.common import commit_or_409
from app.auth import CurrentUser, normalize_email, require_owner
from app.config import get_settings
from app.db import get_session
from app.email_sender import send_invitation
from app.mail_events import is_suppressed
from app.models import City, User, UserRole
from app.schemas.profile import InviteRenter, ProfileIn, ProfileOut

router = APIRouter(prefix="/api/profile", tags=["profile"])

DbSession = Annotated[Session, Depends(get_session)]
OwnerUser = Annotated[User, Depends(require_owner)]

EMAIL_TAKEN = "An account already exists for this email"
_GST = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


# ---------- helpers ----------


def profile_out(session: Session, user: User) -> ProfileOut:
    city = session.get(City, user.city_id) if user.city_id else None
    return ProfileOut(
        id=user.id,
        email=user.email,
        name=user.name,
        status=user.status,
        city_id=user.city_id,
        city_name=city.name if city else None,
        gst_number=user.gst_number,
        roles=user.role_names,
    )


def check_city(session: Session, city_id: uuid.UUID | None) -> None:
    if city_id is not None and session.get(City, city_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Pick a city from the list")


def check_gst(raw: str | None) -> str | None:
    """Optional GST: blank means none; otherwise it must look like a real GST number."""
    if raw is None or not raw.strip():
        return None
    gst = raw.strip().upper()
    if not _GST.match(gst):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Enter a valid 15-character GST number"
        )
    return gst


# ---------- endpoints ----------


@router.get("/me", response_model=ProfileOut)
def my_profile(user: CurrentUser, session: DbSession):
    return profile_out(session, user)


@router.put("/me", response_model=ProfileOut)
def update_my_profile(body: ProfileIn, user: CurrentUser, session: DbSession):
    check_city(session, body.city_id)
    user.name = body.name
    user.city_id = body.city_id
    user.gst_number = check_gst(body.gst_number)
    commit_or_409(session, "Profile was changed at the same time, try again")
    session.refresh(user)
    return profile_out(session, user)


@router.post("/renters", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
def invite_renter(body: InviteRenter, owner: OwnerUser, session: DbSession):
    try:
        email = normalize_email(body.email)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    if session.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, EMAIL_TAKEN)
    if is_suppressed(session, email):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "This address can't receive our emails. Please use another address.",
        )

    # Tell the renter first: if the email fails, no account is created.
    if get_settings().otp_delivery == "email":
        try:
            send_invitation(email, owner.name or "A godown owner")
        except RuntimeError as error:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "We could not send the invite. Try again."
            ) from error

    renter = User(email=email, name=body.name, status="UNCLAIMED", invited_by_id=owner.id)
    renter.roles.append(UserRole(role="RENTER"))
    session.add(renter)
    commit_or_409(session, EMAIL_TAKEN)
    session.refresh(renter)
    return profile_out(session, renter)
