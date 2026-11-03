# ---------------------------------------------------------------
# Stack: dev
# Everything the app needs in the development environment:
#   - Aurora DSQL cluster (database)
#   - Private S3 bucket for warehouse photos
#   - Daily DSQL DPU cost alarm
#   - Hosting (M0b): API on Lambda + Angular on S3, one CloudFront URL
#   - Narrow GitHub deploy role for app releases
# ---------------------------------------------------------------

# Account ID makes the photo bucket name globally unique.
data "aws_caller_identity" "current" {}

locals {
  env         = "dev"
  name_prefix = "bhandaran-${local.env}"
}

# Database. Deletion protection is OFF in dev so the cluster can be
# torn down and recreated freely.
module "dsql" {
  source = "../../modules/dsql"

  name                = local.name_prefix
  deletion_protection = false
}

# Warehouse photos. force_destroy = true: dev data is disposable.
# CORS allows the local Angular dev server to upload directly.
module "photos" {
  source = "../../modules/s3_bucket"

  bucket_name          = "${local.name_prefix}-photos-${data.aws_caller_identity.current.account_id}"
  force_destroy        = true
  cors_allowed_origins = var.photo_cors_origins
}

# Email when DSQL usage in one day is far above normal.
module "cost_alarms" {
  source = "../../modules/cost_alarms"

  name_prefix              = local.name_prefix
  alert_email              = var.alert_email
  create_dpu_alarm         = true
  dsql_cluster_id          = module.dsql.identifier
  dsql_daily_dpu_threshold = var.dsql_daily_dpu_threshold
}

# ---------- Hosting (M0b) ----------

# FastAPI on Lambda behind an API Gateway HTTP API.
# CORS_ORIGINS is empty: the browser reaches UI and API through the
# same CloudFront URL, so no cross-origin calls happen.
module "api" {
  source = "../../modules/api_lambda"

  name             = "${local.name_prefix}-api"
  dsql_cluster_arn = module.dsql.arn

  environment = {
    DB_MODE       = "dsql"
    DSQL_ENDPOINT = module.dsql.endpoint
    DSQL_USER     = "admin"
    CORS_ORIGINS  = "[]"
  }
}

# Angular build in S3 + CloudFront in front of both S3 and the API.
module "web" {
  source = "../../modules/web_hosting"

  name          = local.name_prefix
  bucket_name   = "${local.name_prefix}-web-${data.aws_caller_identity.current.account_id}"
  force_destroy = true
  api_domain    = module.api.api_domain
}

# Role the "deploy-dev" GitHub workflow uses on every push to main.
module "github_deploy" {
  source = "../../modules/github_deploy_role"

  name                = "${local.name_prefix}-github-deploy"
  github_repo         = var.github_repo
  lambda_function_arn = module.api.function_arn
  web_bucket_arn      = module.web.bucket_arn
  distribution_arn    = module.web.distribution_arn
}
