# ---------------------------------------------------------------
# Inputs for the bootstrap stack.
# ---------------------------------------------------------------

# AWS region where the state bucket lives (Mumbai by default).
variable "region" {
  description = "AWS region for the Terraform state bucket"
  type        = string
  default     = "ap-south-1"
}
