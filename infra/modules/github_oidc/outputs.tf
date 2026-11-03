# ---------------------------------------------------------------
# Outputs of the github_oidc module. Put these ARNs into GitHub
# repo variables (Settings -> Secrets and variables -> Actions).
# ---------------------------------------------------------------

output "plan_role_arn" {
  description = "Role for terraform plan (pull requests)"
  value       = aws_iam_role.plan.arn
}

output "apply_role_arn" {
  description = "Role for terraform apply (main branch only)"
  value       = aws_iam_role.apply.arn
}
