# ---------------------------------------------------------------
# Outputs of the dsql module: what the app and alarms need to know.
# ---------------------------------------------------------------

# Cluster ID: used for IAM policies and the CloudWatch "ClusterId" dimension.
output "identifier" {
  description = "DSQL cluster identifier"
  value       = aws_dsql_cluster.this.identifier
}

# Full ARN: used when granting IAM permission to connect (dsql:DbConnect).
output "arn" {
  description = "DSQL cluster ARN"
  value       = aws_dsql_cluster.this.arn
}

# Hostname the FastAPI app connects to (port 5432, database "postgres").
output "endpoint" {
  description = "Hostname for PostgreSQL clients"
  value       = local.endpoint
}
