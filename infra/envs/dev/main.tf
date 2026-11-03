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

  # SES configuration set that reports bounces and complaints (M3 bounce handling).
  mail_configuration_set    = "${local.name_prefix}-mail"
  ses_configuration_set_arn = "arn:aws:ses:${var.region}:${data.aws_caller_identity.current.account_id}:configuration-set/${local.mail_configuration_set}"
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
  cors_allowed_origins = concat(var.photo_cors_origins, [module.web.url])
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

# Secret that signs login tokens and hashes OTP codes (M3).
# Changing it logs everyone out. Never printed by Terraform.
resource "random_password" "app_secret_key" {
  length  = 64
  special = false
}

# Email sender for login codes (SES; SMS waits for DLT, M12).
module "ses" {
  source = "../../modules/ses_identity"

  identity   = var.mail_from
  region     = var.region
  account_id = data.aws_caller_identity.current.account_id
}

# FastAPI on Lambda behind an API Gateway HTTP API.
# CORS_ORIGINS is empty: the browser reaches UI and API through the
# same CloudFront URL, so no cross-origin calls happen.
module "api" {
  source = "../../modules/api_lambda"

  name                      = "${local.name_prefix}-api"
  dsql_cluster_arn          = module.dsql.arn
  ses_identity_arn          = module.ses.identity_arn
  ses_configuration_set_arn = local.ses_configuration_set_arn
  photo_bucket_arn          = module.photos.bucket_arn

  environment = {
    DB_MODE        = "dsql"
    DSQL_ENDPOINT  = module.dsql.endpoint
    DSQL_USER      = "admin"
    CORS_ORIGINS   = "[]"
    APP_SECRET_KEY = random_password.app_secret_key.result
    # Login codes are emailed through SES (SMS waits for DLT, M12).
    OTP_DELIVERY           = "email"
    COOKIE_SECURE          = "true"
    MAIL_FROM              = var.mail_from
    MAIL_CONFIGURATION_SET = local.mail_configuration_set
    PHOTO_BUCKET           = module.photos.bucket_name
  }
}

# Bounce and complaint reports from SES -> SNS -> the API Lambda (bounce handling).
module "ses_events" {
  source = "../../modules/ses_events"

  name                   = local.name_prefix
  configuration_set_name = local.mail_configuration_set
  region                 = var.region
  account_id             = data.aws_caller_identity.current.account_id
  api_function_arn       = module.api.function_arn
  api_function_name      = module.api.function_name
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

  name                  = "${local.name_prefix}-github-deploy"
  github_repo           = var.github_repo
  github_subject_prefix = var.github_subject_prefix
  lambda_function_arn   = module.api.function_arn
  web_bucket_arn        = module.web.bucket_arn
  distribution_arn      = module.web.distribution_arn
}
