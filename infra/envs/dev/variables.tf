# ---------------------------------------------------------------
# Inputs for the dev stack. Real values go in terraform.tfvars
# (git-ignored); see terraform.tfvars.example.
# ---------------------------------------------------------------

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "alert_email" {
  description = "Email for DSQL cost alerts"
  type        = string
}

# Angular dev server origin(s) allowed to upload photos.
variable "photo_cors_origins" {
  description = "Browser origins allowed to use presigned photo URLs"
  type        = list(string)
  default     = ["http://localhost:4200"]
}

variable "dsql_daily_dpu_threshold" {
  description = "Alarm when daily DSQL TotalDPU exceeds this"
  type        = number
  default     = 10000
}

# Repository whose main branch may deploy app code to dev.
variable "github_repo" {
  description = "GitHub repository in owner/name form"
  type        = string
  default     = "arpit-jain-mygit/bhandaran.ai"
}

# GitHub OIDC subject prefix for this repo (immutable-subject format).
# See modules/github_oidc/variables.tf for how to look it up.
variable "github_subject_prefix" {
  description = "Prefix of the GitHub OIDC sub claim"
  type        = string
  default     = "repo:arpit-jain-mygit@250862261/bhandaran.ai@1444180371"
}

# Verified SES sender address for login codes. Set in terraform.tfvars
# (git-ignored), not here. SES emails this address a link to verify.
variable "mail_from" {
  description = "Verified SES sender address for login emails"
  type        = string
}
