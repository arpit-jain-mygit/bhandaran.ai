# ---------------------------------------------------------------
# Terraform + AWS provider versions, remote state, and provider
# settings for the "dev" stack.
# ---------------------------------------------------------------
terraform {
  # >= 1.10 is needed for S3 native state locking (use_lockfile).
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    # Zips the Lambda placeholder code.
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.8"
    }
  }

  # State is stored in the S3 bucket created by infra/bootstrap.
  # The bucket name is passed at init time, so it is not hardcoded:
  #   terraform init -backend-config=backend.hcl
  backend "s3" {
    key          = "dev/terraform.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true # S3 lock file; no DynamoDB table needed
  }
}

# Every resource in this stack gets these tags automatically.
# "project" lets the AWS Budget and Cost Explorer filter our costs.
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      project     = "bhandaran"
      environment = "dev"
      managed_by  = "terraform"
    }
  }
}
