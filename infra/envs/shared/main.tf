# ---------------------------------------------------------------
# Stack: shared
# Account-wide things that exist ONCE, not per environment:
#   - GitHub Actions -> AWS login (OIDC roles)
#   - Monthly AWS Budget with email alerts
# ---------------------------------------------------------------

# CI roles for GitHub Actions (plan on PRs, apply on main).
module "github_oidc" {
  source = "../../modules/github_oidc"

  name_prefix           = "bhandaran"
  github_repo           = var.github_repo
  github_subject_prefix = var.github_subject_prefix
  state_bucket_arn      = "arn:aws:s3:::${var.state_bucket_name}"
  create_oidc_provider  = var.create_oidc_provider
}

# Monthly budget for everything tagged project=bhandaran.
module "cost_alarms" {
  source = "../../modules/cost_alarms"

  name_prefix        = "bhandaran"
  alert_email        = var.alert_email
  create_budget      = true
  monthly_budget_usd = var.monthly_budget_usd
}
