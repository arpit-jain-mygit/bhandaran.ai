# ---------------------------------------------------------------
# Sends login codes by email through Amazon SES (M3).
# The sender address must be a verified SES identity (see
# infra/modules/ses_identity). Until SES production access is
# granted, SES only delivers to verified recipient addresses.
# ---------------------------------------------------------------
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

logger = logging.getLogger(__name__)

CODE_EMAIL_SUBJECT = "Your bhandaran.ai login code"
INVITE_EMAIL_SUBJECT = "You are invited to bhandaran.ai"


def send_email(to_address: str, subject: str, body: str) -> None:
    """Send a plain-text email. Raises RuntimeError if SES refuses or is unreachable."""
    settings = get_settings()
    client = boto3.client("sesv2", region_name=settings.aws_region)
    try:
        client.send_email(
            FromEmailAddress=settings.mail_from,
            Destination={"ToAddresses": [to_address]},
            Content={"Simple": {"Subject": {"Data": subject}, "Body": {"Text": {"Data": body}}}},
        )
    except (ClientError, BotoCoreError) as error:
        # Log the reason for operators; never the code itself.
        logger.error("SES send failed: %s", error)
        raise RuntimeError("Email could not be sent") from error


def send_login_code(to_address: str, code: str, minutes: int) -> None:
    """Email a login code. Raises RuntimeError if SES refuses or is unreachable."""
    body = (
        f"Your bhandaran.ai login code is {code}.\n\n"
        f"It works for {minutes} minutes. If you did not ask for it, ignore this email."
    )
    send_email(to_address, CODE_EMAIL_SUBJECT, body)


def send_invitation(to_address: str, owner_name: str) -> None:
    """Tell an invited renter how to claim their account."""
    body = (
        f"{owner_name} has invited you to bhandaran.ai to store stock in their godown.\n\n"
        "Open bhandaran.ai and log in with this email address. We will send you a code "
        "to confirm it is you."
    )
    send_email(to_address, INVITE_EMAIL_SUBJECT, body)
