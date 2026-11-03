# ---------------------------------------------------------------
# Outputs of the dev stack: values the FastAPI app config needs.
# ---------------------------------------------------------------

output "dsql_endpoint" {
  description = "DSQL hostname (port 5432, database postgres)"
  value       = module.dsql.endpoint
}

output "dsql_cluster_id" {
  description = "DSQL cluster identifier"
  value       = module.dsql.identifier
}

output "dsql_cluster_arn" {
  description = "DSQL cluster ARN (for IAM dsql:DbConnect policies)"
  value       = module.dsql.arn
}

output "photos_bucket_name" {
  description = "S3 bucket for warehouse photos"
  value       = module.photos.bucket_name
}

# ---------- Hosting (M0b) ----------

output "web_url" {
  description = "Public URL of the dev app (UI + /api)"
  value       = module.web.url
}

output "web_bucket_name" {
  description = "GitHub variable DEV_WEB_BUCKET"
  value       = module.web.bucket_name
}

output "cloudfront_distribution_id" {
  description = "GitHub variable DEV_CLOUDFRONT_ID"
  value       = module.web.distribution_id
}

output "api_function_name" {
  description = "GitHub variable DEV_API_FUNCTION"
  value       = module.api.function_name
}

output "github_deploy_role_arn" {
  description = "GitHub variable AWS_DEV_DEPLOY_ROLE_ARN"
  value       = module.github_deploy.role_arn
}

# ---------- Email (SES) ----------

output "mail_from" {
  description = "Verified SES sender address used for login codes"
  value       = var.mail_from
}
