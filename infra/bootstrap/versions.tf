# ---------------------------------------------------------------
# Which Terraform and which AWS provider version this folder needs.
# Terraform >= 1.10 is required for S3 native state locking.
# ---------------------------------------------------------------
terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # NOTE: no "backend" block here on purpose.
  # Bootstrap creates the S3 bucket that every other stack stores its
  # state in, so bootstrap itself keeps its (tiny) state locally.
}

# ---------------------------------------------------------------
# AWS provider: region comes from a variable; every resource gets
# the same default tags so costs are easy to track in Cost Explorer.
# ---------------------------------------------------------------
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      project    = "bhandaran"
      stack      = "bootstrap"
      managed_by = "terraform"
    }
  }
}
