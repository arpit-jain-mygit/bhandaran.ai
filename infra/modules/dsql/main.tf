# ---------------------------------------------------------------
# Module: dsql
# Creates one Aurora DSQL cluster (serverless, PostgreSQL-compatible).
# Billing is per use (DPUs + storage); an idle cluster costs ~$0.
# Apps connect with short-lived IAM auth tokens, not passwords,
# so no VPC / NAT gateway is needed for the MVP.
# ---------------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# Current region, used to build the connection endpoint below.
data "aws_region" "current" {}

# The DSQL cluster itself.
# deletion_protection_enabled = true means AWS refuses to delete it
# until protection is turned off first (keep true for prod).
resource "aws_dsql_cluster" "this" {
  deletion_protection_enabled = var.deletion_protection

  tags = {
    Name = var.name
  }
}

locals {
  # DSQL endpoints follow a fixed pattern: <id>.dsql.<region>.on.aws
  endpoint = "${aws_dsql_cluster.this.identifier}.dsql.${data.aws_region.current.region}.on.aws"
}
