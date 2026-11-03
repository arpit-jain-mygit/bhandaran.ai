# ---------------------------------------------------------------
# Inputs for the dsql module.
# ---------------------------------------------------------------

# Friendly name, shown as the "Name" tag in the AWS console.
variable "name" {
  description = "Name tag for the DSQL cluster, e.g. bhandaran-dev"
  type        = string
}

# true = AWS blocks deletion of the cluster (recommended for prod).
variable "deletion_protection" {
  description = "Protect the cluster from accidental deletion"
  type        = bool
  default     = true
}
