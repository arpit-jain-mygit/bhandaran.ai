# ---------------------------------------------------------------
# Mail suppression (bounce handling). When SES reports that an
# address permanently bounced or complained, it is listed here and
# the app stops sending it login codes or invites.
# ---------------------------------------------------------------
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

SUPPRESSION_REASONS = ("BOUNCE", "COMPLAINT")


class EmailSuppression(Base):
    __tablename__ = "email_suppression"
    __table_args__ = (
        CheckConstraint(f"reason IN {SUPPRESSION_REASONS}", name="ck_email_suppression_reason"),
    )

    # Lower-case address (see normalize_email).
    email: Mapped[str] = mapped_column(String(254), primary_key=True)
    reason: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
