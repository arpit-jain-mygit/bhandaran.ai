# ---------------------------------------------------------------
# SES identity: one email address the app sends login codes from.
# SES emails that address a link; clicking it verifies it.
#
# While the account is in the SES sandbox, SES only sends to
# verified addresses. Request production access to send to anyone.
# ---------------------------------------------------------------

# A single verified sender address (no DNS needed).
resource "aws_sesv2_email_identity" "sender" {
  email_identity = var.identity
}

locals {
  # ARN IAM policies use to allow sending from this identity.
  identity_arn = "arn:aws:ses:${var.region}:${var.account_id}:identity/${var.identity}"
}
