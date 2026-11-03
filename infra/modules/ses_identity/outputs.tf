# ---------------------------------------------------------------
# Outputs of the ses_identity module.
# ---------------------------------------------------------------

# ARN IAM policies use to allow sending from this identity.
output "identity_arn" {
  description = "ARN of the SES identity"
  value       = local.identity_arn
}
