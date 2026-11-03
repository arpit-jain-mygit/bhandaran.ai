# ---------------------------------------------------------------
# Inputs for the cost_alarms module.
# ---------------------------------------------------------------

# Prefix for names, e.g. "bhandaran-dev".
variable "name_prefix" {
  description = "Prefix for budget, topic and alarm names"
  type        = string
}

# Where alert emails go.
variable "alert_email" {
  description = "Email address that receives cost alerts"
  type        = string
}

# Create the monthly budget? (Do this once per account, in "shared".)
variable "create_budget" {
  description = "Create the monthly AWS Budget"
  type        = bool
  default     = false
}

# Monthly spend limit for the budget, in US dollars.
variable "monthly_budget_usd" {
  description = "Monthly budget in USD"
  type        = number
  default     = 10
}

# Create the DSQL daily DPU alarm? Must be a plain true/false known
# before apply (Terraform can't base "count" on a not-yet-created ID).
variable "create_dpu_alarm" {
  description = "Create the SNS topic and DSQL daily DPU alarm"
  type        = bool
  default     = false
}

# DSQL cluster to watch (required when create_dpu_alarm = true).
variable "dsql_cluster_id" {
  description = "DSQL cluster identifier to watch"
  type        = string
  default     = null
}

# Daily DPU usage that triggers the alarm.
variable "dsql_daily_dpu_threshold" {
  description = "Alarm when daily TotalDPU exceeds this number"
  type        = number
  default     = 10000
}
