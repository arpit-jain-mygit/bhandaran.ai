# ---------------------------------------------------------------
# Module: cost_alarms
# Emails you before costs surprise you:
#   1. An AWS Budget for the whole account (monthly $ limit).
#   2. Optionally, a CloudWatch alarm when a DSQL cluster uses more
#      DPUs per day than expected (DSQL bills per DPU).
# ---------------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# ---------- 1. Monthly account budget ----------

resource "aws_budgets_budget" "monthly" {
  count = var.create_budget ? 1 : 0

  name         = "${var.name_prefix}-monthly"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  # Only count costs tagged project=bhandaran (set via default_tags),
  # so other projects in the same account don't trigger this budget.
  # NOTE: the "project" tag must be activated once as a cost
  # allocation tag in the Billing console for this filter to work.
  cost_filter {
    name   = "TagKeyValue"
    values = ["user:project$bhandaran"]
  }

  # Email at 50% and 100% of actual spend...
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 50
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  # ...and when AWS forecasts the month will go over budget.
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}

# ---------- 2. DSQL daily DPU alarm ----------

# SNS topic = a mailing list for alarms. AWS sends a confirmation
# email first; click the link in it or no alerts will arrive.
resource "aws_sns_topic" "alerts" {
  count = var.create_dpu_alarm ? 1 : 0
  name  = "${var.name_prefix}-cost-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.create_dpu_alarm ? 1 : 0
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Fires when TotalDPU summed over one day crosses the threshold.
# Free tier is 100,000 DPU/month (~3,300/day), so the default of
# 10,000/day means "something is using far more than expected".
resource "aws_cloudwatch_metric_alarm" "dsql_dpu" {
  count = var.create_dpu_alarm ? 1 : 0

  alarm_name        = "${var.name_prefix}-dsql-daily-dpu"
  alarm_description = "DSQL used more than ${var.dsql_daily_dpu_threshold} DPU in a day"

  namespace   = "AWS/AuroraDSQL"
  metric_name = "TotalDPU"
  dimensions = {
    ClusterId = var.dsql_cluster_id
  }

  statistic           = "Sum"
  period              = 86400 # one day, in seconds
  evaluation_periods  = 1
  comparison_operator = "GreaterThanThreshold"
  threshold           = var.dsql_daily_dpu_threshold

  # No data = cluster idle = fine, not an alarm.
  treat_missing_data = "notBreaching"

  alarm_actions = [aws_sns_topic.alerts[0].arn]
}
