# ---------------------------------------------------------------
# Inputs for the web_hosting module.
# ---------------------------------------------------------------

# Used in CloudFront names/comments, e.g. "bhandaran-dev".
variable "name" {
  description = "Name prefix for CloudFront resources"
  type        = string
}

# Globally unique name for the bucket holding the Angular build.
variable "bucket_name" {
  description = "S3 bucket name for the web app files"
  type        = string
}

# true = "terraform destroy" also deletes the files (dev only).
variable "force_destroy" {
  description = "Allow deleting the bucket even if it contains files"
  type        = bool
  default     = false
}

# API Gateway hostname (no https://) that serves /api/*.
variable "api_domain" {
  description = "Hostname of the API origin"
  type        = string
}
