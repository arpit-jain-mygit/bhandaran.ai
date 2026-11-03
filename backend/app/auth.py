# ---------------------------------------------------------------
# Login building blocks (M3): phone numbers, OTP codes, signed
# tokens, and the "who is calling / what may they do" checks that
# API endpoints depend on.
#
# How a request is identified:
#   1. Browser: an httpOnly cookie "bh_session" (page scripts can't
#      read it; SameSite=Strict so other sites can't send it).
#   2. API clients / tests: header "Authorization: Bearer <token>".
# The token only says WHO the user is. Their roles and status are
# read fresh from the database on every request, so suspending a
# user or removing a role takes effect immediately.
# ---------------------------------------------------------------
import hashlib
import hmac
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.models import User

SESSION_COOKIE = "bh_session"
TOKEN_ALGORITHM = "HS256"
SIGNUP_TOKEN_MINUTES = 10  # time to finish sign-up after the OTP is correct

# Indian mobile: optional +91 / 91 / 0 prefix, then 10 digits starting 6-9.
_PHONE = re.compile(r"^(?:\+?91|0)?([6-9]\d{9})$")


# ---------- phone numbers ----------


def normalize_phone(raw: str) -> str:
    """'98260 12345', '+91-9826012345', '09826012345' -> '+919826012345'."""
    digits = re.sub(r"[\s\-()]", "", raw)
    match = _PHONE.match(digits)
    if not match:
        raise ValueError("Enter a valid 10-digit Indian mobile number")
    return f"+91{match.group(1)}"


def mask_phone(phone: str) -> str:
    """'+919826012345' -> '+91******2345' (safe to write in logs)."""
    return phone[:3] + "******" + phone[-4:]


# ---------- secrets ----------


def _secret() -> bytes:
    key = get_settings().app_secret_key
    if not key:
        # Fail closed: without a secret nobody can log in.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Login is not configured")
    return key.encode()


def _derived_key(purpose: str) -> bytes:
    """Separate keys for separate jobs, all derived from one secret."""
    return hmac.new(_secret(), purpose.encode(), hashlib.sha256).digest()


# ---------- OTP codes ----------


def new_otp_code() -> str:
    """Random 6-digit code, e.g. '048213'."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(phone: str, code: str) -> str:
    """Only this hash is stored, never the code itself."""
    return hmac.new(_derived_key("otp"), f"{phone}:{code}".encode(), hashlib.sha256).hexdigest()


def otp_matches(phone: str, code: str, stored_hash: str) -> bool:
    # compare_digest takes the same time for right and wrong codes.
    return hmac.compare_digest(hash_otp(phone, code), stored_hash)


# ---------- signed tokens (JWT) ----------


def _encode(claims: dict, lifetime: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {**claims, "iat": now, "exp": now + lifetime}
    return jwt.encode(payload, _derived_key("jwt"), algorithm=TOKEN_ALGORITHM)


def _decode(token: str, expected_type: str) -> dict:
    try:
        claims = jwt.decode(token, _derived_key("jwt"), algorithms=[TOKEN_ALGORITHM])
    except jwt.PyJWTError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please log in again") from error
    if claims.get("typ") != expected_type:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please log in again")
    return claims


def create_session_token(user_id: uuid.UUID) -> str:
    """Proof that this user logged in. Lasts settings.session_days."""
    return _encode(
        {"sub": str(user_id), "typ": "session"}, timedelta(days=get_settings().session_days)
    )


def create_signup_token(phone: str) -> str:
    """Proof that this phone passed the OTP check; used to finish sign-up."""
    return _encode({"sub": phone, "typ": "signup"}, timedelta(minutes=SIGNUP_TOKEN_MINUTES))


def phone_from_signup_token(token: str) -> str:
    return _decode(token, "signup")["sub"]


# ---------- session cookie ----------


def set_session_cookie(response: Response, user_id: uuid.UUID) -> None:
    settings = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(user_id),
        max_age=settings.session_days * 24 * 3600,
        httponly=True,  # page scripts can't read it
        secure=settings.cookie_secure,  # HTTPS only
        samesite="strict",  # never sent from other websites
        path="/api",  # only the API needs it
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/api")


# ---------- "who is calling?" dependencies ----------


def get_current_user(
    session: Annotated[Session, Depends(get_session)],
    bh_session: Annotated[str | None, Cookie()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    """The logged-in user, or None for anonymous visitors."""
    token = bh_session
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        return None

    claims = _decode(token, "session")
    try:
        user = session.get(User, uuid.UUID(claims["sub"]))
    except (KeyError, ValueError):
        return None
    if user is None or user.status != "ACTIVE":
        return None
    return user


OptionalUser = Annotated[User | None, Depends(get_current_user)]


def require_user(user: OptionalUser) -> User:
    """Endpoint needs a logged-in user (any role) -> otherwise HTTP 401."""
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please log in")
    return user


CurrentUser = Annotated[User, Depends(require_user)]


def require_role(*roles: str):
    """
    Endpoint needs one of these roles:
      not logged in -> 401, logged in without the role -> 403.
    Usage: dependencies=[Depends(require_role("ADMIN"))]
    """

    def check(user: CurrentUser) -> User:
        if not set(roles) & set(user.role_names):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You don't have access to this")
        return user

    return check


# Shortcuts used by the API modules.
require_admin = require_role("ADMIN")
require_owner = require_role("OWNER")
