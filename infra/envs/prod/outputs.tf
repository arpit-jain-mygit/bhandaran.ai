# ---------------------------------------------------------------
# Outputs of the prod stack: values the FastAPI app config needs.
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
