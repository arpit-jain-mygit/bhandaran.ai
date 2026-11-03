# ---------------------------------------------------------------
# Stack: dev
# Everything the app needs in the development environment:
#   - Aurora DSQL cluster (database)
#   - Private S3 bucket for warehouse photos
#   - Daily DSQL DPU cost alarm
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
