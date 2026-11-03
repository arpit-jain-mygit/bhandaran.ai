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
