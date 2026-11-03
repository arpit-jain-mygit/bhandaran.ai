# ---------------------------------------------------------------
# Outputs of the web_hosting module.
# ---------------------------------------------------------------

# Public URL of the app.
output "url" {
  description = "HTTPS URL of the web app"
  value       = "https://${aws_cloudfront_distribution.this.domain_name}"
}

# CI needs these to upload files and clear the CloudFront cache.
output "bucket_name" {
  description = "S3 bucket holding the Angular build"
  value       = module.bucket.bucket_name
}

output "bucket_arn" {
  description = "ARN of the web bucket"
  value       = module.bucket.bucket_arn
}

output "distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = aws_cloudfront_distribution.this.id
}

output "distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.this.arn
}
