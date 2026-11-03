# ---------------------------------------------------------------
# Inputs for the shared stack. Real values go in terraform.tfvars
# (git-ignored); see terraform.tfvars.example.
# ---------------------------------------------------------------

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

# Same bucket name as in backend.hcl (output of infra/bootstrap).
variable "state_bucket_name" {
  description = "Terraform state bucket name"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository allowed to deploy, owner/name"
  type        = string
  default     = "arpit-jain-mygit/bhandaran.ai"
}

# false = reuse the account's existing GitHub OIDC provider.
variable "create_oidc_provider" {
  description = "Create the GitHub OIDC provider in this account"
  type        = bool
  default     = false
}

variable "alert_email" {
  description = "Email for budget alerts"
  type        = string
}

variable "monthly_budget_usd" {
  description = "Monthly budget in USD for bhandaran resources"
  type        = number
  default     = 10
}

# GitHub OIDC subject prefix for this repo (immutable-subject format).
# See modules/github_oidc/variables.tf for how to look it up.
variable "github_subject_prefix" {
  description = "Prefix of the GitHub OIDC sub claim"
  type        = string
  default     = "repo:arpit-jain-mygit@250862261/bhandaran.ai@1444180371"
}
