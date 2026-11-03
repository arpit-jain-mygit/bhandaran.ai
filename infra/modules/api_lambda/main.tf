# ---------------------------------------------------------------
# Module: api_lambda
# Runs the FastAPI backend on AWS Lambda behind an API Gateway
# HTTP API:
#
#   CloudFront /api/*  ->  HTTP API  ->  Lambda (FastAPI + Mangum)  ->  DSQL
#
# Terraform creates the function with a tiny placeholder; the real
# code is uploaded by CI (aws lambda update-function-code), so app
# deploys don't need a Terraform run.
# ---------------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.8"
    }
  }
}

# ---------- Placeholder code (replaced by CI on first deploy) ----------

data "archive_file" "placeholder" {
  type        = "zip"
  output_path = "${path.module}/.placeholder.zip"

  source {
    filename = "app/lambda_handler.py"
    content  = <<-PY
      # Placeholder until CI uploads the real FastAPI build.
      def handler(event, context):
          return {"statusCode": 503, "body": "API not deployed yet"}
    PY
  }
}

# ---------- IAM: what the Lambda function is allowed to do ----------

# Trust policy: only the Lambda service can use this role.
data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.name}-lambda"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

# Write logs to CloudWatch.
resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Connect to the DSQL cluster as the "admin" database user.
# TODO(M3): switch to a least-privilege database role (dsql:DbConnect).
data "aws_iam_policy_document" "dsql" {
  statement {
    actions   = ["dsql:DbConnectAdmin"]
    resources = [var.dsql_cluster_arn]
  }
}

resource "aws_iam_role_policy" "dsql" {
  name   = "dsql-connect"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.dsql.json
}

# Send email (email OTP codes) from the verified SES domain only.
data "aws_iam_policy_document" "ses" {
  statement {
    actions   = ["ses:SendEmail"]
    resources = [var.ses_identity_arn]
  }
}

# Only created when an SES identity is given.
resource "aws_iam_role_policy" "ses" {
  count  = var.ses_identity_arn == null ? 0 : 1
  name   = "ses-send"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.ses.json
}

# ---------- Logs ----------

# Keep API logs for 14 days (older logs are deleted to save cost).
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.name}"
  retention_in_days = 14
}

# ---------- The Lambda function ----------

resource "aws_lambda_function" "api" {
  function_name = var.name
  role          = aws_iam_role.lambda.arn

  runtime       = "python3.14"
  architectures = ["arm64"] # Graviton: ~20% cheaper than x86
  handler       = "app.lambda_handler.handler"
  memory_size   = var.memory_mb
  timeout       = 15 # seconds; API Gateway's own limit is 30

  filename         = data.archive_file.placeholder.output_path
  source_code_hash = data.archive_file.placeholder.output_base64sha256

  # App settings (read by backend/app/config.py).
  environment {
    variables = var.environment
  }

  # CI uploads new code directly; don't let Terraform roll it back.
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

# ---------- API Gateway HTTP API (public HTTPS entry point) ----------

resource "aws_apigatewayv2_api" "http" {
  name          = var.name
  protocol_type = "HTTP"
}

# Send every request (any method, any path) to the Lambda function.
resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "all" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# "$default" stage = live immediately, no /stage-name in URLs.
# Throttling caps requests per second, which also caps cost.
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit  = var.throttle_rate_per_second
    throttling_burst_limit = var.throttle_burst
  }
}

# Allow API Gateway (this API only) to invoke the function.
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowHttpApiInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

# ---------- Keep-warm ping (cold-start reducer) ----------

# Every few minutes (default: every 5 min, 05:30-23:30 IST) send
# {"warmup": true} straight to the function. The handler runs one
# "SELECT 1" so the instance and its DSQL connection stay warm.
# Cost: ~6,500 tiny invocations a month - inside Lambda's free tier.
resource "aws_cloudwatch_event_rule" "warmup" {
  count = var.warmup_schedule != null ? 1 : 0

  name                = "${var.name}-warmup"
  description         = "Keep ${var.name} warm (fewer cold starts)"
  schedule_expression = var.warmup_schedule
}

resource "aws_cloudwatch_event_target" "warmup" {
  count = var.warmup_schedule != null ? 1 : 0

  rule  = aws_cloudwatch_event_rule.warmup[0].name
  arn   = aws_lambda_function.api.arn
  input = jsonencode({ warmup = true })
}

# Allow this one EventBridge rule to invoke the function.
resource "aws_lambda_permission" "warmup" {
  count = var.warmup_schedule != null ? 1 : 0

  statement_id  = "AllowWarmupSchedule"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.warmup[0].arn
}
