# ---------------------------------------------------------------
# Inputs for the s3_bucket module.
# ---------------------------------------------------------------

# Globally unique bucket name (include the account ID to be safe).
variable "bucket_name" {
  description = "Globally unique S3 bucket name"
  type        = string
}

# true = "terraform destroy" also deletes files inside (dev only).
variable "force_destroy" {
  description = "Allow deleting the bucket even if it contains files"
  type        = bool
  default     = false
}

# Web origins allowed to upload/download via presigned URLs,
# e.g. ["http://localhost:4200"]. Empty list = no CORS rule.
variable "cors_allowed_origins" {
  description = "Browser origins allowed to use presigned URLs"
  type        = list(string)
  default     = []
}
