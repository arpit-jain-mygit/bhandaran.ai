# ---------------------------------------------------------------
# TEMPORARY admin check (until M3 adds phone-OTP login + roles).
#
# Admin write endpoints depend on require_admin. The caller must send
# the secret from settings.admin_api_key in the X-Admin-Key header.
# If no key is configured, every admin write is refused.
# ---------------------------------------------------------------
import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

from app.config import get_settings


def require_admin(x_admin_key: Annotated[str | None, Header()] = None) -> None:
    expected = get_settings().admin_api_key

    # compare_digest takes the same time for right and wrong keys,
    # so attackers can't guess the key by measuring response time.
    if not expected or not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin key missing or wrong",
        )
