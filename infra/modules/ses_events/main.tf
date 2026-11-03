# ---------------------------------------------------------------
# SES bounce and complaint reports (bounce handling).
#
#   configuration set  - sends with it are tracked by SES
#   SNS topic          - SES publishes BOUNCE and COMPLAINT reports here
#   Lambda subscription - SNS calls the API Lambda with each report,
#                         which stops mailing bad addresses
# ---------------------------------------------------------------

resource "aws_sesv2_configuration_set" "mail" {
  configuration_set_name = var.configuration_set_name
}

resource "aws_sns_topic" "reports" {
  name = "${var.name}-ses-reports"
}

# Only SES, and only for this AWS account, may publish here.
data "aws_iam_policy_document" "topic" {
  statement {
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.reports.arn]
    principals {
      type        = "Service"
      identifiers = ["ses.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = [var.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "reports" {
  arn    = aws_sns_topic.reports.arn
  policy = data.aws_iam_policy_document.topic.json
}

# Send bounce and complaint reports from the configuration set to SNS.
resource "aws_sesv2_configuration_set_event_destination" "reports" {
  configuration_set_name = aws_sesv2_configuration_set.mail.configuration_set_name
  event_destination_name = "bounces-and-complaints"

  event_destination {
    enabled              = true
    matching_event_types = ["BOUNCE", "COMPLAINT"]

    sns_destination {
      topic_arn = aws_sns_topic.reports.arn
    }
  }
}

# Call the API Lambda with each report.
resource "aws_sns_topic_subscription" "api" {
  topic_arn = aws_sns_topic.reports.arn
  protocol  = "lambda"
  endpoint  = var.api_function_arn
}

resource "aws_lambda_permission" "sns" {
  statement_id  = "AllowSnsReports"
  action        = "lambda:InvokeFunction"
  function_name = var.api_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.reports.arn
}
