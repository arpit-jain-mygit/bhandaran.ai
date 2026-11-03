# ---------------------------------------------------------------
# Outputs of the api_lambda module.
# ---------------------------------------------------------------

# CI uploads new code to this function.
output "function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.api.function_name
}

output "function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.api.arn
}

# Hostname only (no https://), used as a CloudFront origin.
output "api_domain" {
  description = "API Gateway hostname, e.g. abc123.execute-api.ap-south-1.amazonaws.com"
  value       = replace(aws_apigatewayv2_api.http.api_endpoint, "https://", "")
}
