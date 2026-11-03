# ---------------------------------------------------------------
# Bounce and complaint reports from SES (bounce handling).
#
# SES publishes each report to an SNS topic; SNS calls the API Lambda
# with the report. A PERMANENT bounce or a complaint adds the address
# to email_suppression, so login codes and invites stop going there.
# Temporary bounces (full mailbox, server down) are only logged.
# ---------------------------------------------------------------
import json
import logging

from sqlalchemy.orm import Session

from app.models import EmailSuppression

logger = logging.getLogger(__name__)


def is_ses_sns_event(event: object) -> bool:
    """True for an SNS notification (how SES reports bounces and complaints)."""
    if not isinstance(event, dict):
        return False
    records = event.get("Records")
    return bool(records) and records[0].get("EventSource") == "aws:sns"


def addresses_to_suppress(message: dict) -> list[tuple[str, str]]:
    """(address, reason) pairs that should stop future mail."""
    # Configuration-set reports say "eventType"; older identity reports say "notificationType".
    kind = message.get("eventType") or message.get("notificationType")
    if kind == "Bounce":
        bounce = message.get("bounce", {})
        if bounce.get("bounceType") != "Permanent":
            logger.info("Temporary bounce, not suppressed")
            return []
        return [(r["emailAddress"], "BOUNCE") for r in bounce.get("bouncedRecipients", [])]
    if kind == "Complaint":
        complaint = message.get("complaint", {})
        return [(r["emailAddress"], "COMPLAINT") for r in complaint.get("complainedRecipients", [])]
    return []


def record_mail_events(session: Session, event: dict) -> int:
    """Store suppressions from an SNS event. Returns how many addresses were added."""
    added = 0
    for record in event["Records"]:
        message = json.loads(record["Sns"]["Message"])
        for raw_address, reason in addresses_to_suppress(message):
            address = raw_address.strip().lower()
            if session.get(EmailSuppression, address) is None:
                session.add(EmailSuppression(email=address, reason=reason))
                added += 1
                logger.warning("Suppressed %s after %s", address[:2] + "***", reason)
    session.commit()
    return added


def is_suppressed(session: Session, email: str) -> bool:
    return session.get(EmailSuppression, email) is not None
