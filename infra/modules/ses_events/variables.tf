# ---------------------------------------------------------------
# Inputs for the ses_events module.
# ---------------------------------------------------------------

# Prefix for topic names, e.g. bhandaran-dev.
variable "name" {
  description = "Name prefix, e.g. bhandaran-dev"
  type        = string
}

# Configuration set name; the API sends mail with it (MAIL_CONFIGURATION_SET).
variable "configuration_set_name" {
  description = "SES configuration set that tracks bounces and complaints"
  type        = string
}

variable "account_id" {
  description = "AWS account ID (limits who may publish to the topic)"
  type        = string
}

variable "api_function_arn" {
  description = "ARN of the API Lambda that handles the reports"
  type        = string
}

variable "api_function_name" {
  description = "Name of the API Lambda"
  type        = string
}

variable "region" {
  description = "AWS region of the SES configuration set"
  type        = string
}
