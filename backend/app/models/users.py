# ---------------------------------------------------------------
# Users, their roles, and one-time login codes (M3).
#
#   app_user      - one row per phone number ("user" is a reserved
#                   word in PostgreSQL, hence "app_user")
#   user_role     - which roles a user has (OWNER, RENTER, ADMIN);
#                   one person can have several
#   otp_challenge - a 6-digit code sent to a phone; only a hash of
#                   the code is stored
# ---------------------------------------------------------------
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UuidPkMixin

ROLES = ("OWNER", "RENTER", "ADMIN")
USER_STATUSES = ("ACTIVE", "SUSPENDED")


class User(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "app_user"
    __table_args__ = (CheckConstraint(f"status IN {USER_STATUSES}", name="ck_app_user_status"),)

    # Indian mobile in international form, e.g. +919876543210. One account per phone.
    phone: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    name: Mapped[str | None] = mapped_column(String(100))
    # SUSPENDED users can't log in (and existing sessions stop working).
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")

    roles: Mapped[list["UserRole"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def role_names(self) -> list[str]:
        """Roles as a sorted list, e.g. ["OWNER", "RENTER"]."""
        return sorted(role.role for role in self.roles)


class UserRole(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "user_role"
    __table_args__ = (
        UniqueConstraint("user_id", "role", name="uq_user_role_user_role"),
        CheckConstraint(f"role IN {ROLES}", name="ck_user_role_role"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("app_user.id", name="fk_user_role_user"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)

    user: Mapped[User] = relationship(back_populates="roles")


class OtpChallenge(UuidPkMixin, Base):
    __tablename__ = "otp_challenge"
    # Speeds up "latest code for this phone" and the hourly limit.
    __table_args__ = (Index("ix_otp_challenge_phone_created", "phone", "created_at"),)

    phone: Mapped[str] = mapped_column(String(16), nullable=False)
    # HMAC-SHA256 of phone + code (never the code itself).
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Wrong guesses so far; the code stops working after too many.
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    # Set when the code is used, so it can't be used twice.
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
