# ---------------------------------------------------------------
# Login API (M3): email address + one-time code (OTP).
#
#   POST /api/auth/otp     {email}               email a 6-digit code
#   POST /api/auth/verify  {email, code}         check it -> logged in,
#                                                or "signup_required"
#   POST /api/auth/signup  {signup_token, name, role}  create account
#   GET  /api/auth/me                            who am I?
#   POST /api/auth/logout                        end the session
#
# Abuse limits: 5 codes per email per hour; a code expires after
# 5 minutes and stops working after 5 wrong guesses.
# ---------------------------------------------------------------
import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.common import commit_or_409
from app.auth import (
    CurrentUser,
    clear_session_cookie,
    create_signup_token,
    email_from_signup_token,
    hash_otp,
    mask_email,
    new_otp_code,
    normalize_email,
    otp_matches,
    set_session_cookie,
)
from app.config import get_settings
from app.db import get_session
from app.email_sender import send_login_code
from app.models import OtpChallenge, User, UserRole
from app.schemas.auth import (
    OtpRequest,
    OtpSent,
    OtpVerify,
    SignupRequest,
    UserOut,
    VerifyResult,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["login"])

DbSession = Annotated[Session, Depends(get_session)]

OTP_LIFETIME = timedelta(minutes=5)
MAX_CODES_PER_HOUR = 5
MAX_WRONG_GUESSES = 5
EMAIL_TAKEN = "An account already exists for this email"


# ---------- helpers ----------


def email_or_422(raw: str) -> str:
    try:
        return normalize_email(raw)
    except ValueError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error


def user_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, name=user.name, roles=user.role_names)


def deliver_code(email: str, code: str) -> str | None:
    """
    Send the code. "email" mails it through SES (never logged).
    "log" writes it to the server log (local dev only).
    "response" also returns it in the reply, so the local login page can show it.
    """
    settings = get_settings()
    if settings.otp_delivery == "email":
        try:
            send_login_code(email, code, minutes=int(OTP_LIFETIME.total_seconds() // 60))
        except RuntimeError as error:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE, "We could not send the code. Try again."
            ) from error
        return None

    logger.warning("OTP for %s: %s", mask_email(email), code)
    if settings.otp_delivery == "response" and settings.db_mode == "local":
        return code
    return None


# ---------- endpoints ----------


@router.post("/otp", response_model=OtpSent, status_code=status.HTTP_202_ACCEPTED)
def request_otp(body: OtpRequest, session: DbSession):
    email = email_or_422(body.email)
    now = datetime.now(UTC)

    # Limit: a few codes per email per hour (stops inbox bombing / guessing).
    recent = session.scalar(
        select(func.count())
        .select_from(OtpChallenge)
        .where(OtpChallenge.email == email, OtpChallenge.created_at > now - timedelta(hours=1))
    )
    if recent >= MAX_CODES_PER_HOUR:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many codes requested. Try again in an hour."
        )

    code = new_otp_code()
    # Send first: if sending fails, no code is stored and the user can retry.
    dev_code = deliver_code(email, code)
    session.add(
        OtpChallenge(email=email, code_hash=hash_otp(email, code), expires_at=now + OTP_LIFETIME)
    )
    commit_or_409(session, "Please try again")

    return OtpSent(
        sent=True,
        expires_in_seconds=int(OTP_LIFETIME.total_seconds()),
        dev_code=dev_code,
    )


@router.post("/verify", response_model=VerifyResult)
def verify_otp(body: OtpVerify, response: Response, session: DbSession):
    email = email_or_422(body.email)
    now = datetime.now(UTC)

    # Only the newest unused, unexpired code counts.
    challenge = session.scalar(
        select(OtpChallenge)
        .where(
            OtpChallenge.email == email,
            OtpChallenge.consumed_at.is_(None),
            OtpChallenge.expires_at > now,
        )
        .order_by(OtpChallenge.created_at.desc())
        .limit(1)
    )
    if challenge is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code expired. Request a new one.")
    if challenge.attempts >= MAX_WRONG_GUESSES:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many wrong tries. Request a new code."
        )

    if not otp_matches(email, body.code, challenge.code_hash):
        challenge.attempts += 1
        commit_or_409(session, "Please try again")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Wrong code")

    # Correct: burn the code so it can't be used again.
    challenge.consumed_at = now
    commit_or_409(session, "Please try again")

    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        return VerifyResult(status="signup_required", signup_token=create_signup_token(email))
    if user.status != "ACTIVE":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is suspended")

    set_session_cookie(response, user.id)
    return VerifyResult(status="logged_in", user=user_out(user))


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, response: Response, session: DbSession):
    email = email_from_signup_token(body.signup_token)
    if session.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, EMAIL_TAKEN)

    user = User(email=email, name=body.name)
    user.roles.append(UserRole(role=body.role))
    session.add(user)
    commit_or_409(session, EMAIL_TAKEN)
    session.refresh(user)

    set_session_cookie(response, user.id)
    return user_out(user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user_out(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    clear_session_cookie(response)
