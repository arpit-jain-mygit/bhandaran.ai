# ---------------------------------------------------------------
# Outputs of the s3_bucket module.
# ---------------------------------------------------------------

# Bucket name: FastAPI needs it to create presigned URLs.
output "bucket_name" {
  description = "Name of the bucket"
  value       = aws_s3_bucket.this.bucket
}

# Bucket ARN: used in IAM policies that grant read/write access.
output "bucket_arn" {
  description = "ARN of the bucket"
  value       = aws_s3_bucket.this.arn
}
