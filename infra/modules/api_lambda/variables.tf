# ---------------------------------------------------------------
# Inputs for the api_lambda module.
# ---------------------------------------------------------------

# Used for the function, role, API and log group names.
variable "name" {
  description = "Name for the API, e.g. bhandaran-dev-api"
  type        = string
}

# The Lambda function may connect only to this DSQL cluster.
variable "dsql_cluster_arn" {
  description = "ARN of the DSQL cluster the API connects to"
  type        = string
}

# Environment variables for the app (DB_MODE, DSQL_ENDPOINT, ...).
variable "environment" {
  description = "Environment variables passed to the FastAPI app"
  type        = map(string)
  default     = {}
}

# More memory also gives more CPU (faster cold starts).
variable "memory_mb" {
  description = "Lambda memory in MB"
  type        = number
  default     = 512
}

# Steady requests per second allowed through API Gateway.
variable "throttle_rate_per_second" {
  description = "API Gateway steady-state request limit"
  type        = number
  default     = 10
}

# Short burst of requests allowed above the steady rate.
variable "throttle_burst" {
  description = "API Gateway burst request limit"
  type        = number
  default     = 20
}

# When to send keep-warm pings (EventBridge schedule, UTC).
# Default: every 5 minutes from 00:00 to 17:55 UTC = 05:30 to 23:25 IST.
# null = no keep-warm ping.
variable "warmup_schedule" {
  description = "EventBridge schedule for keep-warm pings, or null to disable"
  type        = string
  default     = "cron(0/5 0-17 * * ? *)"
}

# SES identity ARN the function may send email from (email OTP).
# null = no email permission.
variable "ses_identity_arn" {
  description = "ARN of the SES identity the API may send email from, or null"
  type        = string
  default     = null
}
