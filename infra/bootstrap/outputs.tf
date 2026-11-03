# ---------------------------------------------------------------
# Values printed after "terraform apply". Copy the bucket name into
# each env's backend.hcl (see infra/README.md).
# ---------------------------------------------------------------

output "state_bucket_name" {
  description = "S3 bucket that stores Terraform state for all stacks"
  value       = aws_s3_bucket.state.bucket
}

output "state_bucket_arn" {
  description = "ARN of the state bucket (used by the CI roles)"
  value       = aws_s3_bucket.state.arn
}
