# ---------------------------------------------------------------
# Tables for platform settings (M2). See app/platform_settings.py
# for the list of settings and how the effective value is chosen.
# Only values that differ from the code defaults are stored.
# ---------------------------------------------------------------
import uuid

from sqlalchemy import String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UuidPkMixin


class PlatformSetting(TimestampMixin, Base):
    """A platform-wide value chosen by an admin (overrides the code default)."""

    __tablename__ = "platform_setting"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)  # JSON text, e.g. "true"


class OwnerSetting(UuidPkMixin, TimestampMixin, Base):
    """One owner's own value for a setting (overrides the platform value)."""

    __tablename__ = "owner_setting"
    __table_args__ = (UniqueConstraint("owner_id", "key", name="uq_owner_setting_owner_key"),)

    # The owner this applies to. No foreign key yet: owner accounts
    # arrive in M3/M4, which will add the link to the owner table.
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)  # JSON text
