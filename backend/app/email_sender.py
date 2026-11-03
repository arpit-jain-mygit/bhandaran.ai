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


def send_login_code(to_address: str, code: str, minutes: int) -> None:
    """Email the code. Raises RuntimeError if SES refuses or is unreachable."""
    settings = get_settings()
    body = (
        f"Your bhandaran.ai login code is {code}.\n\n"
        f"It works for {minutes} minutes. If you did not ask for it, ignore this email."
    )
    client = boto3.client("sesv2", region_name=settings.aws_region)
    try:
        client.send_email(
            FromEmailAddress=settings.mail_from,
            Destination={"ToAddresses": [to_address]},
            Content={
                "Simple": {
                    "Subject": {"Data": CODE_EMAIL_SUBJECT},
                    "Body": {"Text": {"Data": body}},
                }
            },
        )
    except (ClientError, BotoCoreError) as error:
        # Log the reason for operators; never the code itself.
        logger.error("SES send failed: %s", error)
        raise RuntimeError("Email could not be sent") from error
