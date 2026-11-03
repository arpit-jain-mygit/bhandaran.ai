# ---------------------------------------------------------------
# Inputs for the github_oidc module.
# ---------------------------------------------------------------

# GitHub repository allowed to assume the roles, as "owner/name".
variable "github_repo" {
  description = "GitHub repository in owner/name form"
  type        = string
}

# Prefix for role names, e.g. "bhandaran" -> bhandaran-github-plan.
variable "name_prefix" {
  description = "Prefix for IAM role names"
  type        = string
}

# The ARN of the Terraform state bucket (from the bootstrap stack).
variable "state_bucket_arn" {
  description = "ARN of the S3 bucket holding Terraform state"
  type        = string
}

# Set true only if this AWS account has NO GitHub OIDC provider yet.
variable "create_oidc_provider" {
  description = "Create the GitHub OIDC provider (false = reuse existing)"
  type        = bool
  default     = false
}

# Start of GitHub's OIDC "sub" claim for this repo. Classic format is
# "repo:owner/name"; repos using GitHub's immutable subject format
# look like "repo:owner@<id>/name@<id>". Find yours with:
#   gh api repos/<owner>/<name>/actions/oidc/customization/sub
# (field "sub_claim_prefix"; if absent, use "repo:owner/name").
variable "github_subject_prefix" {
  description = "Prefix of the GitHub OIDC sub claim (null = repo:<github_repo>)"
  type        = string
  default     = null
}
