# ---------------------------------------------------------------
# Outputs of the github_deploy_role module.
# Set as GitHub repo variable AWS_DEV_DEPLOY_ROLE_ARN.
# ---------------------------------------------------------------

output "role_arn" {
  description = "Role ARN for the deploy workflow"
  value       = aws_iam_role.deploy.arn
}
