# ---------------------------------------------------------------
# JSON shapes for the login API (M3).
# ---------------------------------------------------------------
import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
OtpCode = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{6}$")]


class OtpRequest(BaseModel):
    phone: str  # any common format; normalised to +91XXXXXXXXXX


class OtpSent(BaseModel):
    sent: bool
    expires_in_seconds: int
    # Local development only (OTP_DELIVERY=response): the code itself.
    dev_code: str | None = None


class OtpVerify(BaseModel):
    phone: str
    code: OtpCode


class UserOut(BaseModel):
    id: uuid.UUID
    phone: str
    name: str | None
    roles: list[str]


class VerifyResult(BaseModel):
    # "logged_in": existing user, session cookie set.
    # "signup_required": new phone - finish with POST /api/auth/signup.
    status: Literal["logged_in", "signup_required"]
    user: UserOut | None = None
    signup_token: str | None = None


class SignupRequest(BaseModel):
    signup_token: str
    name: Name
    # People choose Owner or Renter themselves; Admin is never self-chosen.
    role: Literal["OWNER", "RENTER"]
