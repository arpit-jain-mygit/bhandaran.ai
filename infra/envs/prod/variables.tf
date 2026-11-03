# ---------------------------------------------------------------
# Inputs for the prod stack. Real values go in terraform.tfvars
# (git-ignored); see terraform.tfvars.example.
# ---------------------------------------------------------------

variable "region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "alert_email" {
  description = "Email for DSQL cost alerts"
  type        = string
}

# Production web origin(s), e.g. ["https://bhandaran.ai"].
variable "photo_cors_origins" {
  description = "Browser origins allowed to use presigned photo URLs"
  type        = list(string)
  default     = []
}

variable "dsql_daily_dpu_threshold" {
  description = "Alarm when daily DSQL TotalDPU exceeds this"
  type        = number
  default     = 10000
}
