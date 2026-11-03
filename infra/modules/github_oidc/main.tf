# ---------------------------------------------------------------
# Module: github_oidc
# Lets GitHub Actions log in to AWS WITHOUT stored access keys.
# GitHub issues a short-lived OIDC token; AWS trusts it only for
# this one repository and hands back temporary credentials.
#
# Two roles:
#   plan  role - read-only, used on pull requests ("terraform plan")
#   apply role - admin, used only from the main branch ("terraform apply")
# ---------------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

locals {
  github_oidc_url = "https://token.actions.githubusercontent.com"
}

# ---------- OIDC provider (one per AWS account) ----------

# Create the provider only if the account does not have one yet...
resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 1 : 0

  url            = local.github_oidc_url
  client_id_list = ["sts.amazonaws.com"]
}

# ...otherwise reuse the existing one (an account can only have one
# provider per URL, so creating a second would fail).
data "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 0 : 1
  url   = local.github_oidc_url
}

locals {
  oidc_provider_arn = var.create_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : data.aws_iam_openid_connect_provider.github[0].arn
}

# ---------- Trust policies: WHO may assume each role ----------

# Plan role: allowed from pull requests and from the main branch.
data "aws_iam_policy_document" "plan_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.oidc_provider_arn]
    }

    # Token must be meant for AWS STS.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Token must come from THIS repo, on a PR or on main.
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values = [
        "repo:${var.github_repo}:pull_request",
        "repo:${var.github_repo}:ref:refs/heads/main",
      ]
    }
  }
}

# Apply role: allowed ONLY from the main branch.
data "aws_iam_policy_document" "apply_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:ref:refs/heads/main"]
    }
  }
}

# ---------- Plan role (read-only + state access) ----------

resource "aws_iam_role" "plan" {
  name               = "${var.name_prefix}-github-plan"
  assume_role_policy = data.aws_iam_policy_document.plan_trust.json
}

# Read everything in the account, change nothing.
resource "aws_iam_role_policy_attachment" "plan_readonly" {
  role       = aws_iam_role.plan.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

# "terraform plan" also writes a small lock file (*.tflock) next to
# the state, so the plan role needs write access to the state bucket.
data "aws_iam_policy_document" "state_access" {
  statement {
    actions   = ["s3:ListBucket"]
    resources = [var.state_bucket_arn]
  }

  statement {
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${var.state_bucket_arn}/*"]
  }
}

resource "aws_iam_role_policy" "plan_state" {
  name   = "terraform-state-access"
  role   = aws_iam_role.plan.id
  policy = data.aws_iam_policy_document.state_access.json
}

# ---------- Apply role (full access, main branch only) ----------

resource "aws_iam_role" "apply" {
  name               = "${var.name_prefix}-github-apply"
  assume_role_policy = data.aws_iam_policy_document.apply_trust.json
}

# Terraform creates IAM roles, buckets, clusters, alarms... so the
# apply role needs broad rights. Safety comes from the trust policy:
# only workflows running on the main branch of this repo can use it.
resource "aws_iam_role_policy_attachment" "apply_admin" {
  role       = aws_iam_role.apply.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
