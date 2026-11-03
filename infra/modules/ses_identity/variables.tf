# ---------------------------------------------------------------
# Inputs for the ses_identity module.
# ---------------------------------------------------------------

# Address (or domain) the app sends email from, e.g. a verified Gmail.
variable "identity" {
  description = "Email address (or domain) SES may send from"
  type        = string
}

# Region the identity lives in (must match the Lambda's region).
variable "region" {
  description = "AWS region for the SES identity"
  type        = string
}

# Needed to build the identity ARN for IAM policies.
variable "account_id" {
  description = "AWS account ID"
  type        = string
}
