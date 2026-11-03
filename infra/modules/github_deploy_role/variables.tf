# ---------------------------------------------------------------
# Inputs for the github_deploy_role module.
# ---------------------------------------------------------------

variable "name" {
  description = "IAM role name, e.g. bhandaran-dev-github-deploy"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository allowed to deploy, owner/name"
  type        = string
}

variable "lambda_function_arn" {
  description = "The only Lambda function this role may update"
  type        = string
}

variable "web_bucket_arn" {
  description = "The only S3 bucket this role may write web files to"
  type        = string
}

variable "distribution_arn" {
  description = "The only CloudFront distribution this role may invalidate"
  type        = string
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
