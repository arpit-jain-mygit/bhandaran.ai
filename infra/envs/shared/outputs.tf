# ---------------------------------------------------------------
# Outputs of the shared stack. Copy the role ARNs into GitHub:
# Settings -> Secrets and variables -> Actions -> Variables
#   AWS_PLAN_ROLE_ARN, AWS_APPLY_ROLE_ARN
# ---------------------------------------------------------------

output "github_plan_role_arn" {
  description = "Set as GitHub variable AWS_PLAN_ROLE_ARN"
  value       = module.github_oidc.plan_role_arn
}

output "github_apply_role_arn" {
  description = "Set as GitHub variable AWS_APPLY_ROLE_ARN"
  value       = module.github_oidc.apply_role_arn
}
